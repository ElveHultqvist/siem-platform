# Assumptions

This document tracks assumptions made during the initial development of the multi-tenant SIEM + SOAR platform.

## Date: 2026-01-21

### Event Bus Selection

**Assumption**: NATS JetStream is chosen over Kafka for the MVP.

**Rationale**:

- Lightweight and cloud-native
- Lower operational overhead for Kubernetes deployments
- Sufficient for MVP throughput requirements (10K-100K events/sec)
- Easier to run locally for development
- JetStream provides persistence and replay capabilities

**Risk**: May need to migrate to Kafka if throughput exceeds 100K events/sec or if advanced Kafka ecosystem tools are required.

**Mitigation**: Event bus abstraction layer in `/libs/common` allows future migration.

---

### Language Choices

**Assumption**: Go for high-throughput services (ingest, tenant), Python for business logic (detection, case, connector).

**Rationale**:

- Go provides excellent performance for ingestion workloads
- Python FastAPI ecosystem is mature for CRUD APIs and ML/security analytics
- Team familiarity and hiring availability
- Rich libraries for security analytics in Python (pandas, sklearn, etc.)

**Risk**: Performance bottlenecks in Python services under high load.

**Mitigation**: Horizontal scaling with Kubernetes, async processing, option to rewrite critical paths in Go if needed.

---

### Multi-Tenancy Strategy

**Assumption**: Logical multi-tenancy using tenant_id filtering rather than physical database/cluster per tenant.

**Rationale**:

- Cost-effective for MVP and small-to-medium deployments
- Simpler operational model
- Sufficient isolation for most use cases with proper RBAC and row-level security

**Risk**: Noisy neighbor problems, regulatory requirements for data residency.

**Mitigation**:

- Tenant isolation testing in CI/CD
- Data residency flags in tenant configuration (prepared for physical separation later)
- Resource quotas per tenant in Kubernetes

---

### Authentication

**Assumption**: JWT tokens with OIDC readiness, no SAML in MVP.

**Rationale**:

- JWT is lightweight and stateless
- OIDC covers most modern authentication needs
- SAML adds complexity and is declining in adoption

**Risk**: Enterprise customers may require SAML.

**Mitigation**: OIDC can often bridge to SAML providers. SAML support can be added post-MVP if needed.

---

### Detection Engine

**Assumption**: In-memory state store for MVP, Redis interface prepared but not implemented.

**Rationale**:

- Simplifies initial development and deployment
- Acceptable for single-instance deployment
- Reduces infrastructure dependencies

**Risk**: State lost on pod restart, no horizontal scaling.

**Mitigation**:

- Design interface for Redis from day one
- Migration path documented
- Acceptable for MVP validation

---

### Storage Choices

**Assumption**: OpenSearch for events/alerts, PostgreSQL for control plane/cases.

**Rationale**:

- OpenSearch is open-source Elasticsearch fork (no licensing concerns)
- Excellent for log/event indexing and search
- PostgreSQL is battle-tested for relational data
- Both have mature Kubernetes operators

**Risk**: OpenSearch operational complexity, potential licensing changes.

**Mitigation**: Could migrate to Elasticsearch if licensing becomes favorable, or to ClickHouse for analytics.

---

### HPE Connector Priorities

**Assumption**: Morpheus and OpsRamp are the priority HPE integrations for MVP.

**Rationale**:

- Morpheus is HPE's cloud management platform
- OpsRamp is the AIOps/IT operations platform
- These cover infrastructure automation and incident management

**Risk**: Other HPE products (GreenLake, Aruba, Alletra) may be higher priority for some customers.

**Mitigation**: Extensible connector framework allows rapid addition of new integrations.

---

### Local Development Environment

**Assumption**: Kind (Kubernetes in Docker) is the default local K8s for development.

**Rationale**:

- Lightweight and fast startup
- Works on all platforms (Mac, Linux, Windows WSL)
- Official Kubernetes SIG project
- Easy to reset and recreate

**Alternative**: K3d (K3s in Docker) is also supported. Developers can choose based on preference.

---

### Secret Management

**Assumption**: Kubernetes Secrets for MVP, Vault/CyberArk interface prepared.

**Rationale**:

- Kubernetes Secrets are sufficient for local dev and non-production
- Avoids external dependency for MVP
- Interface design allows easy migration

**Risk**: Kubernetes Secrets are base64-encoded, not encrypted at rest by default.

**Mitigation**:

- Document encryption at rest configuration for production
- Vault integration guide post-MVP
- Never commit secrets to Git (enforced by .gitignore and CI checks)

---

### Walking Skeleton Rule

**Assumption**: Single detection rule (10 failed logins in 5 minutes) is sufficient for MVP validation.

**Rationale**:

- Demonstrates end-to-end flow
- Common use case (brute force detection)
- Simple to understand and test
- Validates state management, alerting, and case creation

**Risk**: Not representative of complex detection scenarios (correlation, ML models).

**Mitigation**: Rule engine architecture designed for extensibility. Additional rules can be added incrementally.

---

### RBAC Roles

**Assumption**: Four roles are sufficient: `platform_admin`, `tenant_admin`, `soc_analyst`, `auditor`.

**Rationale**:

- Covers common SIEM access patterns
- Simple enough for MVP
- Extensible for future roles

**Risk**: Customers may need fine-grained permissions.

**Mitigation**: Role-based permissions can be refined post-MVP. Consider adding attribute-based access control (ABAC) later.

---

### CI/CD Platform

**Assumption**: GitHub Actions for CI, GitOps with ArgoCD planned for CD.

**Rationale**:

- GitHub Actions is free for open-source
- Wide adoption and good integration
- ArgoCD is Kubernetes-native GitOps standard

**Alternative**: Could use GitLab CI, Jenkins, or other platforms based on customer preference.

---

### Data Retention

**Assumption**: Tenant-configurable retention policies, no automatic cold storage in MVP.

**Rationale**:

- Retention requirements vary widely by industry and regulation
- Cold storage (S3-compatible) adds complexity
- Can be added post-MVP

**Risk**: High storage costs for long retention.

**Mitigation**: Interface for cold storage prepared, Elasticsearch ILM/OpenSearch ISM configured.

---

### Schema Standards

**Assumption**: Custom canonical schema with translation stubs for ECS, OCSF, UDM.

**Rationale**:

- Flexibility to optimize for our use cases
- Can map to industry standards for interoperability
- No vendor lock-in

**Risk**: Not natively compatible with tools expecting ECS/OCSF.

**Mitigation**: Translation layer provides compatibility. May adopt OCSF fully in future.

---

### Testing Strategy

**Assumption**: 70% code coverage minimum, focus on unit tests, some integration tests.

**Rationale**:

- 70% is achievable without excessive effort
- Unit tests provide fast feedback
- Integration tests for critical paths

**Risk**: May miss issues caught only in end-to-end testing.

**Mitigation**: Manual walking skeleton testing, plan for E2E test suite post-MVP.

---

## Updating This Document

When making architectural decisions that involve assumptions, add them to this document with:

1. **Assumption**: What we're assuming
2. **Rationale**: Why we made this choice
3. **Risk**: What could go wrong
4. **Mitigation**: How we reduce the risk

This helps future developers understand the context and make informed changes.
