#!/usr/bin/env bash

set -e

CLUSTER_NAME="${CLUSTER_NAME:-siem-platform}"
KIND_IMAGE="${KIND_IMAGE:-kindest/node:v1.28.0}"

echo "Creating Kind cluster: $CLUSTER_NAME"

# Check if cluster already exists
if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
    echo "Cluster $CLUSTER_NAME already exists"
    exit 0
fi

# Create Kind cluster with custom configuration
cat <<EOF | kind create cluster --name "$CLUSTER_NAME" --image "$KIND_IMAGE" --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 30080
    hostPort: 8080
    protocol: TCP
  - containerPort: 30443
    hostPort: 8443
    protocol: TCP
- role: worker
- role: worker
EOF

echo "Waiting for cluster to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

echo "Installing NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

echo "Waiting for ingress controller to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s

echo "✅ Kind cluster $CLUSTER_NAME is ready!"
