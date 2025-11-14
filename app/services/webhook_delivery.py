"""
Webhook delivery service for transaction status notifications.

Handles:
- Sending webhook notifications on transaction status changes
- Retry logic with exponential backoff
- Delivery status tracking
"""
import aiohttp
import asyncio
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.logging import log
from app.db.models.webhooks import Webhook, WebhookDelivery
from app.models.transaction import Transaction


class WebhookDeliveryService:
    """Service for delivering webhook notifications"""

    def __init__(self):
        self.max_retries = 5
        self.initial_retry_delay = 2  # seconds
        self.max_retry_delay = 300  # 5 minutes
        self.timeout = 30  # seconds

    async def notify_transaction_update(
        self,
        db: Session,
        transaction: Transaction,
        event_type: str = "transaction.updated"
    ):
        """
        Send webhook notifications for a transaction update.

        Args:
            db: Database session
            transaction: Transaction that was updated
            event_type: Type of event (transaction.created, transaction.updated, transaction.completed, etc.)
        """
        try:
            # Get all active webhooks for this API key
            webhooks = db.query(Webhook).filter(
                Webhook.api_key_id == transaction.api_key_id,
                Webhook.is_active == True
            ).all()

            if not webhooks:
                log.debug(f"No webhooks configured for API key {transaction.api_key_id}")
                return

            # Build webhook payload
            payload = self._build_payload(transaction, event_type)

            # Send to all webhooks
            for webhook in webhooks:
                # Check if this webhook should receive this event
                if not self._should_send_event(webhook, event_type):
                    continue

                # Create delivery record
                delivery = WebhookDelivery(
                    webhook_id=webhook.id,
                    transaction_id=transaction.id,
                    event_type=event_type,
                    payload=payload,
                    url=webhook.url,
                    attempt_number=0,
                    success=False,
                    created_at=datetime.utcnow()
                )
                db.add(delivery)
                db.commit()
                db.refresh(delivery)

                # Send webhook in background
                asyncio.create_task(
                    self._deliver_webhook(webhook.url, payload, delivery.id, webhook.secret)
                )

        except Exception as e:
            log.error(f"Error notifying transaction update: {e}")

    def _build_payload(self, transaction: Transaction, event_type: str) -> Dict:
        """Build webhook payload from transaction"""
        return {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "id": transaction.id,
                "source_tx_hash": transaction.source_tx_hash,
                "destination_tx_hash": transaction.destination_tx_hash,
                "status": transaction.status,
                "bridge_name": transaction.bridge_name,
                "source_chain": transaction.source_chain,
                "destination_chain": transaction.destination_chain,
                "source_token": transaction.source_token,
                "destination_token": transaction.destination_token,
                "amount": transaction.amount,
                "amount_received": transaction.amount_received,
                "estimated_time_seconds": transaction.estimated_time_seconds,
                "error_message": transaction.error_message,
                "created_at": transaction.created_at.isoformat() if transaction.created_at else None,
                "updated_at": transaction.updated_at.isoformat() if transaction.updated_at else None,
                "completed_at": transaction.completed_at.isoformat() if transaction.completed_at else None,
            }
        }

    def _should_send_event(self, webhook: Webhook, event_type: str) -> bool:
        """Check if webhook should receive this event type"""
        if not webhook.events:
            # If no events specified, send all events
            return True

        # Check if event type matches any configured events
        for event in webhook.events:
            if event == event_type or event == "*" or event_type.startswith(event.rstrip("*")):
                return True

        return False

    async def _deliver_webhook(
        self,
        url: str,
        payload: Dict,
        delivery_id: int,
        secret: Optional[str] = None
    ):
        """
        Deliver webhook with retry logic.

        Args:
            url: Webhook URL
            payload: Payload to send
            delivery_id: WebhookDelivery ID for tracking
            secret: Optional webhook secret for signature
        """
        from app.db.base import SessionLocal

        db = SessionLocal()
        retry_count = 0
        delay = self.initial_retry_delay

        try:
            delivery = db.query(WebhookDelivery).filter(
                WebhookDelivery.id == delivery_id
            ).first()

            if not delivery:
                log.error(f"Webhook delivery {delivery_id} not found")
                return

            while retry_count < self.max_retries:
                try:
                    # Prepare headers
                    headers = {
                        "Content-Type": "application/json",
                        "User-Agent": "Nexbridge-Webhook/1.0"
                    }

                    # Add signature if secret provided
                    if secret:
                        import hmac
                        import hashlib
                        import json

                        payload_bytes = json.dumps(payload, sort_keys=True).encode()
                        signature = hmac.new(
                            secret.encode(),
                            payload_bytes,
                            hashlib.sha256
                        ).hexdigest()
                        headers["X-Webhook-Signature"] = f"sha256={signature}"

                    # Send webhook
                    start_time = datetime.utcnow()
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            url,
                            json=payload,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=self.timeout)
                        ) as response:
                            response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                            delivery.attempt_number += 1
                            delivery.status_code = response.status
                            delivery.response_body = await response.text()
                            delivery.response_time_ms = response_time_ms

                            if 200 <= response.status < 300:
                                # Success
                                delivery.success = True
                                delivery.delivered_at = datetime.utcnow()
                                db.commit()
                                log.info(f"Webhook delivered successfully to {url}")
                                return
                            else:
                                # Non-2xx response
                                log.warning(
                                    f"Webhook returned {response.status} for {url}, "
                                    f"attempt {retry_count + 1}/{self.max_retries}"
                                )

                except asyncio.TimeoutError:
                    delivery.attempt_number += 1
                    delivery.error_message = "Request timeout"
                    log.warning(
                        f"Webhook timeout for {url}, "
                        f"attempt {retry_count + 1}/{self.max_retries}"
                    )

                except Exception as e:
                    delivery.attempt_number += 1
                    delivery.error_message = str(e)
                    log.warning(
                        f"Webhook error for {url}: {e}, "
                        f"attempt {retry_count + 1}/{self.max_retries}"
                    )

                # Save attempt
                db.commit()

                # Retry logic
                retry_count += 1
                if retry_count < self.max_retries:
                    # Exponential backoff
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, self.max_retry_delay)

            # All retries exhausted
            delivery.success = False
            delivery.error_message = f"Failed after {self.max_retries} attempts"
            db.commit()
            log.error(f"Webhook delivery failed after {self.max_retries} attempts to {url}")

        except Exception as e:
            log.error(f"Error in webhook delivery: {e}")
        finally:
            db.close()

    async def retry_failed_deliveries(self, db: Session, hours_ago: int = 24):
        """
        Retry failed webhook deliveries from the last N hours.

        Args:
            db: Database session
            hours_ago: How many hours back to look for failed deliveries
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_ago)

            failed_deliveries = db.query(WebhookDelivery).filter(
                WebhookDelivery.success == False,
                WebhookDelivery.created_at >= cutoff_time,
                WebhookDelivery.attempt_number < self.max_retries
            ).all()

            log.info(f"Retrying {len(failed_deliveries)} failed webhook deliveries")

            for delivery in failed_deliveries:
                webhook = db.query(Webhook).filter(
                    Webhook.id == delivery.webhook_id,
                    Webhook.is_active == True
                ).first()

                if webhook:
                    # Retry delivery
                    asyncio.create_task(
                        self._deliver_webhook(
                            webhook.url,
                            delivery.payload,
                            delivery.id,
                            webhook.secret
                        )
                    )

        except Exception as e:
            log.error(f"Error retrying failed deliveries: {e}")


# Global instance
webhook_delivery = WebhookDeliveryService()
