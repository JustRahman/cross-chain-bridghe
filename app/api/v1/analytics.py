"""Analytics dashboard endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, case
from datetime import datetime, timedelta
from typing import List

from app.db.base import get_db
from app.db.models.api_keys import APIKey, APIUsage
from app.db.models.transactions import TransactionHistory
from app.db.models.webhooks import WebhookDelivery
from app.db.models.analytics import BridgePerformanceMetric, HistoricalGasPrice
from app.schemas.analytics import (
    AnalyticsDashboardResponse,
    SystemHealthMetrics,
    EndpointStats,
    ChainStats,
    BridgePopularity,
    TimeSeriesDataPoint,
    UserAnalyticsResponse,
    BridgeReliabilityScore,
    ReliabilityScoresResponse
)
from app.core.security import get_api_key
from app.core.logging import log
from app.services.reliability_scorer import reliability_scorer


router = APIRouter()


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
async def get_analytics_dashboard(
    hours: int = Query(24, ge=1, le=168, description="Hours of data to analyze"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get comprehensive analytics dashboard.

    Provides:
    - System health metrics
    - Top endpoints by usage
    - Chain statistics
    - Bridge popularity ranking
    - Request volume over time
    - Error rates

    Perfect for monitoring and business intelligence.
    """
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # System health metrics
        total_requests = db.query(func.count(APIUsage.id)).filter(
            APIUsage.created_at >= cutoff
        ).scalar() or 0

        total_transactions = db.query(func.count(TransactionHistory.id)).filter(
            TransactionHistory.created_at >= cutoff
        ).scalar() or 0

        avg_response_time = db.query(func.avg(APIUsage.response_time_ms)).filter(
            APIUsage.created_at >= cutoff
        ).scalar() or 0

        error_requests = db.query(func.count(APIUsage.id)).filter(
            and_(
                APIUsage.created_at >= cutoff,
                APIUsage.status_code >= 400
            )
        ).scalar() or 0

        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0

        active_keys = db.query(func.count(APIKey.id)).filter(
            APIKey.is_active == True
        ).scalar() or 0

        webhook_deliveries = db.query(func.count(WebhookDelivery.id)).filter(
            WebhookDelivery.created_at >= cutoff
        ).scalar() or 0

        successful_webhooks = db.query(func.count(WebhookDelivery.id)).filter(
            and_(
                WebhookDelivery.created_at >= cutoff,
                WebhookDelivery.success == True
            )
        ).scalar() or 0

        webhook_success_rate = (successful_webhooks / webhook_deliveries * 100) if webhook_deliveries > 0 else 100

        system_health = SystemHealthMetrics(
            total_requests_24h=total_requests,
            total_transactions_24h=total_transactions,
            average_response_time_ms=int(avg_response_time),
            error_rate_percent=round(error_rate, 2),
            active_api_keys=active_keys,
            rate_limit_violations_24h=0,  # TODO: Implement rate limit tracking
            webhook_deliveries_24h=webhook_deliveries,
            webhook_success_rate=round(webhook_success_rate, 2)
        )

        # Top endpoints
        endpoint_data = db.query(
            APIUsage.endpoint,
            func.count(APIUsage.id).label('total'),
            func.sum(case((APIUsage.status_code < 400, 1), else_=0)).label('successful'),
            func.sum(case((APIUsage.status_code >= 400, 1), else_=0)).label('failed'),
            func.avg(APIUsage.response_time_ms).label('avg_time'),
            func.min(APIUsage.response_time_ms).label('min_time'),
            func.max(APIUsage.response_time_ms).label('max_time')
        ).filter(
            APIUsage.created_at >= cutoff
        ).group_by(APIUsage.endpoint).order_by(desc('total')).limit(10).all()

        top_endpoints = [
            EndpointStats(
                endpoint=row.endpoint,
                total_requests=row.total,
                successful_requests=row.successful,
                failed_requests=row.failed,
                success_rate=round((row.successful / row.total * 100) if row.total > 0 else 0, 2),
                average_response_time_ms=int(row.avg_time) if row.avg_time else 0,
                min_response_time_ms=int(row.min_time) if row.min_time else 0,
                max_response_time_ms=int(row.max_time) if row.max_time else 0
            )
            for row in endpoint_data
        ]

        # Chain statistics
        chain_data = db.query(
            TransactionHistory.source_chain,
            func.count(TransactionHistory.id).label('total'),
            func.sum(TransactionHistory.actual_cost_usd).label('volume')
        ).filter(
            TransactionHistory.created_at >= cutoff
        ).group_by(TransactionHistory.source_chain).all()

        chain_stats = []
        for row in chain_data:
            # Get average gas price for chain
            chain_ids = {"ethereum": 1, "arbitrum": 42161, "optimism": 10, "polygon": 137, "base": 8453}
            chain_id = chain_ids.get(row.source_chain, 1)

            avg_gas = db.query(func.avg(HistoricalGasPrice.standard)).filter(
                and_(
                    HistoricalGasPrice.chain_id == chain_id,
                    HistoricalGasPrice.recorded_at >= cutoff
                )
            ).scalar() or 30.0

            # Most popular bridge for this chain
            popular_bridge = db.query(
                TransactionHistory.selected_bridge,
                func.count(TransactionHistory.id).label('count')
            ).filter(
                and_(
                    TransactionHistory.source_chain == row.source_chain,
                    TransactionHistory.created_at >= cutoff
                )
            ).group_by(TransactionHistory.selected_bridge).order_by(desc('count')).first()

            chain_stats.append(ChainStats(
                chain_name=row.source_chain,
                chain_id=chain_id,
                total_transactions=row.total,
                total_volume_usd=float(row.volume) if row.volume else 0.0,
                average_gas_price_gwei=float(avg_gas),
                most_popular_bridge=popular_bridge[0] if popular_bridge else "unknown"
            ))

        # Bridge popularity
        bridge_data = db.query(
            TransactionHistory.selected_bridge,
            func.count(TransactionHistory.id).label('total'),
            func.sum(case((TransactionHistory.status == 'completed', 1), else_=0)).label('successful'),
            func.avg(TransactionHistory.actual_cost_usd).label('avg_cost'),
            func.avg(TransactionHistory.actual_time_minutes).label('avg_time')
        ).filter(
            TransactionHistory.created_at >= cutoff
        ).group_by(TransactionHistory.selected_bridge).order_by(desc('total')).all()

        bridge_popularity = [
            BridgePopularity(
                bridge_name=row.selected_bridge,
                total_uses=row.total,
                success_rate=round((row.successful / row.total * 100) if row.total > 0 else 0, 2),
                average_cost_usd=round(float(row.avg_cost), 2) if row.avg_cost else 0.0,
                average_time_minutes=int(row.avg_time) if row.avg_time else 0
            )
            for row in bridge_data
        ]

        # Time series data (hourly for last 24h)
        requests_over_time = []
        error_rate_over_time = []

        for i in range(hours):
            hour_start = datetime.utcnow() - timedelta(hours=hours-i)
            hour_end = hour_start + timedelta(hours=1)

            hour_requests = db.query(func.count(APIUsage.id)).filter(
                and_(
                    APIUsage.created_at >= hour_start,
                    APIUsage.created_at < hour_end
                )
            ).scalar() or 0

            hour_errors = db.query(func.count(APIUsage.id)).filter(
                and_(
                    APIUsage.created_at >= hour_start,
                    APIUsage.created_at < hour_end,
                    APIUsage.status_code >= 400
                )
            ).scalar() or 0

            requests_over_time.append(TimeSeriesDataPoint(
                timestamp=hour_start.isoformat(),
                value=float(hour_requests)
            ))

            error_rate = (hour_errors / hour_requests * 100) if hour_requests > 0 else 0
            error_rate_over_time.append(TimeSeriesDataPoint(
                timestamp=hour_start.isoformat(),
                value=round(error_rate, 2)
            ))

        return AnalyticsDashboardResponse(
            system_health=system_health,
            top_endpoints=top_endpoints,
            chain_statistics=chain_stats,
            bridge_popularity=bridge_popularity,
            requests_over_time=requests_over_time,
            error_rate_over_time=error_rate_over_time,
            generated_at=datetime.utcnow()
        )

    except Exception as e:
        log.error(f"Error generating analytics dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")


@router.get("/reliability-scores", response_model=ReliabilityScoresResponse)
async def get_reliability_scores(
    hours: int = Query(24, ge=1, le=168, description="Hours of data to analyze"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get reliability scores for all bridges.

    Analyzes:
    - Success rates
    - Completion times
    - Cost efficiency
    - Overall reliability (0-100 score)

    Helps users choose the most reliable bridges.
    """
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # Get performance metrics for each bridge
        metrics = db.query(BridgePerformanceMetric).filter(
            BridgePerformanceMetric.calculated_at >= cutoff
        ).all()

        # Aggregate by bridge
        bridge_stats = {}

        for metric in metrics:
            if metric.bridge_name not in bridge_stats:
                bridge_stats[metric.bridge_name] = {
                    "total_transactions": 0,
                    "successful": 0,
                    "failed": 0,
                    "completion_times": [],
                    "costs": [],
                    "reliability_scores": []
                }

            stats = bridge_stats[metric.bridge_name]
            stats["total_transactions"] += metric.total_transactions
            stats["successful"] += metric.successful_transactions
            stats["failed"] += metric.failed_transactions

            if metric.avg_completion_time_minutes:
                stats["completion_times"].append(metric.avg_completion_time_minutes)
            if metric.avg_cost_usd:
                stats["costs"].append(metric.avg_cost_usd)
            if metric.reliability_score:
                stats["reliability_scores"].append(metric.reliability_score)

        # Calculate scores
        scores = []

        for bridge_name, stats in bridge_stats.items():
            total = stats["total_transactions"]
            if total == 0:
                continue

            success_rate = (stats["successful"] / total * 100) if total > 0 else 0
            avg_time = sum(stats["completion_times"]) / len(stats["completion_times"]) if stats["completion_times"] else 0
            avg_cost = sum(stats["costs"]) / len(stats["costs"]) if stats["costs"] else 0
            reliability = sum(stats["reliability_scores"]) / len(stats["reliability_scores"]) if stats["reliability_scores"] else 75.0

            # Calculate uptime
            uptime = success_rate  # Simplified

            # Cost rating
            if avg_cost < 5:
                cost_rating = "cheap"
            elif avg_cost < 15:
                cost_rating = "moderate"
            else:
                cost_rating = "expensive"

            # Speed rating
            if avg_time < 3:
                speed_rating = "fast"
            elif avg_time < 8:
                speed_rating = "moderate"
            else:
                speed_rating = "slow"

            # Recommendation
            if reliability >= 90 and success_rate >= 95:
                recommendation = "Highly recommended - excellent reliability and performance"
            elif reliability >= 75 and success_rate >= 90:
                recommendation = "Recommended - good reliability"
            elif reliability >= 60:
                recommendation = "Acceptable - monitor for issues"
            else:
                recommendation = "Use with caution - below average reliability"

            scores.append(BridgeReliabilityScore(
                bridge_name=bridge_name,
                reliability_score=round(reliability, 2),
                success_rate=round(success_rate, 2),
                average_completion_time_minutes=int(avg_time),
                total_transactions_analyzed=total,
                uptime_percentage=round(uptime, 2),
                cost_rating=cost_rating,
                speed_rating=speed_rating,
                recommendation=recommendation
            ))

        # Sort by reliability score
        scores.sort(key=lambda x: x.reliability_score, reverse=True)

        return ReliabilityScoresResponse(
            scores=scores,
            analysis_period_hours=hours,
            last_updated=datetime.utcnow()
        )

    except Exception as e:
        log.error(f"Error calculating reliability scores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate scores: {str(e)}")


@router.get("/bridge-reliability/{bridge_name}")
async def get_bridge_reliability(
    bridge_name: str,
    hours: int = Query(168, ge=24, le=720, description="Hours to analyze (1-30 days)"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get comprehensive reliability analysis for a specific bridge.

    Provides detailed breakdown:
    - Overall reliability score (0-100)
    - Component scores with weights
    - Success rate analysis
    - Time and cost consistency
    - Uptime metrics
    - Volume analysis
    - Trend (improving/stable/declining)
    - Detailed recommendations

    Perfect for:
    - Choosing the most reliable bridge
    - Monitoring bridge performance
    - Risk assessment
    """
    try:
        # Normalize bridge name
        bridge_name = bridge_name.lower()

        log.info(f"Reliability analysis requested for bridge: {bridge_name}, period: {hours}h")

        # Calculate comprehensive score
        result = reliability_scorer.calculate_comprehensive_score(
            bridge_name=bridge_name,
            db=db,
            hours=hours
        )

        return result

    except Exception as e:
        log.error(f"Error getting bridge reliability: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get reliability: {str(e)}")


@router.get("/bridge-comparison")
async def compare_bridges(
    bridges: str = Query(..., description="Comma-separated bridge names to compare"),
    hours: int = Query(168, ge=24, le=720, description="Hours to analyze"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Compare reliability scores across multiple bridges.

    Query parameters:
    - bridges: Comma-separated list (e.g., "across,hop,stargate")
    - hours: Analysis period (default: 168 = 7 days)

    Returns:
    - Side-by-side comparison
    - Rankings
    - Best choice recommendation
    """
    try:
        # Parse bridge names
        bridge_list = [b.strip().lower() for b in bridges.split(",")]

        if len(bridge_list) < 2:
            raise HTTPException(status_code=400, detail="At least 2 bridges required for comparison")

        if len(bridge_list) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 bridges for comparison")

        log.info(f"Bridge comparison requested: {bridge_list}, period: {hours}h")

        # Get scores for all bridges
        comparisons = []

        for bridge_name in bridge_list:
            score_data = reliability_scorer.calculate_comprehensive_score(
                bridge_name=bridge_name,
                db=db,
                hours=hours
            )
            comparisons.append(score_data)

        # Sort by overall score (highest first)
        comparisons.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

        # Determine best choice
        best_bridge = comparisons[0] if comparisons else None

        return {
            "bridges_compared": len(comparisons),
            "analysis_period_hours": hours,
            "comparisons": comparisons,
            "best_choice": {
                "bridge_name": best_bridge["bridge_name"],
                "overall_score": best_bridge["overall_score"],
                "rating": best_bridge["rating"],
                "reason": "Highest overall reliability score"
            } if best_bridge else None,
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error comparing bridges: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to compare bridges: {str(e)}")
