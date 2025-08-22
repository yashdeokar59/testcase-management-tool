# Test Management Tool - Kubernetes Deployment

This directory contains Kubernetes manifests and scripts to deploy the Test Management Tool on a Kubernetes cluster.

## 📁 Files Overview

### Core Manifests
- `namespace.yaml` - Creates the test-management namespace
- `configmap.yaml` - Application configuration and MySQL settings
- `secret.yaml` - Database credentials and connection strings
- `persistent-volume.yaml` - Storage for MySQL data and file uploads

### Database Components
- `mysql-deployment.yaml` - MySQL 8.0 deployment
- `mysql-service.yaml` - MySQL service for internal communication
- `mysql-init-configmap.yaml` - Database initialization scripts

### Web Application Components
- `web-deployment.yaml` - Flask web application deployment
- `web-service.yaml` - Web service with NodePort access
- `ingress.yaml` - Ingress for external access
- `hpa.yaml` - Horizontal Pod Autoscaler for scaling

### Security & Networking
- `network-policy.yaml` - Network policies for security

### Scripts
- `deploy.sh` - Complete deployment script
- `cleanup.sh` - Clean removal of all resources
- `monitor.sh` - Monitoring and health check script

## 🚀 Quick Start

### Prerequisites
- Kubernetes cluster (minikube, kind, or cloud provider)
- kubectl configured to access your cluster
- Docker for building images

### Deploy the Application
```bash
# Make scripts executable
chmod +x k8s/*.sh

# Deploy everything
./k8s/deploy.sh
```

### Access the Application
```bash
# Via NodePort (immediate access)
http://localhost:30080

# Via Ingress (requires host entry)
echo '127.0.0.1 test-management.local' | sudo tee -a /etc/hosts
http://test-management.local
```

### Monitor the Deployment
```bash
./k8s/monitor.sh
```

### Clean Up
```bash
./k8s/cleanup.sh
```

## 📊 Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Ingress       │    │   NodePort      │
│ (Port 80/443)   │    │   (Port 30080)  │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
          ┌─────────────────┐
          │  Web Service    │
          │   (Port 80)     │
          └─────────┬───────┘
                    │
          ┌─────────────────┐
          │ Web Deployment  │
          │  (2-10 pods)    │
          │   Flask App     │
          └─────────┬───────┘
                    │
          ┌─────────────────┐
          │ MySQL Service   │
          │   (Port 3306)   │
          └─────────┬───────┘
                    │
          ┌─────────────────┐
          │MySQL Deployment │
          │    (1 pod)      │
          │  + Persistent   │
          │    Storage      │
          └─────────────────┘
```

## 🔧 Configuration

### Environment Variables
Set in `configmap.yaml`:
- `FLASK_ENV`: production
- `SESSION_TIMEOUT_MINUTES`: 30
- `UPLOAD_FOLDER`: /app/uploads

### Database Credentials
Set in `secret.yaml` (base64 encoded):
- Root password: `password`
- Database: `testmanagement`
- User: `testuser`
- Password: `testpass`

### Resource Limits
- **Web pods**: 128Mi-256Mi RAM, 100m-200m CPU
- **MySQL pod**: 256Mi-512Mi RAM, 250m-500m CPU

### Scaling
- **Min replicas**: 2
- **Max replicas**: 10
- **CPU threshold**: 70%
- **Memory threshold**: 80%

## 🛠️ Customization

### Change Resource Limits
Edit `web-deployment.yaml` and `mysql-deployment.yaml`:
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "200m"
  limits:
    memory: "512Mi"
    cpu: "400m"
```

### Change Database Credentials
1. Update `secret.yaml` with base64 encoded values:
```bash
echo -n "newpassword" | base64
```
2. Redeploy the secret:
```bash
kubectl apply -f k8s/secret.yaml
```

### Enable HTTPS
1. Uncomment TLS section in `ingress.yaml`
2. Create TLS certificate:
```bash
kubectl create secret tls test-management-tls \
  --cert=path/to/cert.crt \
  --key=path/to/cert.key \
  -n test-management
```

### Use Cloud Storage
Replace `hostPath` in `persistent-volume.yaml` with cloud provider storage class:
```yaml
spec:
  storageClassName: gp2  # AWS EBS
  # or
  storageClassName: standard  # GCP Persistent Disk
```

## 📋 Troubleshooting

### Check Pod Status
```bash
kubectl get pods -n test-management
kubectl describe pod <pod-name> -n test-management
```

### View Logs
```bash
# Web application logs
kubectl logs -f deployment/web-deployment -n test-management

# MySQL logs
kubectl logs -f deployment/mysql-deployment -n test-management
```

### Test Database Connection
```bash
# Connect to MySQL pod
kubectl exec -it deployment/mysql-deployment -n test-management -- mysql -u root -ppassword

# Test from web pod
kubectl exec -it deployment/web-deployment -n test-management -- nc -zv mysql-service 3306
```

### Common Issues

1. **Pods stuck in Pending**: Check PV/PVC status and node resources
2. **ImagePullBackOff**: Ensure Docker image is built and available
3. **CrashLoopBackOff**: Check application logs for errors
4. **Service not accessible**: Verify service and ingress configuration

### Performance Tuning

1. **Increase MySQL buffer pool**:
   Edit `mysql-config` in `configmap.yaml`

2. **Adjust web app workers**:
   Modify Gunicorn configuration in Dockerfile

3. **Scale manually**:
   ```bash
   kubectl scale deployment web-deployment --replicas=5 -n test-management
   ```

## 🔒 Security Considerations

- Network policies restrict pod-to-pod communication
- Secrets are used for sensitive data
- Non-root containers where possible
- Resource limits prevent resource exhaustion
- Health checks ensure service availability

## 📈 Monitoring

Use the monitoring script for regular health checks:
```bash
./k8s/monitor.sh
```

For production, consider integrating with:
- Prometheus + Grafana for metrics
- ELK stack for log aggregation
- Jaeger for distributed tracing

## 🚀 Production Deployment

For production environments:

1. **Use managed databases** (RDS, Cloud SQL)
2. **Implement proper backup strategies**
3. **Set up monitoring and alerting**
4. **Use HTTPS with valid certificates**
5. **Implement proper RBAC**
6. **Use network policies**
7. **Regular security updates**

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review Kubernetes and application logs
3. Verify cluster resources and connectivity
