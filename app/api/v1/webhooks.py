"""Webhook management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List

from app.db.base import get_db
from app.db.models.webhooks import Webhook, WebhookDelivery
from app.schemas.webhooks import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookListResponse,
    WebhookDeliveryResponse,
    WebhookTestRequest,
    WebhookTestResponse
)
from app.services.webhook_service import webhook_service
from app.core.security import get_api_key
from app.core.logging import log


router = APIRouter()


@router.post("/", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    webhook: WebhookCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Create a new webhook.

    Supported events:
    - transaction.created
    - transaction.pending
    - transaction.completed
    - transaction.failed
    - transaction.cancelled
    """
    try:
        # Validate events
        valid_events = [
            "transaction.created",
            "transaction.pending",
            "transaction.completed",
            "transaction.failed",
            "transaction.cancelled"
        ]

        invalid_events = [e for e in webhook.events if e not in valid_events]
        if invalid_events:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid events: {invalid_events}. Valid events: {valid_events}"
            )

        db_webhook = Webhook(
            url=str(webhook.url),
            secret=webhook.secret,
            events=webhook.events,
            chain_filter=webhook.chain_filter,
            bridge_filter=webhook.bridge_filter,
            user_email=webhook.user_email,
            is_active=True
        )

        db.add(db_webhook)
        db.commit()
        db.refresh(db_webhook)

        log.info(f"Created webhook: {db_webhook.id}")
        return db_webhook

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log.error(f"Error creating webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create webhook: {str(e)}")


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Get a specific webhook by ID"""
    try:
        webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()

        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

        return webhook

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get webhook: {str(e)}")


@router.get("/", response_model=WebhookListResponse)
async def list_webhooks(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """List all webhooks"""
    try:
        query = db.query(Webhook)

        if is_active is not None:
            query = query.filter(Webhook.is_active == is_active)

        webhooks = query.order_by(desc(Webhook.created_at)).all()

        return WebhookListResponse(
            webhooks=webhooks,
            total=len(webhooks)
        )

    except Exception as e:
        log.error(f"Error listing webhooks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list webhooks: {str(e)}")


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    update_data: WebhookUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Update webhook configuration"""
    try:
        webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()

        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            if key == "url" and value:
                value = str(value)
            setattr(webhook, key, value)

        db.commit()
        db.refresh(webhook)

        log.info(f"Updated webhook: {webhook_id}")
        return webhook

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log.error(f"Error updating webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update webhook: {str(e)}")


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Delete a webhook"""
    try:
        webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()

        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

        db.delete(webhook)
        db.commit()

        log.info(f"Deleted webhook: {webhook_id}")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log.error(f"Error deleting webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete webhook: {str(e)}")


@router.post("/test", response_model=WebhookTestResponse)
async def test_webhook(
    test_request: WebhookTestRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Test a webhook by sending a test event.

    Useful for verifying webhook configuration before going live.
    """
    try:
        webhook = db.query(Webhook).filter(Webhook.id == test_request.webhook_id).first()

        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

        result = await webhook_service.test_webhook(webhook, db)

        return WebhookTestResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error testing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to test webhook: {str(e)}")


@router.get("/{webhook_id}/deliveries", response_model=List[WebhookDeliveryResponse])
async def get_webhook_deliveries(
    webhook_id: int,
    limit: int = Query(50, ge=1, le=200, description="Number of deliveries to return"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Get delivery logs for a specific webhook"""
    try:
        webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()

        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

        deliveries = db.query(WebhookDelivery).filter(
            WebhookDelivery.webhook_id == webhook_id
        ).order_by(desc(WebhookDelivery.created_at)).limit(limit).all()

        return deliveries

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting webhook deliveries: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get deliveries: {str(e)}")
