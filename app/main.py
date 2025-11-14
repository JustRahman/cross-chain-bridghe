"""Main FastAPI application entry point"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from app.core.config import settings
from app.core.logging import log
from app.api.v1 import routes, bridges, health, transactions, utilities, transaction_history, webhooks, slippage, gas_optimization, api_keys, analytics, simulator
from app.api import websocket
from app.db.base import engine, Base
from app.db import models  # Import models to register them with Base
from app.middleware import UsageTrackingMiddleware
import sentry_sdk


# Initialize Sentry if DSN is provided
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        traces_sample_rate=0.1 if settings.APP_ENV == "production" else 1.0,
        # Add data like request headers and IP for users
        send_default_pii=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the application"""
    # Startup
    log.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    log.info(f"Environment: {settings.APP_ENV}")

    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        log.info("Database tables created successfully")
    except Exception as e:
        log.error(f"Failed to create database tables: {e}")

    yield

    # Shutdown
    log.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title="Nexbridge API",
    version=settings.APP_VERSION,
    description="Bridge aggregation API. Compare 10 protocols, optimize costs, real-time data.",
    lifespan=lifespan,
    docs_url=None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add usage tracking middleware
app.add_middleware(UsageTrackingMiddleware)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    log.info(f"Static files mounted from {static_dir}")

# Include routers
app.include_router(
    health.router,
    prefix="",
    tags=["health"]
)

app.include_router(
    routes.router,
    prefix=f"{settings.API_V1_PREFIX}/routes",
    tags=["routes"]
)

app.include_router(
    bridges.router,
    prefix=f"{settings.API_V1_PREFIX}/bridges",
    tags=["bridges"]
)

app.include_router(
    transactions.router,
    prefix=f"{settings.API_V1_PREFIX}/transactions",
    tags=["transactions"]
)

app.include_router(
    utilities.router,
    prefix=f"{settings.API_V1_PREFIX}/utilities",
    tags=["utilities"]
)

app.include_router(
    transaction_history.router,
    prefix=f"{settings.API_V1_PREFIX}/transaction-history",
    tags=["transaction-history"]
)

app.include_router(
    webhooks.router,
    prefix=f"{settings.API_V1_PREFIX}/webhooks",
    tags=["webhooks"]
)

app.include_router(
    slippage.router,
    prefix=f"{settings.API_V1_PREFIX}/slippage",
    tags=["slippage"]
)

app.include_router(
    gas_optimization.router,
    prefix=f"{settings.API_V1_PREFIX}/gas-optimization",
    tags=["gas-optimization"]
)

app.include_router(
    api_keys.router,
    prefix=f"{settings.API_V1_PREFIX}/api-keys",
    tags=["api-keys"]
)

app.include_router(
    analytics.router,
    prefix=f"{settings.API_V1_PREFIX}/analytics",
    tags=["analytics"]
)

app.include_router(
    simulator.router,
    prefix=f"{settings.API_V1_PREFIX}/simulator",
    tags=["simulator"]
)

# WebSocket endpoints
app.include_router(
    websocket.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["websocket"]
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page"""
    index_file = Path(__file__).parent / "static" / "index.html"
    if index_file.exists():
        with open(index_file, "r") as f:
            return f.read()
    else:
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "operational",
            "docs": "/docs" if settings.DEBUG else "Contact support for API documentation"
        }


@app.get("/docs", include_in_schema=False)
async def custom_docs():
    """API documentation"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title
    )


@app.get("/sentry-debug")
async def trigger_error():
    """Sentry debug endpoint - triggers an error to test Sentry integration"""
    division_by_zero = 1 / 0
    return division_by_zero


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
