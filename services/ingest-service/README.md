# Ingest Service (Go)

High-performance event ingestion service that receives security events via HTTP and publishes them to the event bus.

## Architecture

- **Language**: Go 1.21+
- **Framework**: Standard library with custom routing
- **Dependencies**: NATS client, JWT library
- **Throughput Target**: 10,000+ events/sec per instance

## API Endpoints

### POST /v1/ingest/events

Ingest security events.

**Headers:**

- `X-Tenant-ID`: Tenant identifier (required)
- `Authorization`: Bearer JWT token (required)
- `Content-Type`: application/json

**Request Body:**

```json
{
  "category": "auth",
  "severity": 5,
  "actor": {
    "id": "user123",
    "name": "John Doe"
  },
  "target": {
    "id": "webapp-1",
    "name": "Corporate Portal"
  },
  "attributes": {
    "failed_login_count": 1,
    "source_ip": "203.0.113.42"
  }
}
```

**Response:**

```json
{
  "event_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "accepted"
}
```

### GET /health

Health check endpoint.

### GET /ready

Readiness check endpoint.

## Configuration

Environment variables:

- `NATS_URL`: NATS server URL (default: `nats://nats:4222`)
- `JWT_PUBLIC_KEY_PATH`: Path to JWT public key
- `LOG_LEVEL`: Logging level (default: `info`)
- `PORT`: HTTP port (default: `8080`)

## Development

```bash
cd services/ingest-service

# Install dependencies
go mod download

# Run locally
go run main.go

# Run tests
go test -v ./...

# Build
go build -o ingest-service .
```

## Deployment

```bash
# Build Docker image
docker build -t siem-platform/ingest-service:latest .

# Deploy to Kubernetes
helm upgrade --install ingest-service deploy/helm/ingest-service
```

## Sprint 2 Implementation

This service is implemented in **Sprint 2** by the **Ingest Service Agent (Go)**.

See [sub_agents.md](../../.gemini/antigravity/brain/e4ceb0ba-ab8d-4c21-9fd8-006c00066279/sub_agents.md) for detailed specifications.
