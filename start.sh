#!/bin/bash

# Test Management Tool - Startup Script
echo "🚀 Starting Test Management Tool..."
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Navigate to project directory
cd "$(dirname "$0")"

# Start the application
echo "📦 Starting containers..."
docker compose up -d

# Wait a moment for containers to start
sleep 8

# Initialize database tables
echo "🔧 Initializing database..."
./init_tables.sh

# Check if containers are running
if docker ps | grep -q "test_management"; then
    echo "✅ Application started successfully!"
    echo ""
    echo "🌐 Access your application at: http://localhost:5000"
    echo "📊 Monitor with: docker stats"
    echo "📝 View logs with: docker logs test_management_web"
    echo "🛑 Stop with: ./stop.sh"
    echo ""
else
    echo "❌ Failed to start containers. Check logs with:"
    echo "   docker logs test_management_web"
    echo "   docker logs test_management_db"
fi
