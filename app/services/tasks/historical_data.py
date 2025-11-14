"""Celery tasks for collecting historical data"""
from celery import shared_task
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.db.models.analytics import HistoricalGasPrice, HistoricalTokenPrice
from app.services.gas_estimator import gas_estimator
from app.services.token_prices import token_price_service
from app.core.logging import log


@shared_task(name="collect_gas_prices")
def collect_historical_gas_prices():
    """
    Collect and store current gas prices for all chains.

    Runs every 5 minutes via Celery Beat.
    """
    db = SessionLocal()
    try:
        chains = [
            (1, "ethereum"),
            (10, "optimism"),
            (42161, "arbitrum"),
            (137, "polygon"),
            (8453, "base"),
            (56, "bsc"),
            (43114, "avalanche"),
            (250, "fantom")
        ]

        records_created = 0

        for chain_id, chain_name in chains:
            try:
                # Fetch current gas prices
                gas_data = gas_estimator.get_gas_prices_sync(chain_id)

                if gas_data:
                    record = HistoricalGasPrice(
                        chain_id=chain_id,
                        chain_name=chain_name,
                        slow=gas_data.get("slow", 0),
                        standard=gas_data.get("standard", 0),
                        fast=gas_data.get("fast", 0),
                        rapid=gas_data.get("rapid", 0),
                        estimated_gas_limit=100000
                    )

                    db.add(record)
                    records_created += 1
                    log.info(f"Collected gas prices for {chain_name}")

            except Exception as e:
                log.error(f"Error collecting gas prices for {chain_name}: {str(e)}")

        db.commit()
        log.info(f"Gas price collection complete: {records_created} records")

        return {"success": True, "records_created": records_created}

    except Exception as e:
        db.rollback()
        log.error(f"Error in gas price collection task: {str(e)}")
        return {"success": False, "error": str(e)}

    finally:
        db.close()


@shared_task(name="collect_token_prices")
def collect_historical_token_prices():
    """
    Collect and store current token prices.

    Runs every 5 minutes via Celery Beat.
    """
    db = SessionLocal()
    try:
        # Get all token prices
        prices = token_price_service.get_all_prices_sync()

        if not prices:
            log.warning("No token prices returned")
            return {"success": False, "error": "No prices returned"}

        records_created = 0

        for token_symbol, price_data in prices.items():
            try:
                record = HistoricalTokenPrice(
                    token_symbol=token_symbol,
                    price_usd=price_data.get("price", 0),
                    market_cap=price_data.get("market_cap"),
                    volume_24h=price_data.get("volume_24h"),
                    price_change_24h=price_data.get("price_change_24h")
                )

                db.add(record)
                records_created += 1

            except Exception as e:
                log.error(f"Error storing price for {token_symbol}: {str(e)}")

        db.commit()
        log.info(f"Token price collection complete: {records_created} records")

        return {"success": True, "records_created": records_created}

    except Exception as e:
        db.rollback()
        log.error(f"Error in token price collection task: {str(e)}")
        return {"success": False, "error": str(e)}

    finally:
        db.close()


@shared_task(name="cleanup_old_data")
def cleanup_old_historical_data(days_to_keep: int = 90):
    """
    Clean up historical data older than specified days.

    Runs daily via Celery Beat.
    """
    db = SessionLocal()
    try:
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Delete old gas prices
        gas_deleted = db.query(HistoricalGasPrice).filter(
            HistoricalGasPrice.recorded_at < cutoff_date
        ).delete()

        # Delete old token prices
        token_deleted = db.query(HistoricalTokenPrice).filter(
            HistoricalTokenPrice.recorded_at < cutoff_date
        ).delete()

        db.commit()

        log.info(f"Cleanup complete: {gas_deleted} gas records, {token_deleted} token records deleted")

        return {
            "success": True,
            "gas_records_deleted": gas_deleted,
            "token_records_deleted": token_deleted
        }

    except Exception as e:
        db.rollback()
        log.error(f"Error in cleanup task: {str(e)}")
        return {"success": False, "error": str(e)}

    finally:
        db.close()
