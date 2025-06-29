#!/bin/bash

# Test Management Tool - Stop Script
echo "🛑 Stopping Test Management Tool..."
echo "================================="

# Navigate to project directory
cd "$(dirname "$0")"

# Stop the application
docker compose down

echo "✅ Application stopped successfully!"
echo "🚀 To start again, run: ./start.sh"
