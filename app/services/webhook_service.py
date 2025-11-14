"""Webhook notification service"""
import hmac
import hashlib
import httpx
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.webhooks import Webhook, WebhookDelivery
from app.core.logging import log


class WebhookService:
    """Service for sending webhook notifications"""

    def __init__(self):
        self.timeout = 10  # 10 seconds timeout
        self.max_retries = 3

    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for payload"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    async def send_webhook(
        self,
        webhook: Webhook,
        event_type: str,
        data: Dict[str, Any],
        db: Session,
        transaction_id: Optional[int] = None
    ) -> bool:
        """Send webhook notification"""
        try:
            # Build payload
            payload = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }

            payload_json = json.dumps(payload)

            # Generate signature if secret is provided
            headers = {"Content-Type": "application/json"}
            if webhook.secret:
                signature = self._generate_signature(payload_json, webhook.secret)
                headers["X-Webhook-Signature"] = signature
                headers["X-Webhook-Signature-Algorithm"] = "sha256"

            # Send request
            start_time = datetime.utcnow()

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers=headers
                )

            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Log delivery
            delivery = WebhookDelivery(
                webhook_id=webhook.id,
                transaction_id=transaction_id,
                event_type=event_type,
                payload=payload,
                url=webhook.url,
                status_code=response.status_code,
                response_body=response.text[:1000],  # Limit to 1000 chars
                success=response.status_code < 400,
                attempt_number=1,
                delivered_at=datetime.utcnow(),
                response_time_ms=response_time_ms
            )

            db.add(delivery)

            # Update webhook stats
            webhook.total_calls += 1
            if response.status_code < 400:
                webhook.successful_calls += 1
            else:
                webhook.failed_calls += 1
            webhook.last_triggered_at = datetime.utcnow()

            db.commit()

            log.info(f"Webhook {webhook.id} delivered successfully: {event_type}")
            return response.status_code < 400

        except Exception as e:
            log.error(f"Error sending webhook {webhook.id}: {str(e)}")

            # Log failed delivery
            try:
                delivery = WebhookDelivery(
                    webhook_id=webhook.id,
                    transaction_id=transaction_id,
                    event_type=event_type,
                    payload=payload,
                    url=webhook.url,
                    error_message=str(e),
                    success=False,
                    attempt_number=1
                )

                db.add(delivery)

                webhook.total_calls += 1
                webhook.failed_calls += 1
                webhook.last_triggered_at = datetime.utcnow()

                db.commit()
            except Exception as log_error:
                log.error(f"Error logging webhook failure: {str(log_error)}")

            return False

    async def notify_transaction_event(
        self,
        event_type: str,
        transaction_data: Dict[str, Any],
        db: Session,
        transaction_id: Optional[int] = None
    ):
        """
        Notify all active webhooks subscribed to this event type.

        Event types:
        - transaction.created
        - transaction.pending
        - transaction.completed
        - transaction.failed
        - transaction.cancelled
        """
        try:
            # Get all active webhooks subscribed to this event
            webhooks = db.query(Webhook).filter(
                Webhook.is_active == True,
                Webhook.events.contains([event_type])
            ).all()

            # Filter by chain if specified
            source_chain = transaction_data.get("source_chain")
            destination_chain = transaction_data.get("destination_chain")
            bridge = transaction_data.get("bridge")

            results = []
            for webhook in webhooks:
                # Check chain filter
                if webhook.chain_filter:
                    if source_chain not in webhook.chain_filter and \
                       destination_chain not in webhook.chain_filter:
                        continue

                # Check bridge filter
                if webhook.bridge_filter:
                    if bridge not in webhook.bridge_filter:
                        continue

                # Send webhook
                success = await self.send_webhook(
                    webhook,
                    event_type,
                    transaction_data,
                    db,
                    transaction_id
                )
                results.append((webhook.id, success))

            log.info(f"Notified {len(results)} webhooks for event: {event_type}")
            return results

        except Exception as e:
            log.error(f"Error notifying webhooks: {str(e)}")
            return []

    async def test_webhook(self, webhook: Webhook, db: Session) -> Dict[str, Any]:
        """Test a webhook by sending a test event"""
        try:
            test_data = {
                "test": True,
                "message": "This is a test notification from Nexbridge API",
                "webhook_id": webhook.id
            }

            start_time = datetime.utcnow()

            payload = {
                "event_type": "test.ping",
                "timestamp": datetime.utcnow().isoformat(),
                "data": test_data
            }

            payload_json = json.dumps(payload)

            headers = {"Content-Type": "application/json"}
            if webhook.secret:
                signature = self._generate_signature(payload_json, webhook.secret)
                headers["X-Webhook-Signature"] = signature
                headers["X-Webhook-Signature-Algorithm"] = "sha256"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers=headers
                )

            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)

            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "response_body": response.text[:500],
                "response_time_ms": response_time_ms,
                "error_message": None
            }

        except Exception as e:
            return {
                "success": False,
                "status_code": None,
                "response_body": None,
                "response_time_ms": 0,
                "error_message": str(e)
            }


# Global instance
webhook_service = WebhookService()
