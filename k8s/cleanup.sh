#!/bin/bash

# Test Management Tool Kubernetes Cleanup Script
set -e

echo "🧹 Cleaning up Test Management Tool from Kubernetes..."
echo "====================================================="

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace test-management &> /dev/null; then
    echo "ℹ️  Namespace 'test-management' does not exist"
    exit 0
fi

echo "🗑️  Deleting all resources in test-management namespace..."

# Delete namespace (this will delete all resources in it)
kubectl delete namespace test-management

echo "🗑️  Cleaning up persistent volumes..."
kubectl delete pv mysql-pv --ignore-not-found=true

echo "🧹 Cleaning up Docker images (optional)..."
read -p "Do you want to remove the Docker image? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker rmi testcase-managment-tool-web:latest --force || true
    echo "✅ Docker image removed"
else
    echo "ℹ️  Docker image kept"
fi

echo ""
echo "✅ Cleanup completed successfully!"
echo "🎉 All Test Management Tool resources have been removed from Kubernetes"
