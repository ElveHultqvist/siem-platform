import json
import asyncio
from typing import Dict, List
import structlog
from nats.aio.client import Client as NATS
from nats.js.api import StreamConfig

from detect.engine import DetectionEngine
from detect.alerts import AlertPublisher

logger = structlog.get_logger()


class EventConsumer:
    """NATS consumer for normalized events"""
    
    def __init__(
        self,
        nats_url: str,
        engine: DetectionEngine,
        alert_publisher: AlertPublisher
    ):
        self.nats_url = nats_url
        self.engine = engine
        self.alert_publisher = alert_publisher
        self.nc: NATS = None
        self.js = None
        self._running = False
    
    def is_connected(self) -> bool:
        """Check if NATS is connected"""
        return self.nc is not None and self.nc.is_connected
    
    async def start(self):
        """Start consuming events from NATS"""
        try:
            # Connect to NATS
            self.nc = NATS()
            await self.nc.connect(self.nats_url)
            self.js = self.nc.jetstream()
            
            logger.info("Connected to NATS", url=self.nats_url)
            
            # Ensure stream exists (in production, this would be handled by ops)
            try:
                await self.js.add_stream(
                    StreamConfig(
                        name="EVENTS",
                        subjects=["normalized.events.*", "raw.events.*"]
                    )
                )
            except Exception as e:
                logger.debug("Stream already exists or creation failed", error=str(e))
            
            # Subscribe to normalized events for all tenants
            subscription = await self.js.subscribe(
                "normalized.events.*",
                durable="detect-service"
            )
            
            logger.info("Subscribed to normalized events")
            
            self._running = True
            
            # Process messages
            while self._running:
                try:
                    msg = await subscription.next_msg(timeout=1.0)
                    await self._handle_message(msg)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error("Error processing message", error=str(e))
        
        except Exception as e:
            logger.error("Failed to start consumer", error=str(e))
            raise
    
    async def stop(self):
        """Stop consuming events"""
        self._running = False
        if self.nc:
            await self.nc.close()
            logger.info("NATS connection closed")
    
    async def _handle_message(self, msg):
        """Handle a single NATS message"""
        try:
            # Parse event
            event_data = msg.data.decode()
            event = json.loads(event_data)
            
            tenant_id = event.get("tenant_id")
            event_id = event.get("event_id")
            
            logger.debug(
                "Received event",
                tenant_id=tenant_id,
                event_id=event_id,
                category=event.get("category")
            )
            
            # Process through detection engine
            alerts = await self.engine.process_event(event)
            
            # Publish alerts
            for alert in alerts:
                await self.alert_publisher.publish_alert(alert)
            
            # Acknowledge message
            await msg.ack()
            
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in message", error=str(e))
            await msg.nak()
        except Exception as e:
            logger.error("Failed to handle message", error=str(e))
            await msg.nak()
