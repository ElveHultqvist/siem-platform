import json
from typing import Dict
from datetime import datetime
import structlog
from opensearchpy import OpenSearch, helpers

logger = structlog.get_logger()


class AlertPublisher:
    """Publishes alerts to OpenSearch with tenant-aware indexing"""
    
    def __init__(self, opensearch_url: str):
        self.opensearch_url = opensearch_url
        # Parse URL to get host and port
        if "://" in opensearch_url:
            url_parts = opensearch_url.split("://")[1]
        else:
            url_parts = opensearch_url
        
        host_port = url_parts.split(":")
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 9200
        
        # Create OpenSearch client
        self.client = OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_compress=True,
            use_ssl=False,  # MVPdemo - enable in production
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False
        )
        
        logger.info("OpenSearch client initialized", url=opensearch_url)
    
    async def publish_alert(self, alert: Dict):
        """
        Publish alert to OpenSearch
        
        Args:
            alert: Alert dictionary with tenant_id
        """
        tenant_id = alert.get("tenant_id")
        alert_id = alert.get("alert_id")
        
        if not tenant_id:
            logger.error("Alert missing tenant_id", alert_id=alert_id)
            return
        
        # Index name: alerts-{tenant_id}
        index_name = f"alerts-{tenant_id}"
        
        try:
            # Ensure index exists with mapping
            await self._ensure_index(index_name)
            
            # Index the alert
            response = self.client.index(
                index=index_name,
                id=alert_id,
                body=alert,
                refresh=True  # Make immediately searchable (dev only)
            )
            
            logger.info(
                "Alert published",
                tenant_id=tenant_id,
                alert_id=alert_id,
                index=index_name,
                result=response.get("result")
            )
            
        except Exception as e:
            logger.error(
                "Failed to publish alert",
                tenant_id=tenant_id,
                alert_id=alert_id,
                error=str(e)
            )
            raise
    
    async def _ensure_index(self, index_name: str):
        """Ensure index exists with proper mapping"""
        if self.client.indices.exists(index=index_name):
            return
        
        # Create index with mapping
        mapping = {
            "mappings": {
                "properties": {
                    "tenant_id": {"type": "keyword"},
                    "alert_id": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                    "severity": {"type": "integer"},
                    "rule_name": {"type": "keyword"},
                    "rule_description": {"type": "text"},
                    "actor": {
                        "properties": {
                            "type": {"type": "keyword"},
                            "id": {"type": "keyword"},
                            "name": {"type": "text"}
                        }
                    },
                    "target": {
                        "properties": {
                            "type": {"type": "keyword"},
                            "id": {"type": "keyword"},
                            "name": {"type": "text"}
                        }
                    },
                    "details": {"type": "object"},
                    "related_events": {"type": "keyword"},
                    "tags": {"type": "keyword"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0  # MVP - increase in production
            }
        }
        
        try:
            self.client.indices.create(index=index_name, body=mapping)
            logger.info("Created OpenSearch index", index=index_name)
        except Exception as e:
            logger.warning("Index creation failed (may already exist)", index=index_name, error=str(e))
