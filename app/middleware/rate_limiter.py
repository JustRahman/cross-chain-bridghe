"""Rate limiting middleware using SlowAPI"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from app.core.config import settings
from app.core.logging import log


def get_api_key_from_request(request: Request) -> str:
    """
    Extract API key from request for rate limiting.

    Uses API key as the rate limit key instead of IP address.
    """
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        # Fall back to IP address if no API key
        return get_remote_address(request)

    return f"api_key:{api_key}"


# Create limiter instance
limiter = Limiter(
    key_func=get_api_key_from_request,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"]
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors.

    Returns a JSON response with retry-after header.
    """
    log.warning(
        f"Rate limit exceeded for {get_api_key_from_request(request)}: "
        f"{request.url.path}"
    )

    return HTTPException(
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit is {settings.RATE_LIMIT_PER_MINUTE} requests per minute.",
            "retry_after": 60
        },
        headers={
            "Retry-After": "60"
        }
    )


# Tier-based rate limits
TIER_LIMITS = {
    "free": "60/minute",
    "starter": "120/minute",
    "growth": "300/minute",
    "enterprise": "1000/minute"
}


def get_tier_limit(tier: str) -> str:
    """
    Get rate limit string for a tier.

    Args:
        tier: API key tier

    Returns:
        Rate limit string (e.g., "120/minute")
    """
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])
