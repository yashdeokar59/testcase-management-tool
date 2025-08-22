#!/usr/bin/env python3
"""
Wait for database to be ready
"""
import time
import sys
import pymysql
import os

def wait_for_database():
    """Wait for database to be ready"""
    max_retries = 30
    retry_count = 0
    
    # Try to get database host from environment or use defaults
    # For Docker Compose: 'db'
    # For Kubernetes: 'mysql-service'
    db_host = os.environ.get('DB_HOST', 'mysql-service')
    
    # If we're in Docker Compose environment, use 'db'
    if os.path.exists('/.dockerenv') and 'KUBERNETES_SERVICE_HOST' not in os.environ:
        db_host = 'db'
    
    while retry_count < max_retries:
        try:
            connection = pymysql.connect(
                host=db_host,
                port=3306,
                user='root',
                password='password',
                database='testmanagement',
                charset='utf8mb4'
            )
            connection.close()
            print(f"✅ Database is ready! (Connected to {db_host})")
            return True
        except Exception as e:
            retry_count += 1
            print(f"Waiting for database connection to {db_host}... (attempt {retry_count}/{max_retries})")
            time.sleep(2)
    
    print(f"❌ Failed to connect to database at {db_host} after maximum retries")
    return False

if __name__ == '__main__':
    if wait_for_database():
        sys.exit(0)
    else:
        sys.exit(1)
