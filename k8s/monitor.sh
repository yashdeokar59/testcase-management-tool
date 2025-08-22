#!/bin/bash

# Test Management Tool Kubernetes Monitoring Script

echo "📊 Test Management Tool - Kubernetes Status"
echo "==========================================="

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace test-management &> /dev/null; then
    echo "❌ Namespace 'test-management' does not exist"
    echo "Run './deploy.sh' to deploy the application first"
    exit 1
fi

echo ""
echo "🏷️  Namespace Status:"
kubectl get namespace test-management

echo ""
echo "🚀 Deployments:"
kubectl get deployments -n test-management

echo ""
echo "📦 Pods:"
kubectl get pods -n test-management -o wide

echo ""
echo "🌐 Services:"
kubectl get services -n test-management

echo ""
echo "💾 Persistent Volume Claims:"
kubectl get pvc -n test-management

echo ""
echo "🔄 HPA Status:"
kubectl get hpa -n test-management

echo ""
echo "🌍 Ingress:"
kubectl get ingress -n test-management

echo ""
echo "📈 Resource Usage:"
echo "=================="
kubectl top pods -n test-management 2>/dev/null || echo "Metrics server not available"

echo ""
echo "🔍 Recent Events:"
echo "================"
kubectl get events -n test-management --sort-by='.lastTimestamp' | tail -10

echo ""
echo "🏥 Health Checks:"
echo "================"

# Check if web service is responding
WEB_POD=$(kubectl get pods -n test-management -l component=web -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ ! -z "$WEB_POD" ]; then
    echo "Testing web application health..."
    kubectl exec -n test-management $WEB_POD -- curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/login && echo " ✅ Web app is healthy" || echo " ❌ Web app is not responding"
else
    echo "❌ No web pods found"
fi

# Check MySQL connectivity
MYSQL_POD=$(kubectl get pods -n test-management -l component=database -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ ! -z "$MYSQL_POD" ]; then
    echo "Testing MySQL connectivity..."
    kubectl exec -n test-management $MYSQL_POD -- mysqladmin ping -h localhost -u root -ppassword &>/dev/null && echo " ✅ MySQL is healthy" || echo " ❌ MySQL is not responding"
else
    echo "❌ No MySQL pods found"
fi

echo ""
echo "🔗 Access URLs:"
echo "=============="
NODE_PORT=$(kubectl get svc web-service -n test-management -o jsonpath='{.spec.ports[0].nodePort}')
echo "NodePort: http://localhost:$NODE_PORT"
echo "Ingress: http://test-management.local"
echo ""
echo "Add to /etc/hosts: echo '127.0.0.1 test-management.local' | sudo tee -a /etc/hosts"
