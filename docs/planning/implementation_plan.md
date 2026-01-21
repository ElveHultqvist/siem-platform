# Multi-Tenant SIEM + SOAR Platform - Implementation Plan

## Overview

Building an open-source, multi-tenant SIEM + SOAR platform for hybrid cloud and HPE ecosystem.

**Tech Stack**: Go (ingest), Python FastAPI (business logic), NATS JetStream, OpenSearch, PostgreSQL, Kubernetes

**Timeline**: 7-10 weeks across 10 sprints

---

## Sprint Organization & Sub-Agent Assignments

### Sprint 0: Project Foundation (1-2 days)

**Agent**: Platform Bootstrap Agent  
**Focus**: Create monorepo structure, documentation framework, Git setup

**Deliverables**:

- Directory structure: `/services`, `/libs/common`, `/deploy`, `/docs`, `/scripts`
- Initial `.gitignore`, `README.md`
- `/docs/assumptions.md`

---

### Sprint 1: Platform Skeleton (3-5 days)

**Agent**: Backend Platform Engineer  
**Mission**: Infrastructure foundation and deployment tooling

**Key Deliverables**:

- Helm charts for all 6 services + umbrella chart
- Kustomize overlays (dev/staging/prod)
- Makefile: `dev-up`, `dev-down`, `test`, `lint`, `fmt`, `seed`
- Local K8s bootstrap (Kind/K3d)
- GitHub Actions CI
- Architecture docs & canonical event schema

**Success Criteria**:

- ✅ `make dev-up` bootstraps all infrastructure
- ✅ All Helm charts install without errors

---

### Sprint 2: Ingest Service (3-4 days)

**Agent**: Go Backend Engineer  
**Mission**: High-performance event ingestion with tenant validation

**Scope**:

- HTTP endpoint: `POST /v1/ingest/events`
- Tenant validation (`X-Tenant-ID` header + JWT)
- Publish to NATS `raw.events.{tenant_id}`
- Structured logging, OpenTelemetry stubs

**Constraints**:

- No parsing or detection logic
- Kubernetes-ready container

**Deliverables**: Go service, Dockerfile, unit tests

---

### Sprint 3: Detection Engine (4-5 days)

**Agent**: Security Analytics Engineer (Python)  
**Mission**: Simple rule engine MVP

**Scope**:

- NATS consumer for `normalized.events.{tenant_id}`
- Rule: 10 failed logins in 5 min → alert
- In-memory state store (Redis interface for later)
- Emit alerts to OpenSearch `alerts-{tenant_id}`

**Constraints**: One rule only, no persistence

**Deliverables**: Python service, rule engine, tests

---

### Sprint 4: Case Management (4-5 days)

**Agent**: Incident Response Engineer  
**Mission**: Case tracking with multi-tenant enforcement

**Scope**:

- Postgres schema with `tenant_id` on all tables
- API: create case, link alerts, query cases
- Strong audit fields
- Multi-tenant middleware

**Constraints**: No UI, minimal API surface

**Deliverables**: Python service, SQL migrations, API, tests

---

### Sprint 5: Connector Service (4-5 days)

**Agent**: SOAR Integration Engineer  
**Mission**: Extensible connector framework for HPE ecosystem

**Scope**:

- Connector registry and execution framework
- **Morpheus connector**: `workflow.execute`, `instance.suspend`, `instance.snapshot` (mocked)
- **OpsRamp connector**: `incident.create`, `incident.update`, `alert.query` (mocked)

**Constraints**: No real API calls, focus on extensibility

**Deliverables**: Framework, 2 reference connectors, tests, development guide

---

### Sprint 6: Control Plane Services (5-6 days)

**Agent**: Platform Services Team

**Three Services**:

1. **API Gateway** (FastAPI)
   - JWT auth, OIDC ready
   - Tenant routing
   - RBAC: `platform_admin`, `tenant_admin`, `soc_analyst`, `auditor`
   - Rate limiting
   - OpenAPI docs

2. **Tenant Service** (Go/Python)
   - Tenant CRUD
   - Retention policies, data residency flags
   - Bootstrap scripts: `create-tenant`, `list-tenants`

3. **Content Service** (Python)
   - Rule/playbook versioning (stub)
   - Validation interface

---

### Sprint 7: Normalization Pipeline (3-4 days)

**Agent**: Data Pipeline Engineer

**Scope**:

- Normalize service (Python)
- NATS consumer: `raw.events.{tenant}` → `normalized.events.{tenant}`
- Canonical schema transformation
- Translation stubs: ECS, OCSF, UDM

**Canonical Schema**:

```json
{
  "tenant_id": "string",
  "event_id": "uuid",
  "timestamp": "iso8601",
  "source": { "system": "string", "integration": "string" },
  "category": "auth|endpoint|network|cloud|k8s|storage|ops",
  "severity": "0-10",
  "actor": { "type": "user|service", "id": "string" },
  "target": { "type": "asset|workload", "id": "string" },
  "attributes": {}
}
```

---

### Sprint 8: Storage Infrastructure (2-3 days)

**Agent**: Database/Infrastructure Engineer

**Scope**:

- **OpenSearch**: Deploy via Helm, index template `alerts-{tenant_id}`, ILM
- **PostgreSQL**: Deploy via Helm, migrations, connection pooling
- **NATS JetStream**: Topics setup, persistence config

---

### Sprint 9: Walking Skeleton Integration (3-4 days)

**Agent**: Integration Testing Team

**End-to-End Flow**:

1. POST event → ingest-service
2. Publish → `raw.events.{tenant}`
3. Normalize → `normalized.events.{tenant}`
4. Detect rule → alert to OpenSearch
5. Case-service → create case in Postgres

**Test Scenario**:

```bash
# Ingest 10 failed logins
curl -X POST http://localhost:8080/v1/ingest/events \
  -H "X-Tenant-ID: acme-corp" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"category": "auth", "actor": {"id": "user123"}, "attributes": {"failed_login_count": 1}}'

# Verify alert & case created
```

**Integration Tests**:

- Multi-tenant isolation
- RBAC enforcement
- Load test: 1000 events/sec

---

### Sprint 10: Documentation & Polish (2-3 days)

**Agent**: Documentation Team

**Deliverables**:

- Complete README (architecture, quickstart, APIs)
- Architecture diagrams
- ADRs (NATS vs Kafka, multi-tenancy strategy)
- Developer guides (add service, add connector, add rule)
- Code quality: linting, formatting, test coverage >70%
- Demo video/recording

---

## Shared Context for All Sub-Agents

### Multi-Tenancy (CRITICAL)

Every service MUST:

- Validate `X-Tenant-ID` header
- Match JWT `tenant_id` claim
- Use tenant-scoped storage: `alerts-{tenant_id}`, Postgres `WHERE tenant_id = ?`
- Enforce row/index-level isolation

### Security Requirements

- JWT authentication middleware
- RBAC enforcement
- Structured JSON logging
- No secrets in code (K8s secrets only)

### Coding Standards

- **Go**: gofmt, golangci-lint, zerolog/zap
- **Python**: black, flake8, mypy, FastAPI, pydantic
- **Tests**: pytest/testify, minimum 70% coverage
- **Docs**: OpenAPI specs for all APIs

### Deployment Standards

All services need:

- Multi-stage Dockerfile (non-root user)
- Helm chart with values.yaml
- Health endpoints: `/health`, `/ready`
- Resource limits
- 12-factor config

---

## Timeline & Dependencies

| Sprint    | Duration | Depends On  |
| --------- | -------- | ----------- |
| Sprint 0  | 1-2 days | -           |
| Sprint 1  | 3-5 days | Sprint 0    |
| Sprint 2  | 3-4 days | Sprint 1    |
| Sprint 3  | 4-5 days | Sprint 2, 7 |
| Sprint 4  | 4-5 days | Sprint 3    |
| Sprint 5  | 4-5 days | Sprint 1    |
| Sprint 6  | 5-6 days | Sprint 1    |
| Sprint 7  | 3-4 days | Sprint 2    |
| Sprint 8  | 2-3 days | Sprint 1    |
| Sprint 9  | 3-4 days | All         |
| Sprint 10 | 2-3 days | Sprint 9    |

**Total**: 34-48 days (7-10 weeks)

---

## Success Metrics

### Technical

- ✅ All services running in K8s
- ✅ Walking skeleton <5 sec end-to-end
- ✅ Ingest: ≥1000 events/sec
- ✅ Test coverage ≥70%
- ✅ Zero hardcoded secrets

### Documentation

- ✅ New dev bootstraps in <30 min
- ✅ All APIs have OpenAPI specs
- ✅ Architecture diagrams complete

### Functional

- ✅ Event → case creation works
- ✅ Multi-tenant isolation verified
- ✅ RBAC enforcement verified

---

## Risk Mitigation

> [!WARNING]
> **Critical Path**: Sprint 1 must complete before parallel work begins. NATS/OpenSearch/Postgres (Sprint 8) blocks Walking Skeleton.

> [!CAUTION]
> **Resource Requirements**: 16GB RAM minimum for local K8s cluster

---

## Repository Structure

```
/services
  /api-gateway (Python FastAPI)
  /ingest-service (Go)
  /normalize-service (Python)
  /detect-service (Python)
  /case-service (Python)
  /connector-service (Python)
  /tenant-service (Go/Python)
  /content-service (Python)
/libs
  /common (shared types, auth, validators)
/deploy
  /helm (charts per service + umbrella)
  /kustomize (dev/staging/prod overlays)
/docs
  /schema (canonical_event.json)
  /architecture (diagrams, ADRs)
/scripts
  /bootstrap (local dev setup)
```

---

## Next Steps

1. Review and approve this plan
2. Assign sub-agents to tasks
3. Begin Sprint 0: Create repository structure
4. Proceed with sequential sprint execution

Ready to begin implementation!
