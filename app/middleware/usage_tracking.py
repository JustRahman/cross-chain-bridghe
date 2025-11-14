"""Middleware for tracking API usage"""
import time
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.db.models.api_keys import APIKey, APIUsage
from app.core.logging import log


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track API usage for analytics"""

    async def dispatch(self, request: Request, call_next):
        """Track request and response"""

        # Skip tracking for health check and static files
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        if request.url.path.startswith("/static"):
            return await call_next(request)

        # Start timer
        start_time = time.time()

        # Get API key from header
        api_key_str = request.headers.get("X-API-Key")
        api_key_id = None

        # Process request
        response = await call_next(request)

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Track usage if API key is present
        if api_key_str:
            try:
                # Create new database session for tracking
                db = SessionLocal()

                # Look up API key
                api_key = db.query(APIKey).filter(APIKey.key == api_key_str).first()

                if api_key:
                    api_key_id = api_key.id

                    # Create usage record
                    usage = APIUsage(
                        api_key_id=api_key.id,
                        endpoint=request.url.path,
                        method=request.method,
                        status_code=response.status_code,
                        response_time_ms=response_time_ms,
                        ip_address=request.client.host if request.client else None,
                        user_agent=request.headers.get("User-Agent"),
                        error_message=None,  # Could extract from response if needed
                        created_at=datetime.utcnow()
                    )

                    db.add(usage)

                    # Update API key statistics
                    # Note: Legacy database only tracks total_requests
                    # successful/failed counts can be calculated from api_usage table
                    api_key.total_requests = (api_key.total_requests or 0) + 1
                    api_key.last_used_at = datetime.utcnow()

                    db.commit()

                db.close()

            except Exception as e:
                log.error(f"Error tracking API usage: {str(e)}")
                # Don't fail the request if tracking fails
                try:
                    db.rollback()
                    db.close()
                except:
                    pass

        # Add custom headers
        response.headers["X-Response-Time"] = f"{response_time_ms}ms"

        if api_key_id:
            response.headers["X-API-Key-ID"] = str(api_key_id)

        return response
