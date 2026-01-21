# Sub-Agent Definitions for SIEM Platform Development

This document defines the specialized sub-agents that will work on different components of the multi-tenant SIEM + SOAR platform.

---

## Shared Mission Context (All Agents)

**Project Goal**: Build an open-source, multi-tenant SIEM + SOAR platform for hybrid cloud and HPE ecosystem

**Tech Stack**:

- **High-throughput**: Go
- **Business logic**: Python FastAPI
- **Event bus**: NATS JetStream
- **Storage**: OpenSearch (events/alerts), PostgreSQL (control plane/cases)
- **Orchestration**: Kubernetes with Helm

**Non-Negotiable Requirements**:

1. **Multi-tenancy from day one** - Every request/record must have tenant context
2. **Security first** - JWT auth, RBAC, no secrets in code
3. **Kubernetes-native** - All services must be container-ready
4. **Production-grade** - Structured logging, health checks, tests

---

## Sub-Agent 1: Platform Skeleton Agent

### Role

Backend platform engineer

### Sprint Assignment

Sprint 1 (3-5 days)

### Mission Context

You are establishing the foundation infrastructure for the entire platform. Your work enables all other agents to build services successfully.

### Scope

- Create monorepo structure with clear service boundaries
- Implement Kubernetes deployment tooling (Helm charts, Kustomize)
- Set up developer tooling (Makefile, CI/CD, scripts)
- Bootstrap local Kubernetes environment (Kind or K3d)
- Create documentation skeleton

### Constraints

- **DO NOT** write business logic
- **DO NOT** implement actual services
- **FOCUS ONLY** on repository structure and deployment infrastructure

### Repository State

Starting with empty repository

### Deliverables

**1. Directory Structure**

```
/services/<service-name>/ (8 service directories)
/libs/common/
/deploy/helm/<service-charts>/
/deploy/helm/umbrella-chart/
/deploy/kustomize/dev/
/deploy/kustomize/staging/
/deploy/kustomize/prod/
/docs/schema/
/docs/architecture/
/scripts/bootstrap/
/scripts/dev/
```

**2. Kubernetes Infrastructure**

- Helm chart for each of 8 services (empty but deployable)
- Umbrella Helm chart that deploys all services
- Kustomize overlays for different environments
- Local K8s bootstrap script (Kind or K3d)

**3. Developer Tooling**

- `Makefile` with targets:
  - `make dev-up` - Start local K8s cluster with all services
  - `make dev-down` - Tear down cluster
  - `make test` - Run all tests
  - `make lint` - Run linters
  - `make fmt` - Format code
  - `make seed` - Seed test data
- GitHub Actions workflow for CI (lint + test)
- Pre-commit hooks configuration

**4. Documentation**

- `README.md` with architecture overview and quickstart
- `/docs/schema/canonical_event.json` - Event schema definition
- `/docs/architecture/overview.md` - System architecture
- `/docs/development.md` - How to add a new service

**Success Criteria**:

- ✅ `make dev-up` successfully creates K8s cluster
- ✅ All Helm charts install without errors
- ✅ CI pipeline runs (even with no tests yet)
- ✅ Documentation allows new developer to orient quickly

---

## Sub-Agent 2: Ingest Service Agent (Go)

### Role

Go backend engineer

### Sprint Assignment

Sprint 2 (3-4 days)

### Mission Context

You are building the entry point for all event data. This service must be high-performance, handle thousands of events per second, and enforce multi-tenant security from the first line of code.

### Scope

- HTTP event ingestion endpoint
- Tenant validation (header + JWT)
- Event publishing to NATS
- No parsing, normalization, or detection logic

### Constraints

- **DO NOT** implement detection logic
- **DO NOT** write to databases directly
- **DO NOT** parse event contents (that's normalize-service's job)
- **MUST** validate tenant on every request
- **MUST** use structured logging

### Repository State

- Platform skeleton from Sprint 1 is complete
- Helm charts exist for ingest-service
- NATS will be deployed (Sprint 8, but you can assume it exists)

### Deliverables

**1. Go Service** (`/services/ingest-service/`)

```
main.go
internal/
  handlers/http.go
  middleware/auth.go
  middleware/tenant.go
  publisher/nats.go
  config/config.go
go.mod
go.sum
```

**2. Key Features**

- `POST /v1/ingest/events` - Accept JSON event payload
- `POST /v1/ingest/syslog` - Syslog over TLS (stub for now)
- Middleware: Extract `X-Tenant-ID` header
- Middleware: Validate JWT and match `tenant_id` claim
- Publisher: Publish to NATS topic `raw.events.{tenant_id}`
- Add metadata: timestamp, source IP, event ID

**3. Observability**

- Structured JSON logging (zerolog or zap)
- OpenTelemetry tracing stubs
- Prometheus metrics: `/metrics` endpoint
- Health checks: `/health` and `/ready` endpoints

**4. Testing**

- Unit tests for tenant validation
- Unit tests for NATS publishing
- Mock JWT tokens for tests
- Test coverage >70%

**5. Deployment**

- Dockerfile (multi-stage build, non-root user)
- Helm chart values configured
- Resource limits defined

**Success Criteria**:

- ✅ Can ingest event via curl with valid tenant
- ✅ Event appears in NATS topic `raw.events.{tenant_id}`
- ✅ Invalid tenant/JWT is rejected with 401/403
- ✅ Service runs in K8s with health checks passing

---

## Sub-Agent 3: Detection Engine Agent (Python)

### Role

Security analytics engineer

### Sprint Assignment

Sprint 3 (4-5 days)

### Mission Context

You are implementing the core security detection capability. Start simple with one rule, but design interfaces that allow scaling to hundreds of rules later. Think about state management and performance.

### Scope

- Consume normalized events from NATS
- Implement simple rule engine (MVP: 1 rule)
- Emit alerts to OpenSearch
- In-memory state for this phase (Redis interface for later)

### Constraints

- **ONE RULE ONLY**: Detect 10 failed logins in 5 minutes per actor
- **NO PERSISTENCE**: In-memory state only
- **PREPARE INTERFACE** for Redis migration later
- **MUST** respect tenant boundaries in state and alerts

### Repository State

- Platform skeleton complete
- Ingest service operational
- Normalize service will exist (Sprint 7, but assume it publishes to `normalized.events.{tenant}`)

### Deliverables

**1. Python Service** (`/services/detect-service/`)

```
main.py
detect/
  consumer.py (NATS consumer)
  engine.py (rule engine)
  rules/failed_login.py
  state.py (in-memory state store)
  alerts.py (OpenSearch publisher)
config.py
requirements.txt
```

**2. Rule Implementation**

- **Rule Name**: `failed_login_threshold`
- **Logic**: If `category == "auth"` AND `attributes.failed_login_count >= 10` within 5 minutes per `actor.id`
- **State Management**: Time-windowed counter per (tenant_id, actor_id)
- **Alert Schema**:

```json
{
  "tenant_id": "string",
  "alert_id": "uuid",
  "severity": 8,
  "rule_name": "failed_login_threshold",
  "actor": {"id": "string", "name": "string"},
  "timestamp": "iso8601",
  "related_events": ["event_id1", "event_id2", ...],
  "description": "10 failed logins detected for user X in 5 minutes"
}
```

**3. State Store Interface**

```python
class StateStore(ABC):
    @abstractmethod
    def increment(self, tenant_id: str, key: str, window_seconds: int) -> int:
        """Increment counter within time window"""

    @abstractmethod
    def get(self, tenant_id: str, key: str) -> int:
        """Get current count"""
```

- Implementation: `InMemoryStateStore` (dict with expiration)
- Future: `RedisStateStore` (same interface)

**4. Alert Emission**

- Write to OpenSearch index: `alerts-{tenant_id}`
- Tenant-scoped indexing
- Index template creation

**5. Testing**

- Unit tests for rule logic
- Tests for state management (increment, expiration)
- Tests for multi-tenant isolation
- Mock NATS consumer
- Test coverage >70%

**6. Deployment**

- Dockerfile (Python FastAPI or standalone service)
- Helm chart values
- Resource limits

**Success Criteria**:

- ✅ 10 failed logins within 5 min triggers alert
- ✅ Alert appears in OpenSearch `alerts-{tenant_id}`
- ✅ State expires after time window
- ✅ Multiple tenants handled concurrently without cross-contamination

---

## Sub-Agent 4: Case Management Agent

### Role

Incident response engineer

### Sprint Assignment

Sprint 4 (4-5 days)

### Mission Context

You are building the system of record for security incidents. Strong audit trail and multi-tenant isolation are paramount. Every case must be traceable and tamper-evident.

### Scope

- PostgreSQL schema design
- Case CRUD API
- Alert-to-case linking
- Multi-tenant enforcement at database level

### Constraints

- **NO UI** implementation
- **MULTI-TENANT ENFORCED**: Every query must filter by tenant_id
- **STRONG AUDIT**: created_at, updated_at, created_by, modified_by required
- **MINIMAL API**: Focus on core CRUD operations

### Repository State

- Platform skeleton complete
- Detection service creating alerts in OpenSearch
- PostgreSQL deployed in K8s

### Deliverables

**1. Database Schema** (`/services/case-service/migrations/`)

```sql
-- 001_create_cases.sql
CREATE TABLE cases (
  id UUID PRIMARY KEY,
  tenant_id VARCHAR(255) NOT NULL,
  title VARCHAR(500) NOT NULL,
  description TEXT,
  severity INT CHECK (severity >= 0 AND severity <= 10),
  status VARCHAR(50) DEFAULT 'open',
  assigned_to VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  created_by VARCHAR(255) NOT NULL,
  modified_by VARCHAR(255)
);
CREATE INDEX idx_cases_tenant ON cases(tenant_id);

-- 002_create_case_alerts.sql
CREATE TABLE case_alerts (
  id UUID PRIMARY KEY,
  tenant_id VARCHAR(255) NOT NULL,
  case_id UUID REFERENCES cases(id),
  alert_id VARCHAR(255) NOT NULL,
  linked_at TIMESTAMP DEFAULT NOW(),
  linked_by VARCHAR(255) NOT NULL
);
CREATE INDEX idx_case_alerts_tenant_case ON case_alerts(tenant_id, case_id);

-- Row-level security
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;
-- Policies to be added based on auth context
```

**2. Python Service** (`/services/case-service/`)

```
main.py (FastAPI)
case/
  api/routes.py
  db/repository.py
  db/models.py
  middleware/tenant.py
  schemas.py
config.py
requirements.txt
```

**3. API Endpoints**

- `POST /v1/cases` - Create case
- `GET /v1/cases` - List cases (tenant-filtered, paginated)
- `GET /v1/cases/{id}` - Get case details
- `PUT /v1/cases/{id}` - Update case
- `POST /v1/cases/{id}/alerts` - Link alert to case
- `GET /v1/cases/{id}/alerts` - Get case alerts

**4. Multi-Tenant Enforcement**

- Middleware extracts `X-Tenant-ID` and validates JWT
- All database queries include `WHERE tenant_id = $1`
- Cross-tenant access returns 404 (not 403 to avoid info leak)

**5. Alert Consumer** (async worker)

- Listen to OpenSearch alerts or alerts topic
- Auto-create case for alerts with severity >= 8
- Link alert to case automatically

**6. Testing**

- Unit tests for case CRUD
- Tests for tenant isolation (tenant A cannot see tenant B cases)
- Tests for alert linking
- Integration tests with Postgres
- Test coverage >70%

**7. Deployment**

- Dockerfile
- Helm chart with Postgres connection config
- SQL migration runner (init container or job)
- Resource limits

**Success Criteria**:

- ✅ Case created via API
- ✅ Alert linked to case
- ✅ Cross-tenant access properly denied
- ✅ Audit fields populated correctly
- ✅ OpenAPI spec generated

---

## Sub-Agent 5: Connector Agent

### Role

SOAR integration engineer

### Sprint Assignment

Sprint 5 (4-5 days)

### Mission Context

You are creating the extensibility framework that allows this platform to integrate with any external system. Focus on making it dead simple to add new connectors. The HPE ecosystem (Morpheus, OpsRamp) is the priority.

### Scope

- Connector framework and registry
- Morpheus connector (mocked)
- OpsRamp connector (mocked)
- Action execution interface

### Constraints

- **NO REAL API CALLS**: All connectors should be mocked for MVP
- **FOCUS ON EXTENSIBILITY**: Make it easy to add new connectors
- **SAFETY FIRST**: Validate inputs, handle errors, add retry logic

### Repository State

- Platform skeleton complete
- Case service operational
- Alerts and cases exist in the system

### Deliverables

**1. Connector Framework** (`/services/connector-service/`)

```
main.py (FastAPI)
connector/
  registry.py
  base.py (BaseConnector abstract class)
  executor.py (action execution worker)
  connectors/
    morpheus.py
    opsramp.py
    __init__.py
  schemas.py
config.py
requirements.txt
```

**2. Base Connector Interface**

```python
class BaseConnector(ABC):
    @abstractmethod
    def execute_action(self, action: str, params: dict) -> dict:
        """Execute connector action"""

    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        """Validate connector configuration"""

    @abstractmethod
    def health_check(self) -> bool:
        """Check connector health"""
```

**3. Morpheus Connector**
Actions:

- `workflow.execute(workflow_id, params)` → mocked response
- `instance.suspend(instance_id)` → mocked response
- `instance.snapshot(instance_id, snapshot_name)` → mocked response

Configuration schema:

```json
{
  "api_url": "https://morpheus.example.com/api",
  "api_token": "placeholder",
  "verify_ssl": true
}
```

**4. OpsRamp Connector**
Actions:

- `incident.create(title, description, severity)` → mocked response
- `incident.update(incident_id, status, notes)` → mocked response
- `alert.query(filters)` → mocked response

Configuration schema:

```json
{
  "api_url": "https://api.opsramp.com",
  "client_id": "placeholder",
  "client_secret": "placeholder"
}
```

**5. Connector Registry**

- Database or config file listing available connectors
- Connector configuration per tenant
- Enable/disable connectors per tenant

**6. API Endpoints**

- `POST /v1/connectors/{connector_name}/execute` - Execute action
- `GET /v1/connectors` - List available connectors
- `GET /v1/connectors/{connector_name}/schema` - Get action schema
- `POST /v1/connectors/{connector_name}/test` - Test connection

**7. Testing**

- Unit tests for framework
- Tests for Morpheus connector (all 3 actions)
- Tests for OpsRamp connector (all 3 actions)
- Test error handling and retries
- Test coverage >70%

**8. Documentation**

- `/docs/connectors/development_guide.md` - How to add a new connector
- `/docs/connectors/morpheus.md` - Morpheus connector documentation
- `/docs/connectors/opsramp.md` - OpsRamp connector documentation

**9. Deployment**

- Dockerfile
- Helm chart
- Resource limits

**Success Criteria**:

- ✅ Can execute Morpheus `workflow.execute` (mocked)
- ✅ Can create OpsRamp incident (mocked)
- ✅ Framework allows adding new connector in <1 hour
- ✅ Documentation complete and clear

---

## Shared Context Summary

### Multi-Tenancy Checklist (Every Agent)

- [ ] Extract `X-Tenant-ID` from request header
- [ ] Validate JWT `tenant_id` claim matches header
- [ ] Use tenant-scoped storage (topics, indices, table filters)
- [ ] Test cross-tenant access is denied

### Security Checklist (Every Agent)

- [ ] JWT authentication middleware implemented
- [ ] RBAC roles defined and enforced (where applicable)
- [ ] Structured JSON logging configured
- [ ] No secrets hardcoded (use K8s secrets)

### Deployment Checklist (Every Agent)

- [ ] Multi-stage Dockerfile (non-root user)
- [ ] Health endpoints: `/health` and `/ready`
- [ ] Helm chart with proper values
- [ ] Resource limits defined (CPU/memory)
- [ ] Environment-based configuration (12-factor)

### Testing Checklist (Every Agent)

- [ ] Unit tests written
- [ ] Integration tests (where applicable)
- [ ] Test coverage ≥70%
- [ ] All tests passing in CI

---

## Communication Protocol Between Agents

1. **Shared Schema**: All agents reference `/docs/schema/canonical_event.json`
2. **API Contracts**: OpenAPI specs in each service directory
3. **Event Topics**: Documented in `/docs/architecture/event_flow.md`
4. **Database Schema**: Migrations versioned and documented

Each agent should work independently but coordinate through:

- Shared documentation
- API contracts (OpenAPI)
- Event schemas (JSON Schema)
- Database migrations (versioned SQL)

---

This document ensures each sub-agent has clear responsibilities, constraints, and deliverables while maintaining a cohesive platform architecture.
