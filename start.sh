#!/bin/bash

echo "🚀 Starting Test Management Tool with Docker Compose..."
echo "=================================================="

# Check if Docker and Docker Compose are available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed or not in PATH"
    exit 1
fi

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Start the services
echo "📦 Building and starting containers..."
if docker compose version &> /dev/null; then
    docker compose up -d --build
else
    docker-compose up -d --build
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Test Management Tool is now running!"
    echo ""
    echo "🌐 Access the application:"
    echo "   URL: http://localhost:5000"
    echo ""
    echo "📊 Check status:"
    echo "   docker compose ps"
    echo ""
    echo "📝 View logs:"
    echo "   docker compose logs -f"
    echo ""
    echo "🛑 Stop the application:"
    echo "   ./stop.sh"
else
    echo "❌ Failed to start the application"
    exit 1
fi
