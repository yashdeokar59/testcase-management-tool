# Test Management Tool

A Flask-based web application for managing tests with user authentication, file uploads, and MySQL database integration.

**Two deployment options available:**
- 🐳 **Docker Compose** - For local development and testing
- ☸️ **Kubernetes** - For production deployment and scaling

## 🐳 Quick Start (Docker Compose)

### Prerequisites
- Docker and Docker Compose installed
- 4GB+ available RAM

### Deploy with Docker Compose
```bash
# Start the application
./start.sh

# Access at: http://localhost:5000

# Stop the application  
./stop.sh
```

### Docker Compose Management
```bash
# View logs
docker compose logs -f

# Check status
docker compose ps

# Restart services
docker compose restart

# Remove everything (including data)
docker compose down -v
```

## ☸️ Quick Start (Kubernetes)

### Prerequisites
- Kubernetes cluster (kubeadm, kind, or cloud provider)
- kubectl configured to access your cluster
- Docker for building images

### Deploy with Kubernetes
```bash
# Deploy everything with one command
./k8s/deploy.sh
```

### Access the Application
```bash
# Via Port Forward (recommended)
kubectl port-forward -n test-management svc/web-service 8080:80
# Then visit: http://localhost:8080

# Via NodePort (if supported)
http://localhost:30080

# Via Ingress (add to /etc/hosts first)
echo '127.0.0.1 test-management.local' | sudo tee -a /etc/hosts
http://test-management.local
```

### Kubernetes Management
```bash
# Monitor the deployment
./k8s/monitor.sh

# Test deployment
./k8s/test-deployment.sh

# Clean up
./k8s/cleanup.sh
```

## 📁 Project Structure

```
test-management-tool/
├── 📱 Application Files
│   ├── app.py                 # Main Flask application
│   ├── models.py             # Database models
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile           # Docker configuration
│   ├── entrypoint.sh        # Container startup script
│   ├── init_db.py          # Database initialization
│   ├── wait_for_db.py      # Database connection helper
│   └── templates/          # HTML templates
│
├── 🐳 Docker Compose Setup
│   ├── docker-compose.yml   # Docker Compose configuration
│   ├── start.sh            # Start Docker Compose
│   ├── stop.sh             # Stop Docker Compose
│   ├── .env                # Environment variables
│   ├── init.sql            # Database initialization
│   └── uploads/            # File uploads directory
│
└── ☸️ Kubernetes Setup
    └── k8s/               # Kubernetes manifests and scripts
        ├── deploy.sh           # One-command deployment
        ├── cleanup.sh          # Complete cleanup
        ├── monitor.sh          # Health monitoring
        ├── test-deployment.sh  # Deployment testing
        ├── namespace.yaml      # Namespace creation
        ├── configmap.yaml      # Application configuration
        ├── secret.yaml         # Database credentials
        ├── persistent-volume.yaml # Storage volumes
        ├── mysql-deployment.yaml  # MySQL database
        ├── mysql-service.yaml     # MySQL service
        ├── mysql-init-configmap.yaml # DB initialization
        ├── web-deployment.yaml    # Web application
        ├── web-service.yaml       # Web service
        ├── ingress.yaml          # External access
        ├── hpa.yaml             # Auto-scaling
        ├── network-policy.yaml  # Security policies
        ├── README.md           # Detailed documentation
        └── DEPLOYMENT_GUIDE.md # Step-by-step guide
```

## 🏗️ Architecture

### Docker Compose Architecture
```
┌─────────────────┐
│   Host Machine  │
│                 │
│  ┌───────────┐  │
│  │    Web    │  │ :5000
│  │ Container │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │  MySQL    │  │ :3306
│  │ Container │  │
│  └───────────┘  │
│                 │
│ Volume: mysql_data
│ Volume: ./uploads
└─────────────────┘
```

### Kubernetes Architecture
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

## 🌐 Application Features

- **User Authentication**: Login/logout functionality with session management
- **Test Management**: Create, edit, and organize test cases
- **Project Management**: Organize tests by projects and test suites
- **File Management**: Upload and manage test files
- **Bug Tracking**: Report and track bugs
- **Assignment System**: Assign tests to team members
- **Requirements Management**: Link tests to requirements
- **Dashboard**: Overview of test execution status

## 🔧 Configuration

### Docker Compose Configuration
- **Database**: MySQL 8.0 with persistent volume
- **Web App**: Flask with Gunicorn
- **Networking**: Bridge network for container communication
- **Volumes**: Persistent data and file uploads

### Kubernetes Configuration
- **Auto-scaling**: HPA for handling load (2-10 replicas)
- **High Availability**: Multiple replicas with health checks
- **Persistent Storage**: Database and uploads survive pod restarts
- **Resource Limits**: CPU and memory limits configured
- **Security**: Network policies and secrets management

## 🛠️ Development Commands

### Docker Compose Commands
```bash
# View application logs
docker compose logs -f web

# View database logs
docker compose logs -f db

# Access database directly
docker compose exec db mysql -u root -ppassword testmanagement

# Rebuild and restart
docker compose up -d --build

# Scale web service (Docker Swarm mode)
docker service scale testcase_web=3
```

### Kubernetes Commands
```bash
# View application logs
kubectl logs -f deployment/web-deployment -n test-management

# View database logs
kubectl logs -f deployment/mysql-deployment -n test-management

# Scale application
kubectl scale deployment web-deployment --replicas=5 -n test-management

# Update application
docker build -t testcase-managment-tool-web:v2.0 .
kind load docker-image testcase-managment-tool-web:v2.0 --name test-management-cluster
kubectl set image deployment/web-deployment web=testcase-managment-tool-web:v2.0 -n test-management

# Access database directly
kubectl exec -it deployment/mysql-deployment -n test-management -- mysql -u root -ppassword
```

## 📊 Monitoring

### Docker Compose Monitoring
```bash
# Check container status
docker compose ps

# Monitor resource usage
docker stats

# View container details
docker compose top
```

### Kubernetes Monitoring
```bash
# Check deployment status
kubectl get all -n test-management

# Monitor resource usage
kubectl top pods -n test-management

# View events
kubectl get events -n test-management --sort-by='.lastTimestamp'
```

## 🔒 Security Features

### Docker Compose Security
- Container isolation
- Environment variable management
- Volume permissions
- Network segmentation

### Kubernetes Security
- Network policies for micro-segmentation
- Secrets management for sensitive data
- RBAC and service accounts
- Resource limits to prevent resource exhaustion
- Health checks for automatic recovery

## 🚀 Deployment Comparison

| Feature | Docker Compose | Kubernetes |
|---------|----------------|------------|
| **Use Case** | Local development, testing | Production, scaling |
| **Setup Complexity** | Simple | Moderate |
| **Scalability** | Limited | Excellent |
| **High Availability** | No | Yes |
| **Auto-scaling** | No | Yes (HPA) |
| **Load Balancing** | Basic | Advanced |
| **Rolling Updates** | Manual | Automatic |
| **Resource Management** | Basic | Advanced |
| **Monitoring** | Basic | Advanced |
| **Multi-node** | No | Yes |

## 📞 Support

### Docker Compose Support
- Check `docker-compose.yml` for configuration
- Use `docker compose logs` for troubleshooting
- Ensure Docker and Docker Compose are updated

### Kubernetes Support
- Check `k8s/README.md` for comprehensive documentation
- Check `k8s/DEPLOYMENT_GUIDE.md` for step-by-step instructions
- Run `./k8s/monitor.sh` for health status
- Run `./k8s/test-deployment.sh` for deployment verification

## 🎉 Quick Verification

### Docker Compose Verification
```bash
# Start the application
./start.sh

# Check if running
curl -I http://localhost:5000

# View status
docker compose ps
```

### Kubernetes Verification
```bash
# Deploy and test
./k8s/deploy.sh
./k8s/test-deployment.sh

# Access the application
kubectl port-forward -n test-management svc/web-service 8080:80
# Visit: http://localhost:8080
```

## 🎯 Choosing the Right Deployment

### Use Docker Compose when:
- ✅ Local development and testing
- ✅ Simple single-machine deployment
- ✅ Quick prototyping
- ✅ Learning the application
- ✅ CI/CD testing environments

### Use Kubernetes when:
- ✅ Production deployment
- ✅ Need high availability
- ✅ Auto-scaling requirements
- ✅ Multi-node clusters
- ✅ Advanced monitoring and logging
- ✅ Rolling updates and rollbacks

**Status: ✅ Ready for both Docker Compose and Kubernetes deployment**
