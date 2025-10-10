#!/bin/bash
# Azure Web App startup script for FastAPI application

echo "Starting Azure Web App deployment..."
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "Files in directory: $(ls -la)"

# Install dependencies
echo "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements-azure.txt

# Set up database tables
echo "Setting up database tables..."
python -c "
try:
    from database import create_tables
    create_tables()
    print('Database tables created successfully')
except Exception as e:
    print(f'Database setup error: {e}')
"

# Start the FastAPI application with Gunicorn
echo "Starting FastAPI application..."
exec gunicorn main:app \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info