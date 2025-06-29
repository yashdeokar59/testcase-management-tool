# Test Management Tool

A Flask-based web application for managing tests with user authentication, file uploads, and MySQL database integration.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed on your system
- Port 5000 and 3306 available on your machine

### Running the Server

1. **Navigate to the project directory:**
   ```bash
   cd /home/yash/test-management-tool
   ```

2. **Start the application (Recommended):**
   ```bash
   ./start.sh
   ```
   This script will:
   - Start the Docker containers
   - Automatically initialize database tables
   - Verify everything is working

3. **Alternative manual start:**
   ```bash
   docker compose up -d
   ./init_tables.sh  # Initialize database tables
   ```

4. **Access the application:**
   - Open your browser and go to: http://localhost:5000
   - The application will redirect you to the login page

5. **Stop the application:**
   ```bash
   ./stop.sh
   ```

**✅ The application now automatically handles database initialization, so no manual setup is required!**

## 📁 Project Structure

```
test-management-tool/
├── app.py                 # Main Flask application
├── models.py             # Database models
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration for web app
├── docker-compose.yml   # Docker Compose configuration
├── init.sql            # Database initialization
├── .env                # Environment variables
├── .dockerignore       # Docker ignore file
├── mysql-config/       # MySQL configuration files
├── templates/          # HTML templates
└── uploads/           # File upload directory
```

## 🔧 Development Commands

### View Application Logs
```bash
docker logs test_management_web
```

### View Database Logs
```bash
docker logs test_management_db
```

### Monitor Resource Usage
```bash
docker stats
```

### Access Database Directly
```bash
docker exec -it test_management_db mysql -u root -p
# Password: password
```

### Rebuild After Code Changes
```bash
docker compose down
docker compose build
docker compose up -d
```

## 🌐 Application Features

- **User Authentication**: Login/logout functionality
- **File Management**: Upload and manage test files
- **Database Integration**: MySQL 8.0 with optimized performance
- **Production Ready**: Uses Gunicorn WSGI server
- **Containerized**: Fully dockerized application

## 🔒 Default Configuration

- **Web Application**: http://localhost:5000
- **Database**: MySQL 8.0 on port 3306
- **Database Credentials**:
  - Root Password: `password`
  - Database: `testmanagement`
  - User: `testuser`
  - Password: `testpass`

## 🛠️ Troubleshooting

### Container Issues
```bash
# Check container status
docker ps

# View all containers (including stopped)
docker ps -a

# Restart containers
docker compose restart
```

### Database Connection Issues
```bash
# Check database health
docker exec test_management_db mysqladmin ping -h localhost -u root -ppassword
```

### Port Conflicts
If ports 5000 or 3306 are already in use, modify the ports in `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Change 5000 to 8080
```

## 📊 Performance Optimizations

The application includes several performance optimizations:
- Gunicorn WSGI server with multiple workers
- MySQL performance tuning
- Connection pooling
- Resource limits and health checks
- Optimized Docker images

## 🔄 Updates and Maintenance

### Update Application Code
1. Make your changes to the code
2. Rebuild and restart:
   ```bash
   docker compose down
   docker compose build
   docker compose up -d
   ```

### Backup Database
```bash
docker exec test_management_db mysqldump -u root -ppassword testmanagement > backup.sql
```

### Restore Database
```bash
docker exec -i test_management_db mysql -u root -ppassword testmanagement < backup.sql
```

## 📞 Support

If you encounter any issues:
1. Check the logs using the commands above
2. Ensure Docker and Docker Compose are properly installed
3. Verify that required ports are not in use by other applications
4. Make sure you have sufficient disk space and memory
