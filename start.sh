#!/bin/bash
# Start script for AI CRM application

set -e  # Exit on any error

# Change to the source directory
cd /root/aicrm/src || { echo "Failed to change directory to /root/aicrm/src"; exit 1; }

# Set default values for host and port if not provided
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}

# Run the FastAPI application with uvicorn
python3 -c "from aicrm.main import app; import uvicorn; uvicorn.run(app, host='${HOST}', port=${PORT})"
    