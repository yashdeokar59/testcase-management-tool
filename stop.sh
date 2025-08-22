#!/bin/bash

echo "🛑 Stopping Test Management Tool..."
echo "================================="

# Stop and remove containers
if docker compose version &> /dev/null; then
    docker compose down
else
    docker-compose down
fi

if [ $? -eq 0 ]; then
    echo "✅ Test Management Tool stopped successfully!"
    echo ""
    echo "💾 Data is preserved in Docker volumes"
    echo "🗑️  To remove all data: docker compose down -v"
else
    echo "❌ Failed to stop the application"
    exit 1
fi
