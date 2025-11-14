"""Rate limiting service using Redis"""
import redis
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.api_keys import APIKey, RateLimitLog
from app.core.logging import log


class RateLimiter:
    """Rate limiter using Redis for tracking request counts"""

    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )

    def _get_key(self, api_key_id: int, window: str) -> str:
        """Generate Redis key for rate limit tracking"""
        return f"rate_limit:{api_key_id}:{window}"

    def _get_window_expiry(self, window: str) -> int:
        """Get expiry time in seconds for window"""
        if window == "minute":
            return 60
        elif window == "hour":
            return 3600
        elif window == "day":
            return 86400
        return 60

    def check_rate_limit(
        self,
        api_key: APIKey,
        db: Session,
        endpoint: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if request is within rate limits.

        Returns:
            (allowed: bool, reason: Optional[str], retry_after: Optional[int])
        """
        try:
            # Check minute limit
            minute_key = self._get_key(api_key.id, "minute")
            minute_count = self.redis_client.get(minute_key)
            minute_count = int(minute_count) if minute_count else 0

            if minute_count >= api_key.rate_limit_per_minute:
                self._log_violation(api_key.id, "minute", endpoint, db)
                return False, "Rate limit exceeded: requests per minute", 60

            # Check hour limit
            hour_key = self._get_key(api_key.id, "hour")
            hour_count = self.redis_client.get(hour_key)
            hour_count = int(hour_count) if hour_count else 0

            if hour_count >= api_key.rate_limit_per_hour:
                self._log_violation(api_key.id, "hour", endpoint, db)
                return False, "Rate limit exceeded: requests per hour", 3600

            # Check day limit
            day_key = self._get_key(api_key.id, "day")
            day_count = self.redis_client.get(day_key)
            day_count = int(day_count) if day_count else 0

            if day_count >= api_key.rate_limit_per_day:
                self._log_violation(api_key.id, "day", endpoint, db)
                return False, "Rate limit exceeded: requests per day", 86400

            # All checks passed
            return True, None, None

        except Exception as e:
            log.error(f"Error checking rate limit: {str(e)}")
            # Fail open - allow request if Redis is down
            return True, None, None

    def increment_usage(self, api_key_id: int):
        """Increment usage counters for all time windows"""
        try:
            # Increment minute counter
            minute_key = self._get_key(api_key_id, "minute")
            pipe = self.redis_client.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)

            # Increment hour counter
            hour_key = self._get_key(api_key_id, "hour")
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)

            # Increment day counter
            day_key = self._get_key(api_key_id, "day")
            pipe.incr(day_key)
            pipe.expire(day_key, 86400)

            pipe.execute()

        except Exception as e:
            log.error(f"Error incrementing rate limit: {str(e)}")

    def get_current_usage(self, api_key_id: int) -> dict:
        """Get current usage counts for all time windows"""
        try:
            minute_key = self._get_key(api_key_id, "minute")
            hour_key = self._get_key(api_key_id, "hour")
            day_key = self._get_key(api_key_id, "day")

            minute_count = self.redis_client.get(minute_key)
            hour_count = self.redis_client.get(hour_key)
            day_count = self.redis_client.get(day_key)

            return {
                "minute": int(minute_count) if minute_count else 0,
                "hour": int(hour_count) if hour_count else 0,
                "day": int(day_count) if day_count else 0
            }

        except Exception as e:
            log.error(f"Error getting current usage: {str(e)}")
            return {"minute": 0, "hour": 0, "day": 0}

    def reset_usage(self, api_key_id: int, window: Optional[str] = None):
        """Reset usage counters (for testing or manual reset)"""
        try:
            if window:
                key = self._get_key(api_key_id, window)
                self.redis_client.delete(key)
            else:
                # Reset all windows
                self.redis_client.delete(self._get_key(api_key_id, "minute"))
                self.redis_client.delete(self._get_key(api_key_id, "hour"))
                self.redis_client.delete(self._get_key(api_key_id, "day"))

            log.info(f"Reset rate limit for API key {api_key_id}, window: {window or 'all'}")

        except Exception as e:
            log.error(f"Error resetting usage: {str(e)}")

    def _log_violation(self, api_key_id: int, window: str, endpoint: Optional[str], db: Session):
        """Log rate limit violation to database"""
        try:
            violation = RateLimitLog(
                api_key_id=api_key_id,
                endpoint=endpoint,
                limit_type=window,
                occurred_at=datetime.utcnow()
            )
            db.add(violation)
            db.commit()

            log.warning(f"Rate limit violation: API key {api_key_id}, window: {window}, endpoint: {endpoint}")

        except Exception as e:
            log.error(f"Error logging rate limit violation: {str(e)}")
            db.rollback()


# Singleton instance
rate_limiter = RateLimiter()
