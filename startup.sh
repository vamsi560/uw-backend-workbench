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

# Start the FastAPI application with Gunicorn (ASGI via uvicorn worker). Fallback to uvicorn if Gunicorn fails.
echo "Starting FastAPI application with Gunicorn (uvicorn worker)..."
GUNICORN_CMD="gunicorn main:app --bind 0.0.0.0:8000 --workers ${WEB_CONCURRENCY:-2} --worker-class uvicorn.workers.UvicornWorker --timeout 180 --access-logfile - --error-logfile - --log-level info"

if command -v gunicorn >/dev/null 2>&1; then
    echo "Launching Gunicorn: $GUNICORN_CMD"
    eval $GUNICORN_CMD || FALLBACK=1
else
    echo "Gunicorn not found, enabling fallback"
    FALLBACK=1
fi

if [ "$FALLBACK" = "1" ]; then
    echo "FALLBACK: Starting with uvicorn directly"
    exec python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
else
    # Replace shell with gunicorn master process
    exec $GUNICORN_CMD
fi