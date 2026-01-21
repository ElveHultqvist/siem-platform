import signal
import sys
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from case_service.config import settings
from case_service.database import Database
from case_service.api import cases, alerts

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global database instance
db: Database = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global db
    
    logger.info("Starting case management service", version="0.1.0")
    
    # Initialize database connection pool
    db = Database(settings.database_url)
    await db.connect()
    
    # Run migrations
    await db.run_migrations()
    
    logger.info("Case service started", database_url=settings.database_url.split("@")[-1])
    
    yield
    
    # Shutdown
    logger.info("Shutting down case service")
    if db:
        await db.disconnect()
    logger.info("Case service stopped")


# Create FastAPI app
app = FastAPI(
    title="SIEM Case Management",
    description="Incident case management and alert tracking",
    version="0.1.0",
    lifespan=lifespan
)

# Include routers
app.include_router(cases.router, prefix="/v1", tags=["cases"])
app.include_router(alerts.router, prefix="/v1", tags=["alerts"])


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    """Readiness check endpoint"""
    is_ready = db is not None and await db.is_connected()
    return {"status": "ready" if is_ready else "not ready"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint (stub)"""
    return {"message": "Metrics not yet implemented"}


def handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal", signal=signum)
    sys.exit(0)


if __name__ == "__main__":
    import uvicorn
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Run server
    uv icorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=True
    )
