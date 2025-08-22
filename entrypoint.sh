#!/bin/bash

echo "Starting Test Management Tool..."

# Wait for database to be ready using Python script
echo "Waiting for database to be ready..."
python wait_for_db.py

if [ $? -ne 0 ]; then
    echo "❌ Failed to connect to database. Exiting..."
    exit 1
fi

echo "Database is ready!"

# Initialize database tables
echo "Initializing database tables..."
python init_db.py

echo "Starting application..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 2 --timeout 60 --keep-alive 2 --max-requests 1000 --preload app:app
