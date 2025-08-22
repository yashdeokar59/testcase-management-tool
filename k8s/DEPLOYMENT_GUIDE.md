# 🚀 Test Management Tool - Kubernetes Deployment Guide

## 📋 Complete File Structure

```
k8s/
├── namespace.yaml              # Namespace creation
├── configmap.yaml             # App configuration
├── secret.yaml                # Database credentials
├── persistent-volume.yaml     # Storage volumes
├── mysql-init-configmap.yaml  # DB initialization
├── mysql-deployment.yaml      # MySQL database
├── mysql-service.yaml         # MySQL service
├── web-deployment.yaml        # Web application
├── web-service.yaml           # Web service
├── ingress.yaml               # External access
├── hpa.yaml                   # Auto-scaling
├── network-policy.yaml        # Security policies
├── deploy.sh                  # Deployment script
├── cleanup.sh                 # Cleanup script
├── monitor.sh                 # Monitoring script
├── README.md                  # Documentation
└── DEPLOYMENT_GUIDE.md        # This guide
```

## 🎯 Deployment Options

### Option 1: Quick Deploy (Recommended)
```bash
# One-command deployment
./k8s/deploy.sh
```

### Option 2: Step-by-Step Deploy
```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Create configuration
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/mysql-init-configmap.yaml
kubectl apply -f k8s/secret.yaml

# 3. Create storage
kubectl apply -f k8s/persistent-volume.yaml

# 4. Deploy database
kubectl apply -f k8s/mysql-deployment.yaml
kubectl apply -f k8s/mysql-service.yaml

# 5. Wait for database
kubectl wait --for=condition=available --timeout=300s deployment/mysql-deployment -n test-management

# 6. Deploy web application
kubectl apply -f k8s/web-deployment.yaml
kubectl apply -f k8s/web-service.yaml

# 7. Create external access
kubectl apply -f k8s/ingress.yaml

# 8. Enable auto-scaling
kubectl apply -f k8s/hpa.yaml

# 9. Apply security policies
kubectl apply -f k8s/network-policy.yaml
```

### Option 3: Helm Chart (Future Enhancement)
```bash
# TODO: Create Helm chart for easier management
helm install test-management ./helm-chart
```

## 🌐 Access Methods

### 1. NodePort Access (Immediate)
```bash
# Access via NodePort
http://localhost:30080
```

### 2. Ingress Access (Domain-based)
```bash
# Add to /etc/hosts
echo '127.0.0.1 test-management.local' | sudo tee -a /etc/hosts

# Access via domain
http://test-management.local
```

### 3. Port Forward (Development)
```bash
# Forward local port to service
kubectl port-forward svc/web-service 8080:80 -n test-management

# Access via localhost
http://localhost:8080
```

### 4. Load Balancer (Cloud)
```bash
# Change service type to LoadBalancer
kubectl patch svc web-service -n test-management -p '{"spec":{"type":"LoadBalancer"}}'

# Get external IP
kubectl get svc web-service -n test-management
```

## 📊 Monitoring Commands

### Basic Status
```bash
# Quick overview
kubectl get all -n test-management

# Detailed pod info
kubectl get pods -n test-management -o wide

# Service endpoints
kubectl get endpoints -n test-management
```

### Health Checks
```bash
# Run monitoring script
./k8s/monitor.sh

# Check pod health
kubectl describe pods -n test-management

# View recent events
kubectl get events -n test-management --sort-by='.lastTimestamp'
```

### Logs
```bash
# Web application logs
kubectl logs -f deployment/web-deployment -n test-management

# MySQL logs
kubectl logs -f deployment/mysql-deployment -n test-management

# All pods logs
kubectl logs -f -l app=test-management-tool -n test-management
```

## 🔧 Scaling Operations

### Manual Scaling
```bash
# Scale web application
kubectl scale deployment web-deployment --replicas=5 -n test-management

# Check HPA status
kubectl get hpa -n test-management

# View scaling events
kubectl describe hpa web-hpa -n test-management
```

### Auto-scaling Configuration
```yaml
# Current HPA settings
minReplicas: 2
maxReplicas: 10
CPU threshold: 70%
Memory threshold: 80%
```

## 🛠️ Maintenance Operations

### Update Application
```bash
# Build new image
docker build -t testcase-managment-tool-web:v2.0 .

# Update deployment
kubectl set image deployment/web-deployment web=testcase-managment-tool-web:v2.0 -n test-management

# Check rollout status
kubectl rollout status deployment/web-deployment -n test-management

# Rollback if needed
kubectl rollout undo deployment/web-deployment -n test-management
```

### Database Operations
```bash
# Connect to MySQL
kubectl exec -it deployment/mysql-deployment -n test-management -- mysql -u root -ppassword

# Backup database
kubectl exec deployment/mysql-deployment -n test-management -- mysqldump -u root -ppassword testmanagement > backup.sql

# Restore database
kubectl exec -i deployment/mysql-deployment -n test-management -- mysql -u root -ppassword testmanagement < backup.sql
```

### Storage Management
```bash
# Check storage usage
kubectl exec deployment/mysql-deployment -n test-management -- df -h /var/lib/mysql

# View PVC status
kubectl get pvc -n test-management

# Resize PVC (if supported)
kubectl patch pvc mysql-pvc -n test-management -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'
```

## 🔒 Security Best Practices

### Network Security
- Network policies restrict inter-pod communication
- Only necessary ports are exposed
- Database is not directly accessible from outside

### Secret Management
```bash
# Update database password
kubectl create secret generic test-management-secrets \
  --from-literal=mysql-root-password=newpassword \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pods to use new secrets
kubectl rollout restart deployment/mysql-deployment -n test-management
kubectl rollout restart deployment/web-deployment -n test-management
```

### RBAC (Role-Based Access Control)
```bash
# Create service account
kubectl create serviceaccount test-management-sa -n test-management

# Create role and binding
kubectl create role test-management-role --verb=get,list,watch --resource=pods,services -n test-management
kubectl create rolebinding test-management-binding --role=test-management-role --serviceaccount=test-management:test-management-sa -n test-management
```

## 🚨 Troubleshooting Guide

### Common Issues

#### 1. Pods Stuck in Pending
```bash
# Check node resources
kubectl describe nodes

# Check PVC status
kubectl get pvc -n test-management

# Check events
kubectl get events -n test-management
```

#### 2. ImagePullBackOff
```bash
# Check image name and tag
kubectl describe pod <pod-name> -n test-management

# Verify image exists
docker images | grep testcase-managment-tool-web
```

#### 3. CrashLoopBackOff
```bash
# Check application logs
kubectl logs <pod-name> -n test-management

# Check previous container logs
kubectl logs <pod-name> -n test-management --previous
```

#### 4. Database Connection Issues
```bash
# Test MySQL connectivity
kubectl exec deployment/web-deployment -n test-management -- nc -zv mysql-service 3306

# Check MySQL status
kubectl exec deployment/mysql-deployment -n test-management -- mysqladmin ping -h localhost -u root -ppassword
```

#### 5. Service Not Accessible
```bash
# Check service endpoints
kubectl get endpoints -n test-management

# Test service internally
kubectl exec deployment/web-deployment -n test-management -- curl -I http://web-service
```

### Performance Issues

#### High CPU Usage
```bash
# Check resource usage
kubectl top pods -n test-management

# Scale up if needed
kubectl scale deployment web-deployment --replicas=5 -n test-management
```

#### High Memory Usage
```bash
# Check memory limits
kubectl describe deployment web-deployment -n test-management

# Increase memory limits
kubectl patch deployment web-deployment -n test-management -p '{"spec":{"template":{"spec":{"containers":[{"name":"web","resources":{"limits":{"memory":"512Mi"}}}]}}}}'
```

#### Slow Database Queries
```bash
# Connect to MySQL and check slow queries
kubectl exec -it deployment/mysql-deployment -n test-management -- mysql -u root -ppassword -e "SHOW PROCESSLIST;"

# Check MySQL configuration
kubectl exec deployment/mysql-deployment -n test-management -- cat /etc/mysql/conf.d/my.cnf
```

## 📈 Production Readiness Checklist

### Before Production Deployment

- [ ] **Security**: Enable HTTPS with valid certificates
- [ ] **Monitoring**: Set up Prometheus/Grafana monitoring
- [ ] **Logging**: Configure centralized logging (ELK/EFK)
- [ ] **Backup**: Implement automated database backups
- [ ] **High Availability**: Use managed database service
- [ ] **Resource Limits**: Set appropriate CPU/memory limits
- [ ] **Health Checks**: Configure proper liveness/readiness probes
- [ ] **Secrets**: Use external secret management (Vault, etc.)
- [ ] **Network**: Implement proper network policies
- [ ] **Storage**: Use persistent storage with backups
- [ ] **Scaling**: Test auto-scaling under load
- [ ] **Disaster Recovery**: Plan and test recovery procedures

### Production Configuration Changes

1. **Use managed database** (RDS, Cloud SQL, etc.)
2. **Enable HTTPS** with Let's Encrypt or commercial certificates
3. **Set resource quotas** for the namespace
4. **Implement proper RBAC** with least privilege
5. **Use network policies** for micro-segmentation
6. **Enable audit logging** for compliance
7. **Set up monitoring** and alerting
8. **Implement backup strategies**

## 🎉 Success Verification

After deployment, verify everything is working:

```bash
# 1. Check all pods are running
kubectl get pods -n test-management

# 2. Test web application
curl -I http://localhost:30080/login

# 3. Test database connectivity
kubectl exec deployment/web-deployment -n test-management -- nc -zv mysql-service 3306

# 4. Check auto-scaling
kubectl get hpa -n test-management

# 5. Verify ingress
curl -H "Host: test-management.local" http://localhost/login

# 6. Run monitoring script
./k8s/monitor.sh
```

## 📞 Getting Help

If you encounter issues:

1. **Check logs**: Use `kubectl logs` to view application logs
2. **Describe resources**: Use `kubectl describe` for detailed information
3. **Check events**: Use `kubectl get events` for cluster events
4. **Run monitor script**: Use `./k8s/monitor.sh` for health overview
5. **Review documentation**: Check README.md for detailed information

## 🔄 Cleanup

To completely remove the deployment:

```bash
# Quick cleanup
./k8s/cleanup.sh

# Manual cleanup
kubectl delete namespace test-management
kubectl delete pv mysql-pv
docker rmi testcase-managment-tool-web:latest
```

---

**🎯 Your Test Management Tool is now ready for Kubernetes deployment!**
