"""Health check endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from redis import Redis
from app.db.base import get_db
from app.core.config import settings
from datetime import datetime
import redis


router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION
    }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check including database and redis"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "checks": {
            "database": "unknown",
            "redis": "unknown"
        }
    }

    # Check database connection
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Redis connection
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    return health_status


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe"""
    try:
        db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready"}, 503


@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}
