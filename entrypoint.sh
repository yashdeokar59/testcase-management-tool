#!/bin/bash

echo "Starting Test Management Tool..."

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! mysqladmin ping -h db -u root -ppassword --silent; do
    echo "Waiting for database connection..."
    sleep 2
done

echo "Database is ready!"

# Initialize database tables
echo "Initializing database tables..."
python init_db.py

echo "Starting application..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 2 --timeout 60 --keep-alive 2 --max-requests 1000 --preload app:app
