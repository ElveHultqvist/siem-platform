# Development Guide

This guide explains how to develop and extend the SIEM platform.

## Adding a New Service

### 1. Create Service Directory

```bash
mkdir -p services/my-service
cd services/my-service
```

### 2. Choose Technology Stack

- **Go**: For high-throughput, low-latency services (ingestion, routing)
- **Python FastAPI**: For business logic, CRUD APIs, analytics

### 3. Implement Service

**Go Service Structure:**

```
my-service/
├── main.go
├── go.mod
├── go.sum
├── Dockerfile
├── internal/
│   ├── handlers/
│   ├── middleware/
│   └── config/
└── tests/
```

**Python Service Structure:**

```
my-service/
├── main.py
├── requirements.txt
├── Dockerfile
├── my_service/
│   ├── api/
│   ├── models/
│   └── config.py
└── tests/
```

### 4. Follow Standards

#### Multi-Tenancy

Every service MUST:

- Extract `X-Tenant-ID` from request headers
- Validate JWT `tenant_id` claim matches header
- Scope all operations to tenant

#### Security

- Never hardcode secrets
- Use structured JSON logging
- Implement health check endpoints (`/health`, `/ready`)
- Add RBAC checks where applicable

#### Testing

- Minimum 70% code coverage
- Unit tests for business logic
- Integration tests for external dependencies

### 5. Create Dockerfile

**Go Dockerfile Template:**

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /build
COPY go.* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o service .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
COPY --from=builder /build/service /service
USER nobody
EXPOSE 8080
CMD ["/service"]
```

**Python Dockerfile Template:**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 6. Create Helm Chart

```bash
mkdir -p deploy/helm/my-service
cd deploy/helm/my-service
```

**Chart.yaml:**

```yaml
apiVersion: v2
name: my-service
description: My Service
type: application
version: 0.1.0
appVersion: "0.1.0"
```

**values.yaml:**

```yaml
replicaCount: 2

image:
  repository: siem-platform/my-service
  tag: "latest"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### 7. Add to Umbrella Chart

Edit `deploy/helm/siem-platform/Chart.yaml`:

```yaml
dependencies:
  - name: my-service
    version: "0.1.0"
    repository: "file://./my-service"
    condition: my-service.enabled
```

### 8. Update Documentation

- Add service description to main README
- Document API endpoints (OpenAPI spec)
- Update architecture diagrams

## Code Style Guide

### Go

- Run `gofmt` before committing
- Use `golangci-lint` for linting
- Follow [Effective Go](https://go.dev/doc/effective_go)
- Use structured logging (zerolog or zap)

**Example:**

```go
package main

import (
    "github.com/rs/zerolog/log"
)

func main() {
    log.Info().
        Str("tenant_id", "acme-corp").
        Str("service", "my-service").
        Msg("Service starting")
}
```

### Python

- Run `black` for formatting
- Use `flake8` and `mypy` for linting and type checking
- Follow PEP 8
- Use FastAPI + Pydantic for APIs

**Example:**

```python
from fastapi import FastAPI, Header
from pydantic import BaseModel
import structlog

app = FastAPI()
logger = structlog.get_logger()

class Event(BaseModel):
    category: str
    severity: int

@app.post("/events")
async def create_event(
    event: Event,
    x_tenant_id: str = Header(...)
):
    logger.info("event_created", tenant_id=x_tenant_id, category=event.category)
    return {"status": "ok"}
```

## Testing

### Go Tests

```bash
cd services/my-service
go test -v -race -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

### Python Tests

```bash
cd services/my-service
pytest tests/ -v --cov=. --cov-report=html
```

## Local Development

### Running a Single Service

```bash
# Go service
cd services/my-service
go run main.go

# Python service
cd services/my-service
uvicorn main:app --reload
```

### Running Full Platform

```bash
make dev-up
```

### Viewing Logs

```bash
# All services
make logs

# Specific service
kubectl logs -n siem-platform -l app=my-service -f
```

## Common Patterns

### Tenant Validation Middleware (Go)

```go
func TenantMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        tenantID := r.Header.Get("X-Tenant-ID")
        if tenantID == "" {
            http.Error(w, "Missing tenant header", http.StatusBadRequest)
            return
        }

        // Validate JWT contains matching tenant_id
        // ... JWT validation logic ...

        ctx := context.WithValue(r.Context(), "tenant_id", tenantID)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

### Tenant Validation Middleware (Python)

```python
from fastapi import Header, HTTPException

async def get_tenant_id(x_tenant_id: str = Header(...)) -> str:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="Missing tenant header")

    # Validate JWT contains matching tenant_id
    # ... JWT validation logic ...

    return x_tenant_id

@app.get("/resource")
async def get_resource(tenant_id: str = Depends(get_tenant_id)):
    # tenant_id is validated and available
    pass
```

## Debugging

### Port Forward to Service

```bash
kubectl port-forward -n siem-platform svc/my-service 8080:80
curl http://localhost:8080/health
```

### Shell into Pod

```bash
kubectl exec -it -n siem-platform \
  $(kubectl get pod -n siem-platform -l app=my-service -o jsonpath='{.items[0].metadata.name}') \
  -- /bin/sh
```

### View Resource Usage

```bash
kubectl top pods -n siem-platform
```

## Performance Tuning

### Go Services

- Use connection pooling for databases
- Implement circuit breakers for external APIs
- Use context for timeouts
- Profile with pprof

### Python Services

- Use async/await for I/O-bound operations
- Implement connection pooling (asyncpg, aioredis)
- Use gunicorn/uvicorn workers based on load
- Profile with cProfile

## Security Checklist

- [ ] No secrets in code or config files
- [ ] All endpoints require authentication
- [ ] Tenant validation on every request
- [ ] Input validation using schemas (Pydantic, JSON Schema)
- [ ] SQL injection prevention (parameterized queries)
- [ ] Rate limiting on public endpoints
- [ ] CORS configured appropriately
- [ ] Security headers set (CSP, HSTS, etc.)

## Pre-Commit Checklist

- [ ] Code formatted (`make fmt`)
- [ ] Linters pass (`make lint`)
- [ ] Tests pass (`make test`)
- [ ] Documentation updated
- [ ] CHANGELOG entry added (if applicable)
- [ ] No secrets committed

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Go by Example](https://gobyexample.com/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Twelve-Factor App](https://12factor.net/)
