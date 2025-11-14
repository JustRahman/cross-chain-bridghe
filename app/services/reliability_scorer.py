"""Advanced bridge reliability scoring system"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.db.models.transactions import TransactionHistory
from app.db.models.analytics import BridgePerformanceMetric
from app.core.logging import log


class ReliabilityScorer:
    """
    Calculate comprehensive reliability scores for bridges.

    Scoring factors:
    - Success rate (40%)
    - Completion time consistency (20%)
    - Cost consistency (15%)
    - Uptime (15%)
    - Volume/liquidity (10%)
    """

    def __init__(self):
        self.weights = {
            "success_rate": 0.40,
            "time_consistency": 0.20,
            "cost_consistency": 0.15,
            "uptime": 0.15,
            "volume": 0.10
        }

    def calculate_comprehensive_score(
        self,
        bridge_name: str,
        db: Session,
        hours: int = 168  # 7 days default
    ) -> Dict:
        """
        Calculate comprehensive reliability score for a bridge.

        Returns detailed breakdown with:
        - Overall score (0-100)
        - Component scores
        - Metrics
        - Recommendations
        """
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)

            # Get all transactions for this bridge
            transactions = db.query(TransactionHistory).filter(
                and_(
                    TransactionHistory.selected_bridge == bridge_name,
                    TransactionHistory.created_at >= cutoff
                )
            ).all()

            if not transactions:
                return self._no_data_response(bridge_name)

            # Calculate component scores
            success_score = self._calculate_success_score(transactions)
            time_score = self._calculate_time_consistency_score(transactions)
            cost_score = self._calculate_cost_consistency_score(transactions)
            uptime_score = self._calculate_uptime_score(transactions, hours)
            volume_score = self._calculate_volume_score(transactions, db)

            # Calculate weighted overall score
            overall_score = (
                success_score * self.weights["success_rate"] +
                time_score * self.weights["time_consistency"] +
                cost_score * self.weights["cost_consistency"] +
                uptime_score * self.weights["uptime"] +
                volume_score * self.weights["volume"]
            )

            # Determine rating
            rating = self._get_rating(overall_score)

            # Get recommendation
            recommendation = self._get_recommendation(
                overall_score, success_score, time_score, cost_score
            )

            # Calculate trend (comparing to previous period)
            trend = self._calculate_trend(bridge_name, db, hours)

            return {
                "bridge_name": bridge_name,
                "overall_score": round(overall_score, 2),
                "rating": rating,
                "recommendation": recommendation,
                "trend": trend,
                "component_scores": {
                    "success_rate": {
                        "score": round(success_score, 2),
                        "weight": self.weights["success_rate"] * 100,
                        "description": "Transaction success rate"
                    },
                    "time_consistency": {
                        "score": round(time_score, 2),
                        "weight": self.weights["time_consistency"] * 100,
                        "description": "Completion time consistency"
                    },
                    "cost_consistency": {
                        "score": round(cost_score, 2),
                        "weight": self.weights["cost_consistency"] * 100,
                        "description": "Cost predictability"
                    },
                    "uptime": {
                        "score": round(uptime_score, 2),
                        "weight": self.weights["uptime"] * 100,
                        "description": "Service availability"
                    },
                    "volume": {
                        "score": round(volume_score, 2),
                        "weight": self.weights["volume"] * 100,
                        "description": "Transaction volume and liquidity"
                    }
                },
                "metrics": {
                    "total_transactions": len(transactions),
                    "successful_transactions": len([t for t in transactions if t.status == "completed"]),
                    "failed_transactions": len([t for t in transactions if t.status == "failed"]),
                    "avg_completion_time_minutes": self._avg_completion_time(transactions),
                    "avg_cost_usd": self._avg_cost(transactions),
                    "analyzed_period_hours": hours
                },
                "last_updated": datetime.utcnow().isoformat()
            }

        except Exception as e:
            log.error(f"Error calculating reliability score: {str(e)}")
            return self._error_response(bridge_name, str(e))

    def _calculate_success_score(self, transactions: List[TransactionHistory]) -> float:
        """Calculate success rate score (0-100)"""
        if not transactions:
            return 0.0

        completed = len([t for t in transactions if t.status == "completed"])
        success_rate = (completed / len(transactions)) * 100

        # Perfect score at 98%+, linear scaling below
        if success_rate >= 98:
            return 100.0
        else:
            return success_rate

    def _calculate_time_consistency_score(self, transactions: List[TransactionHistory]) -> float:
        """Calculate time consistency score based on variance (0-100)"""
        completed = [t for t in transactions if t.status == "completed" and t.actual_time_minutes]

        if len(completed) < 3:
            return 50.0  # Insufficient data

        times = [t.actual_time_minutes for t in completed]
        avg_time = sum(times) / len(times)

        # Calculate coefficient of variation
        if avg_time == 0:
            return 50.0

        variance = sum((t - avg_time) ** 2 for t in times) / len(times)
        std_dev = variance ** 0.5
        cv = (std_dev / avg_time) * 100  # Coefficient of variation as percentage

        # Lower CV is better - score inversely
        # CV of 0% = 100 score, CV of 50%+ = 0 score
        score = max(0, 100 - (cv * 2))

        return score

    def _calculate_cost_consistency_score(self, transactions: List[TransactionHistory]) -> float:
        """Calculate cost consistency score based on variance (0-100)"""
        costs = [t.actual_cost_usd for t in transactions if t.actual_cost_usd]

        if len(costs) < 3:
            return 50.0

        avg_cost = sum(costs) / len(costs)

        if avg_cost == 0:
            return 50.0

        variance = sum((c - avg_cost) ** 2 for c in costs) / len(costs)
        std_dev = variance ** 0.5
        cv = (std_dev / avg_cost) * 100

        # Lower CV is better
        score = max(0, 100 - (cv * 2))

        return score

    def _calculate_uptime_score(self, transactions: List[TransactionHistory], hours: int) -> float:
        """Calculate uptime score based on transaction distribution (0-100)"""
        if not transactions:
            return 0.0

        # Check if transactions are distributed across the time period
        # Good uptime = transactions spread evenly
        # Poor uptime = transactions clustered (service down for periods)

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        hour_buckets = hours

        # Create hourly buckets
        buckets = [0] * hour_buckets

        for tx in transactions:
            hours_ago = (datetime.utcnow() - tx.created_at).total_seconds() / 3600
            bucket_index = int(hours_ago)
            if 0 <= bucket_index < hour_buckets:
                buckets[bucket_index] += 1

        # Calculate what percentage of hours had activity
        active_hours = len([b for b in buckets if b > 0])
        activity_rate = (active_hours / hour_buckets) * 100

        # Good uptime = high activity rate
        return min(100, activity_rate * 1.2)  # Boost to make 80%+ = 100

    def _calculate_volume_score(self, transactions: List[TransactionHistory], db: Session) -> float:
        """Calculate volume score relative to other bridges (0-100)"""
        bridge_name = transactions[0].selected_bridge if transactions else None

        if not bridge_name:
            return 50.0

        cutoff = datetime.utcnow() - timedelta(days=7)

        # Get total volume for this bridge
        bridge_volume = db.query(func.sum(TransactionHistory.actual_cost_usd)).filter(
            and_(
                TransactionHistory.selected_bridge == bridge_name,
                TransactionHistory.created_at >= cutoff
            )
        ).scalar() or 0

        # Get total volume for all bridges
        total_volume = db.query(func.sum(TransactionHistory.actual_cost_usd)).filter(
            TransactionHistory.created_at >= cutoff
        ).scalar() or 1

        # Calculate market share
        market_share = (bridge_volume / total_volume) * 100 if total_volume > 0 else 0

        # Score based on market share (10% = 100, linear scaling)
        score = min(100, market_share * 10)

        return score

    def _avg_completion_time(self, transactions: List[TransactionHistory]) -> Optional[int]:
        """Calculate average completion time"""
        times = [t.actual_time_minutes for t in transactions if t.actual_time_minutes]
        if not times:
            return None
        return int(sum(times) / len(times))

    def _avg_cost(self, transactions: List[TransactionHistory]) -> Optional[float]:
        """Calculate average cost"""
        costs = [t.actual_cost_usd for t in transactions if t.actual_cost_usd]
        if not costs:
            return None
        return round(sum(costs) / len(costs), 2)

    def _get_rating(self, score: float) -> str:
        """Convert score to letter rating"""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        elif score >= 50:
            return "C-"
        else:
            return "D"

    def _get_recommendation(
        self,
        overall: float,
        success: float,
        time: float,
        cost: float
    ) -> str:
        """Generate recommendation based on scores"""
        if overall >= 90:
            return "Highly recommended - Excellent reliability and performance across all metrics"
        elif overall >= 80:
            return "Recommended - Good overall performance with minor inconsistencies"
        elif overall >= 70:
            if success < 90:
                return "Acceptable with caution - Lower success rate than ideal"
            elif time < 70:
                return "Acceptable - Completion times can vary significantly"
            elif cost < 70:
                return "Acceptable - Costs can vary significantly"
            else:
                return "Acceptable - Monitor for improvements"
        elif overall >= 60:
            return "Use with caution - Below average reliability, consider alternatives"
        else:
            return "Not recommended - Poor reliability, high risk of issues"

    def _calculate_trend(self, bridge_name: str, db: Session, hours: int) -> str:
        """Calculate trend by comparing current period to previous period"""
        try:
            current_cutoff = datetime.utcnow() - timedelta(hours=hours)
            previous_cutoff = datetime.utcnow() - timedelta(hours=hours * 2)

            # Current period
            current_metrics = db.query(BridgePerformanceMetric).filter(
                and_(
                    BridgePerformanceMetric.bridge_name == bridge_name,
                    BridgePerformanceMetric.calculated_at >= current_cutoff
                )
            ).all()

            # Previous period
            previous_metrics = db.query(BridgePerformanceMetric).filter(
                and_(
                    BridgePerformanceMetric.bridge_name == bridge_name,
                    BridgePerformanceMetric.calculated_at >= previous_cutoff,
                    BridgePerformanceMetric.calculated_at < current_cutoff
                )
            ).all()

            if not current_metrics or not previous_metrics:
                return "insufficient_data"

            current_avg = sum(m.reliability_score for m in current_metrics) / len(current_metrics)
            previous_avg = sum(m.reliability_score for m in previous_metrics) / len(previous_metrics)

            diff = current_avg - previous_avg

            if diff > 5:
                return "improving"
            elif diff < -5:
                return "declining"
            else:
                return "stable"

        except Exception as e:
            log.error(f"Error calculating trend: {str(e)}")
            return "unknown"

    def _no_data_response(self, bridge_name: str) -> Dict:
        """Response when no data is available"""
        return {
            "bridge_name": bridge_name,
            "overall_score": 0,
            "rating": "N/A",
            "recommendation": "Insufficient data - No recent transactions found",
            "trend": "insufficient_data",
            "component_scores": {},
            "metrics": {
                "total_transactions": 0
            },
            "last_updated": datetime.utcnow().isoformat()
        }

    def _error_response(self, bridge_name: str, error: str) -> Dict:
        """Response when error occurs"""
        return {
            "bridge_name": bridge_name,
            "overall_score": 0,
            "rating": "ERROR",
            "recommendation": f"Error calculating score: {error}",
            "trend": "unknown",
            "component_scores": {},
            "metrics": {},
            "last_updated": datetime.utcnow().isoformat()
        }


# Singleton instance
reliability_scorer = ReliabilityScorer()
