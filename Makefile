.PHONY: help dev-up dev-down test lint fmt seed build deploy-dev clean

# Variables
CLUSTER_NAME ?= siem-platform
K8S_NAMESPACE ?= siem-platform
HELM_RELEASE ?= siem-platform
KIND_IMAGE ?= kindest/node:v1.28.0

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev-up: ## Start local Kubernetes cluster with all services
	@echo "🚀 Starting local Kubernetes cluster..."
	@./scripts/bootstrap/kind-up.sh
	@echo "📦 Deploying SIEM platform..."
	@kubectl create namespace $(K8S_NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	@helm dependency update deploy/helm/siem-platform
	@helm upgrade --install $(HELM_RELEASE) deploy/helm/siem-platform \
		--namespace $(K8S_NAMESPACE) \
		--create-namespace \
		--wait \
		--timeout 10m
	@echo "✅ SIEM platform is ready!"
	@echo ""
	@echo "Access the API gateway:"
	@echo "  kubectl port-forward -n $(K8S_NAMESPACE) svc/api-gateway 8080:80"
	@echo ""
	@echo "Run 'make seed' to create test tenant and data"

dev-down: ## Tear down local cluster
	@echo "🛑 Tearing down local Kubernetes cluster..."
	@kind delete cluster --name $(CLUSTER_NAME) || true
	@echo "✅ Cluster deleted"

test: ## Run all tests
	@echo "🧪 Running tests..."
	@echo "Testing Go services..."
	@for dir in services/*/; do \
		if [ -f "$$dir/go.mod" ]; then \
			echo "  Testing $$dir..."; \
			(cd $$dir && go test -v -race -coverprofile=coverage.out ./... || exit 1); \
		fi \
	done
	@echo "Testing Python services..."
	@for dir in services/*/; do \
		if [ -f "$$dir/requirements.txt" ]; then \
			echo "  Testing $$dir..."; \
			(cd $$dir && python -m pytest tests/ -v --cov=. --cov-report=term-missing || exit 1); \
		fi \
	done
	@echo "✅ All tests passed!"

lint: ## Run linters
	@echo "🔍 Running linters..."
	@echo "Linting Go code..."
	@for dir in services/*/; do \
		if [ -f "$$dir/go.mod" ]; then \
			echo "  Linting $$dir..."; \
			(cd $$dir && golangci-lint run ./... || exit 1); \
		fi \
	done
	@echo "Linting Python code..."
	@for dir in services/*/; do \
		if [ -f "$$dir/requirements.txt" ]; then \
			echo "  Linting $$dir..."; \
			(cd $$dir && flake8 . && mypy . || exit 1); \
		fi \
	done
	@echo "✅ All linters passed!"

fmt: ## Format all code
	@echo "✨ Formatting code..."
	@echo "Formatting Go code..."
	@for dir in services/*/; do \
		if [ -f "$$dir/go.mod" ]; then \
			echo "  Formatting $$dir..."; \
			(cd $$dir && gofmt -w . && go mod tidy); \
		fi \
	done
	@echo "Formatting Python code..."
	@for dir in services/*/; do \
		if [ -f "$$dir/requirements.txt" ]; then \
			echo "  Formatting $$dir..."; \
			(cd $$dir && black . && isort .); \
		fi \
	done
	@echo "✅ Code formatted!"

seed: ## Create test tenant and sample data
	@echo "🌱 Seeding test data..."
	@./scripts/dev/seed-data.sh
	@echo "✅ Test data created!"

build: ## Build all Docker images
	@echo "🔨 Building Docker images..."
	@for dir in services/*/; do \
		service=$$(basename $$dir); \
		if [ -f "$$dir/Dockerfile" ]; then \
			echo "  Building $$service..."; \
			docker build -t siem-platform/$$service:latest $$dir; \
		fi \
	done
	@echo "✅ All images built!"

deploy-dev: build ## Deploy to dev environment
	@echo "🚀 Deploying to dev environment..."
	@kubectl apply -k deploy/kustomize/dev
	@echo "✅ Deployed to dev!"

clean: ## Clean build artifacts
	@echo "🧹 Cleaning..."
	@find . -type f -name '*.pyc' -delete
	@find . -type d -name '__pycache__' -delete
	@find . -type d -name '.pytest_cache' -delete
	@find . -type f -name 'coverage.out' -delete
	@find . -type d -name 'dist' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name 'build' -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned!"

# Development shortcuts
logs: ## Tail logs from all pods
	@kubectl logs -n $(K8S_NAMESPACE) -l app.kubernetes.io/instance=$(HELM_RELEASE) --tail=100 -f

pods: ## List all pods
	@kubectl get pods -n $(K8S_NAMESPACE)

shell-api: ## Open shell in API gateway pod
	@kubectl exec -it -n $(K8S_NAMESPACE) $$(kubectl get pod -n $(K8S_NAMESPACE) -l app=api-gateway -o jsonpath='{.items[0].metadata.name}') -- /bin/sh

shell-ingest: ## Open shell in ingest service pod
	@kubectl exec -it -n $(K8S_NAMESPACE) $$(kubectl get pod -n $(K8S_NAMESPACE) -l app=ingest-service -o jsonpath='{.items[0].metadata.name}') -- /bin/sh
