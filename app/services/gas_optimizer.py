"""Time-based gas optimization service"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.db.models.analytics import HistoricalGasPrice
from app.core.logging import log


class GasOptimizer:
    """
    Optimize transaction timing based on historical gas prices.

    Analyzes patterns to recommend:
    - Best time to execute transaction
    - Potential savings
    - Price predictions
    """

    def __init__(self):
        self.analysis_window_hours = 24  # Analyze last 24 hours
        self.forecast_hours = 4  # Forecast next 4 hours

    def analyze_optimal_timing(
        self,
        chain_id: int,
        db_session: Session
    ) -> Dict:
        """
        Analyze historical data to find optimal transaction timing.

        Args:
            chain_id: Blockchain network ID
            db_session: Database session

        Returns:
            Timing analysis and recommendations
        """
        try:
            # Get historical data
            cutoff = datetime.utcnow() - timedelta(hours=self.analysis_window_hours)

            prices = db_session.query(HistoricalGasPrice).filter(
                and_(
                    HistoricalGasPrice.chain_id == chain_id,
                    HistoricalGasPrice.recorded_at >= cutoff
                )
            ).order_by(HistoricalGasPrice.recorded_at).all()

            if not prices or len(prices) < 10:
                return self._get_default_analysis(chain_id)

            # Current gas price
            current_price = prices[-1].standard
            current_time = datetime.utcnow()

            # Calculate statistics
            standard_prices = [p.standard for p in prices]
            avg_price = sum(standard_prices) / len(standard_prices)
            min_price = min(standard_prices)
            max_price = max(standard_prices)

            # Find hourly patterns
            hourly_averages = self._calculate_hourly_averages(prices)

            # Find best time to transact
            best_hour = min(hourly_averages, key=hourly_averages.get)
            best_hour_price = hourly_averages[best_hour]

            # Calculate potential savings
            if current_price > 0:
                savings_percent = ((current_price - best_hour_price) / current_price) * 100
            else:
                savings_percent = 0

            # Determine recommendation
            current_hour = current_time.hour

            if current_price <= best_hour_price * 1.1:  # Within 10% of best
                recommendation = "execute_now"
                message = f"Current gas prices are near optimal. Execute now to save time."
            elif savings_percent > 30:
                recommendation = "wait"
                message = f"Gas prices are {savings_percent:.1f}% above optimal. Consider waiting for hour {best_hour}:00 UTC."
            elif savings_percent > 15:
                recommendation = "consider_waiting"
                message = f"Moderate savings of {savings_percent:.1f}% possible by waiting. Your choice."
            else:
                recommendation = "execute_now"
                message = "Gas prices are reasonable. Small savings not worth the wait."

            # Price trend
            recent_prices = standard_prices[-6:]  # Last 6 data points (~30 min)
            if len(recent_prices) >= 2:
                if recent_prices[-1] < recent_prices[0]:
                    trend = "decreasing"
                elif recent_prices[-1] > recent_prices[0]:
                    trend = "increasing"
                else:
                    trend = "stable"
            else:
                trend = "unknown"

            # Forecast next hours
            forecast = self._forecast_prices(prices, self.forecast_hours)

            return {
                "current_gas_price_gwei": float(current_price),
                "average_24h_gwei": float(avg_price),
                "min_24h_gwei": float(min_price),
                "max_24h_gwei": float(max_price),
                "optimal_hour_utc": best_hour,
                "optimal_price_gwei": float(best_hour_price),
                "potential_savings_percent": float(savings_percent),
                "potential_savings_usd": self._calculate_savings_usd(current_price, best_hour_price, chain_id),
                "recommendation": recommendation,
                "message": message,
                "price_trend": trend,
                "hourly_averages": {str(k): float(v) for k, v in hourly_averages.items()},
                "forecast_next_hours": forecast,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            log.error(f"Error analyzing optimal timing: {str(e)}")
            return self._get_default_analysis(chain_id)

    def _calculate_hourly_averages(self, prices: List[HistoricalGasPrice]) -> Dict[int, float]:
        """Calculate average gas price for each hour of the day"""
        hourly_sums = {}
        hourly_counts = {}

        for price in prices:
            hour = price.recorded_at.hour

            if hour not in hourly_sums:
                hourly_sums[hour] = 0
                hourly_counts[hour] = 0

            hourly_sums[hour] += price.standard
            hourly_counts[hour] += 1

        return {
            hour: hourly_sums[hour] / hourly_counts[hour]
            for hour in hourly_sums
        }

    def _forecast_prices(self, historical_prices: List[HistoricalGasPrice], hours: int) -> List[Dict]:
        """Simple price forecasting based on recent trends"""
        if not historical_prices or len(historical_prices) < 5:
            return []

        forecast = []
        recent_prices = [p.standard for p in historical_prices[-12:]]  # Last hour

        if not recent_prices:
            return []

        # Simple moving average forecast
        avg_recent = sum(recent_prices) / len(recent_prices)

        current_time = datetime.utcnow()

        for i in range(1, hours + 1):
            forecast_time = current_time + timedelta(hours=i)

            # Add some variation based on hour of day patterns
            hour_factor = 1.0
            hour = forecast_time.hour

            # Peak hours (8-18 UTC) tend to be more expensive
            if 8 <= hour <= 18:
                hour_factor = 1.15
            else:
                hour_factor = 0.95

            forecasted_price = avg_recent * hour_factor

            forecast.append({
                "hour_offset": i,
                "timestamp": forecast_time.isoformat(),
                "forecasted_price_gwei": float(forecasted_price),
                "confidence": "low"  # Simple model has low confidence
            })

        return forecast

    def _calculate_savings_usd(
        self,
        current_price: float,
        optimal_price: float,
        chain_id: int
    ) -> float:
        """Calculate potential USD savings"""
        # Assume standard bridge transaction ~200k gas
        gas_limit = 200000

        price_diff = current_price - optimal_price
        gas_savings_eth = (gas_limit * price_diff) / 1e9

        # ETH price (simplified)
        eth_prices = {
            1: 2000.0,    # Ethereum
            10: 2000.0,   # Optimism
            42161: 2000.0,  # Arbitrum
            137: 0.80,    # Polygon (MATIC)
            8453: 2000.0,   # Base
        }

        native_price = eth_prices.get(chain_id, 2000.0)
        savings_usd = gas_savings_eth * native_price

        return round(savings_usd, 2)

    def _get_default_analysis(self, chain_id: int) -> Dict:
        """Return default analysis when insufficient data"""
        return {
            "current_gas_price_gwei": 30.0,
            "average_24h_gwei": 30.0,
            "min_24h_gwei": 20.0,
            "max_24h_gwei": 50.0,
            "optimal_hour_utc": 2,  # 2 AM UTC typically lowest
            "optimal_price_gwei": 25.0,
            "potential_savings_percent": 0.0,
            "potential_savings_usd": 0.0,
            "recommendation": "execute_now",
            "message": "Insufficient historical data for analysis. Current prices appear reasonable.",
            "price_trend": "unknown",
            "hourly_averages": {},
            "forecast_next_hours": [],
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

    def compare_timing_options(
        self,
        chain_id: int,
        amount_usd: float,
        db_session: Session
    ) -> Dict:
        """
        Compare executing now vs waiting for optimal timing.

        Args:
            chain_id: Blockchain network ID
            amount_usd: Transaction amount in USD
            db_session: Database session

        Returns:
            Comparison of timing options
        """
        try:
            analysis = self.analyze_optimal_timing(chain_id, db_session)

            # Estimate total cost now vs later
            gas_cost_now = self._estimate_gas_cost(
                chain_id,
                analysis["current_gas_price_gwei"]
            )

            gas_cost_optimal = self._estimate_gas_cost(
                chain_id,
                analysis["optimal_price_gwei"]
            )

            # Calculate time to optimal hour
            current_hour = datetime.utcnow().hour
            optimal_hour = analysis["optimal_hour_utc"]

            if optimal_hour > current_hour:
                hours_to_wait = optimal_hour - current_hour
            else:
                hours_to_wait = (24 - current_hour) + optimal_hour

            return {
                "execute_now": {
                    "gas_cost_usd": gas_cost_now,
                    "total_cost_usd": amount_usd + gas_cost_now,
                    "wait_time_hours": 0,
                    "recommendation": "Fast execution, higher cost"
                },
                "wait_for_optimal": {
                    "gas_cost_usd": gas_cost_optimal,
                    "total_cost_usd": amount_usd + gas_cost_optimal,
                    "wait_time_hours": hours_to_wait,
                    "recommendation": f"Wait ~{hours_to_wait}h for {analysis['potential_savings_percent']:.1f}% savings"
                },
                "savings": {
                    "amount_usd": gas_cost_now - gas_cost_optimal,
                    "percent": analysis["potential_savings_percent"]
                },
                "best_choice": "execute_now" if analysis["recommendation"] == "execute_now" else "wait_for_optimal"
            }

        except Exception as e:
            log.error(f"Error comparing timing options: {str(e)}")
            return {
                "execute_now": {"gas_cost_usd": 10.0, "total_cost_usd": amount_usd + 10.0, "wait_time_hours": 0},
                "wait_for_optimal": {"gas_cost_usd": 8.0, "total_cost_usd": amount_usd + 8.0, "wait_time_hours": 4},
                "savings": {"amount_usd": 2.0, "percent": 20.0},
                "best_choice": "execute_now"
            }

    def _estimate_gas_cost(self, chain_id: int, gas_price_gwei: float) -> float:
        """Estimate gas cost in USD"""
        gas_limit = 200000
        gas_cost_eth = (gas_limit * gas_price_gwei) / 1e9

        eth_prices = {
            1: 2000.0,
            10: 2000.0,
            42161: 2000.0,
            137: 0.80,
            8453: 2000.0,
        }

        native_price = eth_prices.get(chain_id, 2000.0)
        return round(gas_cost_eth * native_price, 2)


# Global instance
gas_optimizer = GasOptimizer()
