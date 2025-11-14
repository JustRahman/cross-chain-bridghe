"""Transaction timeout estimation service"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.db.models.transactions import TransactionHistory
from app.db.models.analytics import BridgePerformanceMetric, HistoricalGasPrice
from app.core.logging import log


class TimeoutEstimator:
    """
    Estimate transaction completion times and timeouts.

    Uses historical data and current network conditions to predict:
    - Expected completion time
    - Confidence intervals
    - Timeout thresholds
    - Risk of delay
    """

    def __init__(self):
        # Default timeout multipliers by confidence level
        self.confidence_multipliers = {
            50: 1.0,   # 50% confident = median time
            75: 1.5,   # 75% confident = 1.5x median
            90: 2.0,   # 90% confident = 2x median
            95: 2.5,   # 95% confident = 2.5x median
            99: 3.5    # 99% confident = 3.5x median
        }

    def estimate_timeout(
        self,
        bridge_name: str,
        source_chain: str,
        destination_chain: str,
        amount_usd: float,
        db: Session,
        confidence_level: int = 90
    ) -> Dict:
        """
        Estimate transaction timeout with confidence interval.

        Args:
            bridge_name: Bridge protocol name
            source_chain: Source chain
            destination_chain: Destination chain
            amount_usd: Transaction amount in USD
            db: Database session
            confidence_level: Confidence % (50, 75, 90, 95, 99)

        Returns:
            Timeout estimate with breakdown
        """
        try:
            # Get historical data
            historical_times = self._get_historical_times(
                bridge_name, source_chain, destination_chain, db
            )

            if not historical_times or len(historical_times) < 5:
                # Insufficient data - use conservative estimates
                return self._conservative_estimate(
                    bridge_name, source_chain, destination_chain, confidence_level
                )

            # Calculate statistics
            median_time = self._calculate_median(historical_times)
            p75_time = self._calculate_percentile(historical_times, 75)
            p90_time = self._calculate_percentile(historical_times, 90)
            p95_time = self._calculate_percentile(historical_times, 95)
            p99_time = self._calculate_percentile(historical_times, 99)
            avg_time = sum(historical_times) / len(historical_times)
            min_time = min(historical_times)
            max_time = max(historical_times)

            # Adjust for network conditions
            network_multiplier = self._get_network_condition_multiplier(
                source_chain, destination_chain, db
            )

            # Adjust for amount (larger amounts may take longer)
            amount_multiplier = self._get_amount_multiplier(amount_usd)

            # Calculate final estimates
            base_estimate = median_time * network_multiplier * amount_multiplier

            # Get timeout for requested confidence level
            confidence_multiplier = self.confidence_multipliers.get(confidence_level, 2.0)
            timeout_minutes = int(base_estimate * confidence_multiplier)

            # Calculate risk level
            risk_level = self._assess_delay_risk(
                historical_times, network_multiplier, amount_multiplier
            )

            return {
                "bridge_name": bridge_name,
                "source_chain": source_chain,
                "destination_chain": destination_chain,
                "estimates": {
                    "expected_time_minutes": int(base_estimate),
                    "timeout_minutes": timeout_minutes,
                    "confidence_level": confidence_level,
                    "min_time_minutes": min_time,
                    "max_time_minutes": max_time,
                    "median_time_minutes": int(median_time),
                    "average_time_minutes": int(avg_time)
                },
                "percentiles": {
                    "p50": int(median_time),
                    "p75": int(p75_time),
                    "p90": int(p90_time),
                    "p95": int(p95_time),
                    "p99": int(p99_time)
                },
                "risk_assessment": {
                    "delay_risk": risk_level,
                    "network_condition": self._interpret_multiplier(network_multiplier),
                    "amount_impact": self._interpret_amount_impact(amount_multiplier)
                },
                "recommendations": {
                    "set_timeout_at": timeout_minutes,
                    "check_status_after": int(base_estimate * 0.5),
                    "escalate_after": int(base_estimate * 1.5),
                    "consider_alternative_after": int(base_estimate * 2.0)
                },
                "data_quality": {
                    "sample_size": len(historical_times),
                    "data_period_days": 7,
                    "confidence": "high" if len(historical_times) >= 20 else "medium" if len(historical_times) >= 10 else "low"
                },
                "estimated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            log.error(f"Error estimating timeout: {str(e)}")
            return self._error_estimate(bridge_name, str(e))

    def _get_historical_times(
        self,
        bridge_name: str,
        source_chain: str,
        destination_chain: str,
        db: Session
    ) -> List[int]:
        """Get historical completion times"""
        cutoff = datetime.utcnow() - timedelta(days=7)

        transactions = db.query(TransactionHistory.actual_time_minutes).filter(
            and_(
                TransactionHistory.selected_bridge == bridge_name,
                TransactionHistory.source_chain == source_chain,
                TransactionHistory.destination_chain == destination_chain,
                TransactionHistory.status == "completed",
                TransactionHistory.actual_time_minutes.isnot(None),
                TransactionHistory.created_at >= cutoff
            )
        ).all()

        return [t[0] for t in transactions if t[0] > 0]

    def _calculate_median(self, values: List[int]) -> float:
        """Calculate median"""
        sorted_values = sorted(values)
        n = len(sorted_values)

        if n == 0:
            return 0

        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        else:
            return sorted_values[n // 2]

    def _calculate_percentile(self, values: List[int], percentile: int) -> float:
        """Calculate percentile"""
        if not values:
            return 0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100))
        index = min(index, len(sorted_values) - 1)

        return sorted_values[index]

    def _get_network_condition_multiplier(
        self,
        source_chain: str,
        destination_chain: str,
        db: Session
    ) -> float:
        """
        Calculate network condition multiplier based on current gas prices.
        Higher gas = more congestion = longer times
        """
        try:
            # Map chain names to chain IDs
            chain_ids = {
                "ethereum": 1,
                "arbitrum": 42161,
                "optimism": 10,
                "polygon": 137,
                "base": 8453
            }

            source_id = chain_ids.get(source_chain.lower(), 1)
            dest_id = chain_ids.get(destination_chain.lower(), 1)

            # Get current gas prices
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)

            source_gas = db.query(func.avg(HistoricalGasPrice.standard)).filter(
                and_(
                    HistoricalGasPrice.chain_id == source_id,
                    HistoricalGasPrice.recorded_at >= recent_cutoff
                )
            ).scalar() or 30.0

            dest_gas = db.query(func.avg(HistoricalGasPrice.standard)).filter(
                and_(
                    HistoricalGasPrice.chain_id == dest_id,
                    HistoricalGasPrice.recorded_at >= recent_cutoff
                )
            ).scalar() or 30.0

            # Get 24h average gas prices
            day_cutoff = datetime.utcnow() - timedelta(hours=24)

            source_avg = db.query(func.avg(HistoricalGasPrice.standard)).filter(
                and_(
                    HistoricalGasPrice.chain_id == source_id,
                    HistoricalGasPrice.recorded_at >= day_cutoff
                )
            ).scalar() or 30.0

            dest_avg = db.query(func.avg(HistoricalGasPrice.standard)).filter(
                and_(
                    HistoricalGasPrice.chain_id == dest_id,
                    HistoricalGasPrice.recorded_at >= day_cutoff
                )
            ).scalar() or 30.0

            # Calculate multipliers
            source_multiplier = source_gas / source_avg if source_avg > 0 else 1.0
            dest_multiplier = dest_gas / dest_avg if dest_avg > 0 else 1.0

            # Average the two
            avg_multiplier = (source_multiplier + dest_multiplier) / 2

            # Clamp between 0.8 and 2.0
            return max(0.8, min(2.0, avg_multiplier))

        except Exception as e:
            log.error(f"Error calculating network multiplier: {str(e)}")
            return 1.0  # Default

    def _get_amount_multiplier(self, amount_usd: float) -> float:
        """
        Calculate amount-based multiplier.
        Larger amounts may require more confirmations or have liquidity delays.
        """
        if amount_usd < 100:
            return 1.0
        elif amount_usd < 1000:
            return 1.05
        elif amount_usd < 10000:
            return 1.1
        elif amount_usd < 100000:
            return 1.2
        else:
            return 1.3

    def _assess_delay_risk(
        self,
        historical_times: List[int],
        network_multiplier: float,
        amount_multiplier: float
    ) -> str:
        """Assess risk of delays"""
        if not historical_times:
            return "unknown"

        # Calculate variance
        avg = sum(historical_times) / len(historical_times)
        variance = sum((t - avg) ** 2 for t in historical_times) / len(historical_times)
        std_dev = variance ** 0.5
        cv = (std_dev / avg) if avg > 0 else 0

        # High variance = higher risk
        variance_risk = cv > 0.5

        # Network congestion = higher risk
        network_risk = network_multiplier > 1.2

        # Large amount = higher risk
        amount_risk = amount_multiplier > 1.1

        risk_factors = sum([variance_risk, network_risk, amount_risk])

        if risk_factors >= 2:
            return "high"
        elif risk_factors == 1:
            return "medium"
        else:
            return "low"

    def _interpret_multiplier(self, multiplier: float) -> str:
        """Interpret network condition multiplier"""
        if multiplier < 0.9:
            return "excellent"
        elif multiplier < 1.1:
            return "normal"
        elif multiplier < 1.3:
            return "congested"
        else:
            return "highly_congested"

    def _interpret_amount_impact(self, multiplier: float) -> str:
        """Interpret amount impact"""
        if multiplier <= 1.0:
            return "minimal"
        elif multiplier <= 1.1:
            return "low"
        elif multiplier <= 1.2:
            return "moderate"
        else:
            return "significant"

    def _conservative_estimate(
        self,
        bridge_name: str,
        source_chain: str,
        destination_chain: str,
        confidence_level: int
    ) -> Dict:
        """Conservative estimate when insufficient data"""
        # Use conservative defaults
        base_time = 15  # 15 minutes base

        confidence_multiplier = self.confidence_multipliers.get(confidence_level, 2.0)
        timeout_minutes = int(base_time * confidence_multiplier)

        return {
            "bridge_name": bridge_name,
            "source_chain": source_chain,
            "destination_chain": destination_chain,
            "estimates": {
                "expected_time_minutes": base_time,
                "timeout_minutes": timeout_minutes,
                "confidence_level": confidence_level
            },
            "risk_assessment": {
                "delay_risk": "unknown",
                "network_condition": "unknown",
                "amount_impact": "unknown"
            },
            "recommendations": {
                "set_timeout_at": timeout_minutes,
                "check_status_after": 10,
                "escalate_after": 20,
                "consider_alternative_after": 30
            },
            "data_quality": {
                "sample_size": 0,
                "confidence": "low",
                "warning": "Insufficient historical data - using conservative estimates"
            },
            "estimated_at": datetime.utcnow().isoformat()
        }

    def _error_estimate(self, bridge_name: str, error: str) -> Dict:
        """Error response"""
        return {
            "bridge_name": bridge_name,
            "error": f"Failed to estimate timeout: {error}",
            "estimates": {
                "expected_time_minutes": 15,
                "timeout_minutes": 30,
                "confidence_level": 50
            },
            "estimated_at": datetime.utcnow().isoformat()
        }


# Singleton instance
timeout_estimator = TimeoutEstimator()
