#!/usr/bin/env python3
"""
Database initialization script for Test Management Tool
"""

from app import app, db

def init_database():
    """Initialize database tables"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            return True
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False

if __name__ == '__main__':
    init_database()
