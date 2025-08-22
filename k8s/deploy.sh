#!/bin/bash

# Test Management Tool Kubernetes Deployment Script
set -e

echo "🚀 Deploying Test Management Tool to Kubernetes..."
echo "=================================================="

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we can connect to cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
fi

echo "✅ Connected to Kubernetes cluster"

# Build Docker image if it doesn't exist
echo "🔧 Building Docker image..."
# cd .. # Already in correct directory
docker build -t testcase-managment-tool-web:latest .
echo "✅ Docker image built successfully"

# Apply Kubernetes manifests in order
echo "📦 Applying Kubernetes manifests..."

echo "  → Creating namespace..."
kubectl apply -f k8s/namespace.yaml

echo "  → Creating ConfigMaps..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/mysql-init-configmap.yaml

echo "  → Creating Secrets..."
kubectl apply -f k8s/secret.yaml

echo "  → Creating Persistent Volumes..."
kubectl apply -f k8s/persistent-volume.yaml

echo "  → Deploying MySQL..."
kubectl apply -f k8s/mysql-deployment.yaml
kubectl apply -f k8s/mysql-service.yaml

echo "  → Waiting for MySQL to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/mysql-deployment -n test-management

echo "  → Deploying Web Application..."
kubectl apply -f k8s/web-deployment.yaml
kubectl apply -f k8s/web-service.yaml

echo "  → Waiting for Web Application to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/web-deployment -n test-management

echo "  → Creating Ingress..."
kubectl apply -f k8s/ingress.yaml

echo "  → Creating HPA..."
kubectl apply -f k8s/hpa.yaml

echo "  → Applying Network Policy..."
kubectl apply -f k8s/network-policy.yaml

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📊 Deployment Status:"
echo "===================="
kubectl get all -n test-management

echo ""
echo "🌐 Access Information:"
echo "====================="
echo "NodePort: http://localhost:30080"
echo "Ingress: http://test-management.local (add to /etc/hosts)"
echo ""
echo "📝 Useful Commands:"
echo "=================="
echo "View pods:        kubectl get pods -n test-management"
echo "View services:    kubectl get svc -n test-management"
echo "View logs:        kubectl logs -f deployment/web-deployment -n test-management"
echo "Scale web app:    kubectl scale deployment web-deployment --replicas=3 -n test-management"
echo "Delete all:       kubectl delete namespace test-management"
echo ""
echo "🎉 Test Management Tool is now running on Kubernetes!"
