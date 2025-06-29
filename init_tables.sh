#!/bin/bash

# Initialize database tables if they don't exist
echo "🔧 Checking database tables..."

# Check if user table exists
if docker exec test_management_db mysql -u root -ppassword -e "USE testmanagement; DESCRIBE user;" 2>/dev/null >/dev/null; then
    echo "✅ Database tables already exist"
else
    echo "📦 Creating database tables..."
    docker exec test_management_web python -c "
from app import app, db
from models import *
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
"
    echo "✅ Database tables created"
fi
