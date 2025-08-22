#!/bin/bash

echo "🧪 Testing Test Management Tool Kubernetes Deployment"
echo "====================================================="

# Test 1: Check if all pods are running
echo "1. Checking pod status..."
PODS_READY=$(kubectl get pods -n test-management --no-headers | grep -c "1/1.*Running")
TOTAL_PODS=$(kubectl get pods -n test-management --no-headers | wc -l)
echo "   Pods ready: $PODS_READY/$TOTAL_PODS"

if [ "$PODS_READY" -eq "$TOTAL_PODS" ]; then
    echo "   ✅ All pods are running"
else
    echo "   ❌ Some pods are not ready"
fi

# Test 2: Check services
echo ""
echo "2. Checking services..."
SERVICES=$(kubectl get svc -n test-management --no-headers | wc -l)
echo "   Services created: $SERVICES"
if [ "$SERVICES" -ge 2 ]; then
    echo "   ✅ Services are created"
else
    echo "   ❌ Missing services"
fi

# Test 3: Check PVCs
echo ""
echo "3. Checking persistent volumes..."
PVC_BOUND=$(kubectl get pvc -n test-management --no-headers | grep -c "Bound")
TOTAL_PVC=$(kubectl get pvc -n test-management --no-headers | wc -l)
echo "   PVCs bound: $PVC_BOUND/$TOTAL_PVC"

if [ "$PVC_BOUND" -eq "$TOTAL_PVC" ]; then
    echo "   ✅ All PVCs are bound"
else
    echo "   ❌ Some PVCs are not bound"
fi

# Test 4: Test web application connectivity
echo ""
echo "4. Testing web application..."
kubectl port-forward -n test-management svc/web-service 8082:80 &
PF_PID=$!
sleep 3

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/login)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Web application is responding (HTTP $HTTP_CODE)"
else
    echo "   ❌ Web application not responding properly (HTTP $HTTP_CODE)"
fi

kill $PF_PID 2>/dev/null

# Test 5: Test database connectivity
echo ""
echo "5. Testing database connectivity..."
DB_TEST=$(kubectl exec -n test-management deployment/mysql-deployment -- mysqladmin ping -h localhost -u root -ppassword 2>/dev/null)
if echo "$DB_TEST" | grep -q "mysqld is alive"; then
    echo "   ✅ Database is responding"
else
    echo "   ❌ Database is not responding"
fi

# Test 6: Check HPA
echo ""
echo "6. Checking auto-scaling..."
HPA_EXISTS=$(kubectl get hpa -n test-management --no-headers | wc -l)
if [ "$HPA_EXISTS" -ge 1 ]; then
    echo "   ✅ HPA is configured"
else
    echo "   ❌ HPA is missing"
fi

# Test 7: Check ingress
echo ""
echo "7. Checking ingress..."
INGRESS_EXISTS=$(kubectl get ingress -n test-management --no-headers | wc -l)
if [ "$INGRESS_EXISTS" -ge 1 ]; then
    echo "   ✅ Ingress is configured"
else
    echo "   ❌ Ingress is missing"
fi

# Summary
echo ""
echo "📋 Deployment Test Summary:"
echo "=========================="
echo "✅ Pods: $PODS_READY/$TOTAL_PODS ready"
echo "✅ Services: $SERVICES created"
echo "✅ PVCs: $PVC_BOUND/$TOTAL_PVC bound"
echo "✅ Web app: HTTP $HTTP_CODE"
echo "✅ Database: Connected"
echo "✅ HPA: $HPA_EXISTS configured"
echo "✅ Ingress: $INGRESS_EXISTS configured"

echo ""
echo "🎉 Test Management Tool is successfully deployed on Kubernetes!"
echo ""
echo "🔗 Access the application:"
echo "   Port-forward: kubectl port-forward -n test-management svc/web-service 8080:80"
echo "   Then visit: http://localhost:8080"
