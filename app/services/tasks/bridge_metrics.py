"""Celery tasks for bridge performance metrics"""
from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.db.base import SessionLocal
from app.db.models.analytics import BridgePerformanceMetric
from app.db.models.transactions import TransactionHistory
from app.core.logging import log


@shared_task(name="calculate_bridge_performance_metrics")
def calculate_bridge_performance_metrics():
    """
    Calculate and store bridge performance metrics.

    Runs every hour via Celery Beat.
    Analyzes transaction history to compute:
    - Success rates
    - Average completion times
    - Cost metrics
    - Reliability scores
    """
    db = SessionLocal()
    try:
        # Calculate metrics for the last hour
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(hours=1)

        # Get all unique bridge/route combinations from transactions
        routes = db.query(
            TransactionHistory.selected_bridge,
            TransactionHistory.source_chain,
            TransactionHistory.destination_chain
        ).filter(
            and_(
                TransactionHistory.created_at >= period_start,
                TransactionHistory.created_at < period_end
            )
        ).distinct().all()

        metrics_created = 0

        for bridge, source_chain, dest_chain in routes:
            try:
                # Get all transactions for this route
                transactions = db.query(TransactionHistory).filter(
                    and_(
                        TransactionHistory.selected_bridge == bridge,
                        TransactionHistory.source_chain == source_chain,
                        TransactionHistory.destination_chain == dest_chain,
                        TransactionHistory.created_at >= period_start,
                        TransactionHistory.created_at < period_end
                    )
                ).all()

                if not transactions:
                    continue

                total = len(transactions)
                successful = len([t for t in transactions if t.status == "completed"])
                failed = len([t for t in transactions if t.status == "failed"])

                success_rate = (successful / total * 100) if total > 0 else 0.0

                # Calculate timing metrics
                completion_times = [
                    t.actual_time_minutes for t in transactions
                    if t.actual_time_minutes is not None
                ]

                avg_time = sum(completion_times) / len(completion_times) if completion_times else None
                min_time = min(completion_times) if completion_times else None
                max_time = max(completion_times) if completion_times else None

                # Calculate cost metrics
                costs = [
                    t.actual_cost_usd for t in transactions
                    if t.actual_cost_usd is not None
                ]

                avg_cost = sum(costs) / len(costs) if costs else None
                min_cost = min(costs) if costs else None
                max_cost = max(costs) if costs else None

                # Calculate reliability score (0-100)
                # Factors: success rate (70%), timing consistency (20%), cost consistency (10%)
                reliability_score = success_rate * 0.7

                if completion_times and len(completion_times) > 1:
                    # Add timing consistency bonus
                    time_variance = max(completion_times) - min(completion_times)
                    if avg_time and avg_time > 0:
                        consistency = max(0, 1 - (time_variance / avg_time))
                        reliability_score += consistency * 20

                if costs and len(costs) > 1:
                    # Add cost consistency bonus
                    cost_variance = max(costs) - min(costs)
                    if avg_cost and avg_cost > 0:
                        consistency = max(0, 1 - (cost_variance / avg_cost))
                        reliability_score += consistency * 10

                # Create metric record
                metric = BridgePerformanceMetric(
                    bridge_name=bridge,
                    source_chain=source_chain,
                    destination_chain=dest_chain,
                    total_transactions=total,
                    successful_transactions=successful,
                    failed_transactions=failed,
                    success_rate=success_rate,
                    avg_completion_time_minutes=int(avg_time) if avg_time else None,
                    min_completion_time_minutes=int(min_time) if min_time else None,
                    max_completion_time_minutes=int(max_time) if max_time else None,
                    avg_cost_usd=avg_cost,
                    min_cost_usd=min_cost,
                    max_cost_usd=max_cost,
                    reliability_score=reliability_score,
                    period_start=period_start,
                    period_end=period_end
                )

                db.add(metric)
                metrics_created += 1

                log.info(f"Calculated metrics for {bridge} {source_chain}->{dest_chain}")

            except Exception as e:
                log.error(f"Error calculating metrics for {bridge}: {str(e)}")

        db.commit()
        log.info(f"Bridge metrics calculation complete: {metrics_created} metrics created")

        return {"success": True, "metrics_created": metrics_created}

    except Exception as e:
        db.rollback()
        log.error(f"Error in bridge metrics task: {str(e)}")
        return {"success": False, "error": str(e)}

    finally:
        db.close()


@shared_task(name="update_liquidity_snapshots")
def update_liquidity_snapshots():
    """
    Update liquidity snapshots for all bridges.

    Runs every 10 minutes via Celery Beat.
    Monitors available liquidity on each bridge for each chain.
    """
    db = SessionLocal()
    try:
        from app.db.models.analytics import LiquiditySnapshot
        from app.services.route_discovery import route_discovery_engine

        snapshots_created = 0

        # For each bridge, check liquidity on supported chains
        for bridge in route_discovery_engine.bridges:
            for chain_id in bridge.supported_chains:
                try:
                    # Mock liquidity check - in production, query bridge contracts
                    # For now, generate reasonable mock data

                    chain_names = {
                        1: "ethereum",
                        10: "optimism",
                        42161: "arbitrum",
                        137: "polygon",
                        8453: "base"
                    }

                    chain_name = chain_names.get(chain_id, f"chain_{chain_id}")

                    # Mock liquidity data
                    available_liquidity = "50000000000"  # 50,000 USDC
                    available_liquidity_usd = 50000.0
                    total_liquidity_usd = 100000.0
                    utilization_rate = 50.0

                    # Determine status
                    if utilization_rate < 70:
                        status = "sufficient"
                    elif utilization_rate < 85:
                        status = "low"
                    else:
                        status = "critical"

                    snapshot = LiquiditySnapshot(
                        bridge_name=bridge.name,
                        chain_id=chain_id,
                        chain_name=chain_name,
                        token="USDC",
                        available_liquidity=available_liquidity,
                        available_liquidity_usd=available_liquidity_usd,
                        total_liquidity_usd=total_liquidity_usd,
                        utilization_rate=utilization_rate,
                        is_sufficient=status
                    )

                    db.add(snapshot)
                    snapshots_created += 1

                except Exception as e:
                    log.error(f"Error creating liquidity snapshot for {bridge.name} on chain {chain_id}: {str(e)}")

        db.commit()
        log.info(f"Liquidity snapshots updated: {snapshots_created} snapshots")

        return {"success": True, "snapshots_created": snapshots_created}

    except Exception as e:
        db.rollback()
        log.error(f"Error in liquidity snapshots task: {str(e)}")
        return {"success": False, "error": str(e)}

    finally:
        db.close()
