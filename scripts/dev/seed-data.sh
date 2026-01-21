#!/usr/bin/env bash

set -e

NAMESPACE="${K8S_NAMESPACE:-siem-platform}"
API_URL="http://localhost:8080"

echo "🌱 Seeding test tenant and sample data..."

# Wait for API gateway to be ready
echo "Waiting for API gateway..."
kubectl wait --for=condition=Ready pod -l app=api-gateway -n $NAMESPACE --timeout=60s || true

# Port-forward API gateway in background
echo "Setting up port-forward to API gateway..."
kubectl port-forward -n $NAMESPACE svc/api-gateway 8080:80 > /dev/null 2>&1 &
PF_PID=$!
trap "kill $PF_PID 2>/dev/null || true" EXIT

sleep 3

# Create test tenant (using platform admin token - in real deployment this would be secure)
ADMIN_TOKEN="dev-admin-token-replace-in-production"

echo "Creating test tenant: acme-corp..."
TENANT_RESPONSE=$(curl -s -X POST "$API_URL/v1/tenants" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "acme-corp",
    "name": "ACME Corporation",
    "retention_days": 90,
    "data_residency": "us-east"
  }' || echo '{"error": "API not ready yet"}')

echo "Tenant created: $TENANT_RESPONSE"

# Generate tenant API token
TENANT_TOKEN="tenant-acme-corp-dev-token"

echo ""
echo "✅ Test data seeded successfully!"
echo ""
echo "════════════════════════════════════════════════════════"
echo "  Test Tenant Credentials"
echo "════════════════════════════════════════════════════════"
echo "  Tenant ID:    acme-corp"
echo "  API Token:    $TENANT_TOKEN"
echo "  API URL:      $API_URL"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Example: Ingest an event"
echo ""
echo "curl -X POST $API_URL/v1/ingest/events \\"
echo "  -H 'X-Tenant-ID: acme-corp' \\"
echo "  -H 'Authorization: Bearer $TENANT_TOKEN' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"category\": \"auth\","
echo "    \"severity\": 5,"
echo "    \"actor\": {\"id\": \"user123\", \"name\": \"John Doe\"},"
echo "    \"attributes\": {\"failed_login_count\": 1}"
echo "  }'"
echo ""
