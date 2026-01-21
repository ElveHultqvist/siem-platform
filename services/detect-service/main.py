import asyncio
import signal
import sys
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from detect.config import settings
from detect.consumer import EventConsumer
from detect.engine import DetectionEngine
from detect.alerts import AlertPublisher

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

# Global consumer instance
consumer: EventConsumer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global consumer
    
    logger.info("Starting detection engine", version="0.1.0")
    
    # Initialize components
    engine = DetectionEngine()
    alert_publisher = AlertPublisher(settings.opensearch_url)
    
    # Start NATS consumer
    consumer = EventConsumer(
        nats_url=settings.nats_url,
        engine=engine,
        alert_publisher=alert_publisher
    )
    
    # Start consuming in background
    asyncio.create_task(consumer.start())
    
    logger.info("Detection engine started", nats_url=settings.nats_url)
    
    yield
    
    # Shutdown
    logger.info("Shutting down detection engine")
    if consumer:
        await consumer.stop()
    logger.info("Detection engine stopped")


# Create FastAPI app
app = FastAPI(
    title="SIEM Detection Engine",
    description="Rule-based threat detection engine",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    """Readiness check endpoint"""
    is_ready = consumer is not None and consumer.is_connected()
    status_code = 200 if is_ready else 503
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
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=True
    )
