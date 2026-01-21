# Multi-Tenant SIEM + SOAR Platform - Task Breakdown

## Sprint 0: Project Foundation

- [x] Create monorepo directory structure
- [x] Initialize Git repository with .gitignore
- [x] Create shared libraries structure (/libs/common)
- [x] Set up documentation framework (/docs)
- [x] Create assumptions.md document

## Sprint 1: Platform Skeleton (Task 1)

### Repository Structure

- [x] Create service directories (api-gateway, ingest-service, normalize-service, detect-service, case-service, connector-service)
- [x] Create deployment directories (Helm charts, Kustomize overlays)
- [x] Create scripts directory for bootstrap and dev tooling

### Infrastructure & DevOps

- [x] Create Helm charts for each service
- [x] Create umbrella Helm chart
- [x] Create Kustomize overlays (dev, staging, prod)
- [x] Implement Makefile with targets: dev-up, dev-down, test, lint, fmt, seed
- [x] Create local Kubernetes bootstrap scripts (Kind/K3d)
- [x] Set up GitHub Actions CI workflow for linting and tests

### Documentation

- [x] Write architecture overview
- [x] Document local development setup
- [x] Create canonical event schema (JSON Schema)
- [x] Document tenant bootstrap process
- [x] Create connector development guide

## Sprint 2: Ingest Service (Task 2 - Go)

### Core Implementation

- [x] Initialize Go module and project structure
- [x] Implement HTTP ingestion endpoint (/v1/ingest/events)
- [x] Add tenant validation middleware
- [x] Implement JWT authentication middleware
- [x] Add tenant context extraction from headers
- [x] Implement NATS JetStream publisher
- [x] Add structured JSON logging
- [x] Create OpenTelemetry tracing stubs

### Testing & Deployment

- [x] Write unit tests for tenant validation
- [x] Write unit tests for event publishing
- [x] Create Dockerfile for ingest-service
- [x] Create Helm chart values
- [x] Test in local Kubernetes cluster

## Sprint 3: Detection Engine (Task 3 - Python)

### Core Implementation

- [x] Initialize Python project with FastAPI
- [x] Implement NATS consumer for normalized events
- [x] Create in-memory state store for rule engine
- [x] Implement simple failed login detection rule (10 failures in 5 minutes)
- [x] Add alert emission to OpenSearch
- [x] Implement tenant-aware indexing (alerts-{tenant_id})
- [x] Add structured logging

### Testing & Deployment

- [x] Write unit tests for rule engine logic
- [x] Write tests for state management
- [x] Create Dockerfile for detect-service
- [x] Create Helm chart values
- [x] Test detection flow end-to-end

## Sprint 4: Case Management (Task 4)

### Database & Schema

- [x] Design Postgres schema with tenant_id on all tables
- [x] Create SQL migrations for case tables
- [x] Implement row-level tenant isolation
- [x] Add audit fields (created_at, updated_at, created_by)

### API Implementation

- [x] Initialize Python/FastAPI service
- [x] Implement case creation endpoint
- [x] Implement alert-to-case linking
- [x] Add multi-tenant enforcement middleware
- [x] Create case query endpoints
- [x] Add OpenAPI specification

### Testing & Deployment

- [x] Write unit tests for case creation
- [x] Write tests for tenant isolation
- [x] Create Dockerfile for case-service
- [x] Create Helm chart values
- [x] Test case creation from alerts

## Sprint 5: Connector Service (Task 5)

### Framework Implementation

- [ ] Initialize Python/FastAPI service
- [ ] Design connector registry interface
- [ ] Implement connector execution worker pattern
- [ ] Add connector configuration management
- [ ] Implement action interface design

### Reference Connectors

- [ ] Create Morpheus connector stub (workflow.execute, instance.suspend, instance.snapshot)
- [ ] Create OpsRamp connector stub (incident.create, incident.update, alert.query)
- [ ] Implement mocked HTTP calls for both connectors
- [ ] Add configuration placeholders

### Testing & Deployment

- [ ] Write tests for connector framework
- [ ] Write tests for Morpheus connector
- [ ] Write tests for OpsRamp connector
- [ ] Create Dockerfile for connector-service
- [ ] Create Helm chart values

## Sprint 6: Control Plane Services

### API Gateway

- [ ] Initialize Python/FastAPI service
- [ ] Implement JWT authentication
- [ ] Add tenant routing middleware
- [ ] Implement RBAC enforcement (platform_admin, tenant_admin, soc_analyst, auditor)
- [ ] Add rate limiting middleware
- [ ] Generate OpenAPI documentation

### Tenant Service

- [ ] Initialize service (Go or Python)
- [ ] Implement tenant CRUD operations
- [ ] Add retention policy management
- [ ] Add data residency flags
- [ ] Create tenant bootstrap scripts
- [ ] Implement API key rotation stubs

### Content Service

- [ ] Initialize Python service
- [ ] Implement rule/playbook versioning stub
- [ ] Add validation interface
- [ ] Create content management API

## Sprint 7: Normalization & Data Pipeline

### Normalize Service

- [ ] Initialize Python service
- [ ] Implement NATS consumer for raw events
- [ ] Create canonical schema validator
- [ ] Add normalization logic
- [ ] Implement enrichment (minimal fields)
- [ ] Add NATS publisher for normalized events
- [ ] Create ECS/OCSF/UDM translation stubs

### Event Bus Setup

- [ ] Deploy NATS JetStream to Kubernetes
- [ ] Configure topics (raw.events.{tenant}, normalized.events.{tenant})
- [ ] Set up stream persistence
- [ ] Document topic naming conventions

## Sprint 8: Storage Infrastructure

### OpenSearch Setup

- [ ] Deploy OpenSearch to Kubernetes
- [ ] Create index templates for alerts-{tenant_id}
- [ ] Configure tenant-aware indexing
- [ ] Set up retention policies
- [ ] Create index lifecycle management

### PostgreSQL Setup

- [ ] Deploy PostgreSQL to Kubernetes
- [ ] Run initial migrations
- [ ] Configure connection pooling
- [ ] Set up backup strategy
- [ ] Create multi-tenant test data

## Sprint 9: Walking Skeleton Integration

### End-to-End Flow

- [ ] Deploy all services to local Kubernetes
- [ ] Create test tenant
- [ ] Test event ingestion via curl
- [ ] Verify event normalization
- [ ] Verify detection rule triggers
- [ ] Verify alert creation in OpenSearch
- [ ] Verify case creation in Postgres
- [ ] Document the complete flow

### Integration Testing

- [ ] Write integration tests for walking skeleton
- [ ] Test multi-tenant isolation
- [ ] Test RBAC enforcement
- [ ] Load test ingest endpoint
- [ ] Verify logging across all services

## Sprint 10: Documentation & Polish

### Documentation

- [ ] Complete README with quickstart
- [ ] Document API endpoints for each service
- [ ] Create architecture diagrams
- [ ] Write ADRs for key decisions (NATS vs Kafka, etc.)
- [ ] Document connector development process
- [ ] Create troubleshooting guide

### Code Quality

- [ ] Run linters on all services
- [ ] Format all code (gofmt, black)
- [ ] Add pre-commit hooks
- [ ] Review and improve test coverage
- [ ] Add code documentation

### Deliverables Verification

- [ ] Verify all Dockerfiles build successfully
- [ ] Verify all Helm charts install
- [ ] Verify Makefile targets work
- [ ] Test bootstrap scripts on clean environment
- [ ] Create demo video/walkthrough
