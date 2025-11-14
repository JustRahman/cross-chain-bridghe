"""API key management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import secrets

from app.db.base import get_db
from app.db.models.api_keys import APIKey, APIUsage, RateLimitLog
from app.schemas.api_keys import (
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
    APIKeyCreatedResponse,
    APIKeyListResponse,
    APIKeyRevokeRequest,
    APIKeyUsageStats,
    APIKeyUsageResponse
)
from app.core.security import get_api_key
from app.core.logging import log
from app.services.rate_limiter import rate_limiter


router = APIRouter()


def generate_api_key() -> str:
    """Generate secure random API key"""
    return f"nxb_{secrets.token_urlsafe(32)}"


@router.post("/", response_model=APIKeyCreatedResponse, status_code=201)
async def create_api_key(
    key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)  # Admin authentication required
):
    """
    Create a new API key.

    Generates a unique API key with configurable:
    - Rate limits (per minute, hour, day)
    - Endpoint restrictions
    - Chain restrictions
    - IP whitelist
    - Expiration date

    **Note:** The API key value is only shown once. Save it securely!
    """
    try:
        # Generate unique API key
        new_key = generate_api_key()

        # Calculate expiration
        expires_at = None
        if key_data.expires_days:
            expires_at = datetime.utcnow() + timedelta(days=key_data.expires_days)

        # Create API key record
        db_key = APIKey(
            key=new_key,
            name=key_data.name,
            description=key_data.description,
            user_email=key_data.user_email,
            is_active=True,
            rate_limit_per_minute=key_data.rate_limit_per_minute,
            rate_limit_per_hour=key_data.rate_limit_per_hour,
            rate_limit_per_day=key_data.rate_limit_per_day,
            allowed_endpoints=key_data.allowed_endpoints,
            allowed_chains=key_data.allowed_chains,
            allowed_ip_addresses=key_data.allowed_ip_addresses,
            expires_at=expires_at
        )

        db.add(db_key)
        db.commit()
        db.refresh(db_key)

        log.info(f"Created API key: {db_key.id} for {key_data.user_email}")

        # Return response with actual key (only time it's shown)
        response = APIKeyCreatedResponse(
            id=db_key.id,
            key=new_key,  # Include actual key
            name=db_key.name,
            description=db_key.description,
            user_email=db_key.user_email,
            is_active=db_key.is_active,
            is_revoked=db_key.is_revoked,
            rate_limit_per_minute=db_key.rate_limit_per_minute,
            rate_limit_per_hour=db_key.rate_limit_per_hour,
            rate_limit_per_day=db_key.rate_limit_per_day,
            total_requests=db_key.total_requests,
            successful_requests=db_key.successful_requests,
            failed_requests=db_key.failed_requests,
            last_used_at=db_key.last_used_at,
            allowed_endpoints=db_key.allowed_endpoints,
            allowed_chains=db_key.allowed_chains,
            allowed_ip_addresses=db_key.allowed_ip_addresses,
            created_at=db_key.created_at,
            updated_at=db_key.updated_at,
            expires_at=db_key.expires_at,
            revoked_at=db_key.revoked_at,
            revoke_reason=db_key.revoke_reason
        )

        return response

    except Exception as e:
        db.rollback()
        log.error(f"Error creating API key: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create API key: {str(e)}")


@router.get("/", response_model=APIKeyListResponse)
async def list_api_keys(
    user_email: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    List all API keys.

    Optionally filter by:
    - User email
    - Active status
    """
    try:
        query = db.query(APIKey)

        if user_email:
            query = query.filter(APIKey.user_email == user_email)
        if is_active is not None:
            query = query.filter(APIKey.is_active == is_active)

        keys = query.order_by(desc(APIKey.created_at)).all()

        return APIKeyListResponse(
            keys=keys,
            total=len(keys)
        )

    except Exception as e:
        log.error(f"Error listing API keys: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list API keys: {str(e)}")


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key_details(
    key_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Get details for a specific API key"""
    try:
        key = db.query(APIKey).filter(APIKey.id == key_id).first()

        if not key:
            raise HTTPException(status_code=404, detail="API key not found")

        return key

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting API key: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get API key: {str(e)}")


@router.patch("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: int,
    update_data: APIKeyUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Update API key configuration.

    Can update:
    - Name and description
    - Active status
    - Rate limits
    - Access restrictions
    """
    try:
        key = db.query(APIKey).filter(APIKey.id == key_id).first()

        if not key:
            raise HTTPException(status_code=404, detail="API key not found")

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(key, field, value)

        db.commit()
        db.refresh(key)

        log.info(f"Updated API key: {key_id}")
        return key

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log.error(f"Error updating API key: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update API key: {str(e)}")


@router.post("/{key_id}/revoke", response_model=APIKeyResponse)
async def revoke_api_key(
    key_id: int,
    revoke_data: APIKeyRevokeRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Revoke an API key.

    Revoked keys cannot be reactivated. A revocation reason is required.
    """
    try:
        key = db.query(APIKey).filter(APIKey.id == key_id).first()

        if not key:
            raise HTTPException(status_code=404, detail="API key not found")

        if key.is_revoked:
            raise HTTPException(status_code=400, detail="API key already revoked")

        # Revoke the key
        key.is_revoked = True
        key.is_active = False
        key.revoked_at = datetime.utcnow()
        key.revoke_reason = revoke_data.reason

        db.commit()
        db.refresh(key)

        log.info(f"Revoked API key: {key_id} - Reason: {revoke_data.reason}")
        return key

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log.error(f"Error revoking API key: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to revoke API key: {str(e)}")


@router.delete("/{key_id}", status_code=204)
async def delete_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Delete an API key permanently.

    **Warning:** This action cannot be undone.
    Consider revoking instead if you need to keep audit history.
    """
    try:
        key = db.query(APIKey).filter(APIKey.id == key_id).first()

        if not key:
            raise HTTPException(status_code=404, detail="API key not found")

        db.delete(key)
        db.commit()

        log.info(f"Deleted API key: {key_id}")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log.error(f"Error deleting API key: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete API key: {str(e)}")


@router.get("/{key_id}/usage", response_model=APIKeyUsageResponse)
async def get_api_key_usage(
    key_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get detailed usage statistics for an API key.

    Includes:
    - Total and recent request counts
    - Success/failure rates
    - Most used endpoints and chains
    - Average response time
    - Current rate limit status
    - Recent errors
    """
    try:
        key = db.query(APIKey).filter(APIKey.id == key_id).first()

        if not key:
            raise HTTPException(status_code=404, detail="API key not found")

        # Calculate success rate
        success_rate = 0.0
        if key.total_requests > 0:
            success_rate = (key.successful_requests / key.total_requests) * 100

        # Get requests in last 24 hours
        last_24h = datetime.utcnow() - timedelta(hours=24)
        requests_24h = db.query(func.count(APIUsage.id)).filter(
            APIUsage.api_key_id == key_id,
            APIUsage.created_at >= last_24h
        ).scalar() or 0

        # Get requests in last hour
        last_hour = datetime.utcnow() - timedelta(hours=1)
        requests_hour = db.query(func.count(APIUsage.id)).filter(
            APIUsage.api_key_id == key_id,
            APIUsage.created_at >= last_hour
        ).scalar() or 0

        # Most used endpoint
        most_used_endpoint = db.query(
            APIUsage.endpoint,
            func.count(APIUsage.id).label('count')
        ).filter(
            APIUsage.api_key_id == key_id
        ).group_by(APIUsage.endpoint).order_by(desc('count')).first()

        # Average response time
        avg_response_time = db.query(
            func.avg(APIUsage.response_time_ms)
        ).filter(
            APIUsage.api_key_id == key_id
        ).scalar()

        # Recent errors (last 10)
        recent_errors = db.query(APIUsage).filter(
            APIUsage.api_key_id == key_id,
            APIUsage.status_code >= 400
        ).order_by(desc(APIUsage.created_at)).limit(10).all()

        stats = APIKeyUsageStats(
            api_key_id=key.id,
            api_key_name=key.name,
            total_requests=key.total_requests,
            successful_requests=key.successful_requests,
            failed_requests=key.failed_requests,
            success_rate=success_rate,
            requests_last_24h=requests_24h,
            requests_last_hour=requests_hour,
            most_used_endpoint=most_used_endpoint[0] if most_used_endpoint else None,
            most_used_chain=None,
            average_response_time_ms=int(avg_response_time) if avg_response_time else None,
            last_used_at=key.last_used_at
        )

        # Calculate current rate limit status
        rate_limits = {
            "minute": {
                "limit": key.rate_limit_per_minute,
                "used": min(requests_hour, key.rate_limit_per_minute),
                "remaining": max(0, key.rate_limit_per_minute - requests_hour)
            },
            "hour": {
                "limit": key.rate_limit_per_hour,
                "used": requests_hour,
                "remaining": max(0, key.rate_limit_per_hour - requests_hour)
            },
            "day": {
                "limit": key.rate_limit_per_day,
                "used": requests_24h,
                "remaining": max(0, key.rate_limit_per_day - requests_24h)
            }
        }

        # Format recent errors
        errors = [
            {
                "timestamp": e.created_at.isoformat(),
                "endpoint": e.endpoint,
                "status_code": e.status_code,
                "error": e.error_message
            }
            for e in recent_errors
        ]

        return APIKeyUsageResponse(
            stats=stats,
            rate_limits=rate_limits,
            recent_errors=errors
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting API key usage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get usage: {str(e)}")


@router.get("/{key_id}/rate-limits")
async def get_rate_limit_status(
    key_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get current rate limit status for an API key.

    Shows:
    - Current usage in each time window
    - Configured limits
    - Remaining capacity
    - Reset times
    """
    try:
        key = db.query(APIKey).filter(APIKey.id == key_id).first()

        if not key:
            raise HTTPException(status_code=404, detail="API key not found")

        # Get current usage from Redis
        current_usage = rate_limiter.get_current_usage(key.id)

        return {
            "api_key_id": key.id,
            "api_key_name": key.name,
            "rate_limits": {
                "minute": {
                    "limit": key.rate_limit_per_minute,
                    "used": current_usage["minute"],
                    "remaining": max(0, key.rate_limit_per_minute - current_usage["minute"]),
                    "reset_in_seconds": 60
                },
                "hour": {
                    "limit": key.rate_limit_per_hour,
                    "used": current_usage["hour"],
                    "remaining": max(0, key.rate_limit_per_hour - current_usage["hour"]),
                    "reset_in_seconds": 3600
                },
                "day": {
                    "limit": key.rate_limit_per_day,
                    "used": current_usage["day"],
                    "remaining": max(0, key.rate_limit_per_day - current_usage["day"]),
                    "reset_in_seconds": 86400
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting rate limit status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get rate limit status: {str(e)}")


@router.post("/{key_id}/rate-limits/reset")
async def reset_rate_limits(
    key_id: int,
    window: str = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Reset rate limit counters for an API key.

    Useful for testing or manual override. Admin only.

    Query parameters:
    - window: Optional time window to reset (minute, hour, day). If not specified, resets all.
    """
    try:
        key = db.query(APIKey).filter(APIKey.id == key_id).first()

        if not key:
            raise HTTPException(status_code=404, detail="API key not found")

        # Validate window if provided
        if window and window not in ["minute", "hour", "day"]:
            raise HTTPException(status_code=400, detail="Invalid window. Must be: minute, hour, or day")

        # Reset rate limits
        rate_limiter.reset_usage(key.id, window)

        log.info(f"Rate limits reset for API key {key_id}, window: {window or 'all'}")

        return {
            "success": True,
            "message": f"Rate limits reset for {window or 'all'} window(s)",
            "api_key_id": key.id
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error resetting rate limits: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset rate limits: {str(e)}")


@router.get("/{key_id}/violations")
async def get_rate_limit_violations(
    key_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Get recent rate limit violations for an API key.

    Helps identify usage patterns and potential abuse.
    """
    try:
        key = db.query(APIKey).filter(APIKey.id == key_id).first()

        if not key:
            raise HTTPException(status_code=404, detail="API key not found")

        # Get violations
        violations = db.query(RateLimitLog).filter(
            RateLimitLog.api_key_id == key_id
        ).order_by(desc(RateLimitLog.created_at)).limit(limit).all()

        return {
            "api_key_id": key.id,
            "api_key_name": key.name,
            "total_violations": len(violations),
            "violations": [
                {
                    "id": v.id,
                    "endpoint": v.endpoint,
                    "limit_type": v.limit_type,
                    "occurred_at": v.occurred_at.isoformat()
                }
                for v in violations
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting violations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get violations: {str(e)}")
