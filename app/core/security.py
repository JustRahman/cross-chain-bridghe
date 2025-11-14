"""Security utilities for API key management and authentication"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, status, Request, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.base import get_db
from app.db.models.api_keys import APIKey, APIUsage


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    """Generate a secure random API key"""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash"""
    return hash_api_key(plain_key) == hashed_key


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


async def get_api_key_from_query(
    api_key: str,
    db: Session = Depends(get_db)
) -> str:
    """
    Validate API key from query parameter (for WebSocket connections).

    Args:
        api_key: API key from query parameter
        db: Database session

    Returns:
        The API key string if valid

    Raises:
        HTTPException if invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required in query parameter",
        )

    # Validate the API key exists and is active
    api_key_obj = db.query(APIKey).filter(APIKey.key == api_key).first()

    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if api_key_obj.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has been revoked",
        )

    if not api_key_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is inactive",
        )

    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )

    return api_key


async def get_api_key(
    api_key_str: str = Security(api_key_header),
    request: Request = None,
    db: Session = Depends(get_db)
) -> APIKey:
    """
    Dependency to validate API key and enforce rate limits.

    Checks:
    - API key exists
    - Not revoked
    - Not expired
    - Is active
    - IP whitelist (if configured)
    - Endpoint restrictions (if configured)
    - Rate limits

    Returns the APIKey object if valid.
    """
    if not api_key_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required. Include X-API-Key header.",
        )

    # Look up API key in database
    api_key = db.query(APIKey).filter(APIKey.key == api_key_str).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Check if revoked
    if api_key.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"API key has been revoked: {api_key.revoke_reason or 'No reason provided'}",
        )

    # Check if expired
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key has expired",
        )

    # Check if active
    if not api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is not active",
        )

    # Check IP whitelist if configured
    if api_key.allowed_ip_addresses and request:
        client_ip = request.client.host
        if client_ip not in api_key.allowed_ip_addresses:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"IP address {client_ip} not allowed for this API key",
            )

    # Check endpoint restrictions if configured
    if api_key.allowed_endpoints and request:
        endpoint = request.url.path
        # Check if any allowed endpoint pattern matches
        allowed = False
        for pattern in api_key.allowed_endpoints:
            if pattern in endpoint or endpoint.startswith(pattern):
                allowed = True
                break

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Endpoint {endpoint} not allowed for this API key",
            )

    # Check rate limits
    from app.services.rate_limiter import rate_limiter

    endpoint = request.url.path if request else None
    allowed, reason, retry_after = rate_limiter.check_rate_limit(api_key, db, endpoint)

    if not allowed:
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=reason,
            headers=headers
        )

    # Increment usage counter
    rate_limiter.increment_usage(api_key.id)

    # Update last used timestamp
    api_key.last_used_at = datetime.utcnow()
    db.commit()

    return api_key
