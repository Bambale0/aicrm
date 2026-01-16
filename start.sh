#!/bin/bash
# Start script for AI CRM application

set -e  # Exit on any error

# Change to the source directory
cd /root/saas/aicrm || { echo "Failed to change directory to /root/saas/aicrm"; exit 1; }

# Set default values for host and port if not provided
HOST=${HOST:-0.0.0.0}
FASTAPI_PORT=${FASTAPI_PORT:-8000}
SOCKET_PORT=${SOCKET_PORT:-8001}

echo "Starting FastAPI application on port ${FASTAPI_PORT}..."
python3 -c "from aicrm.main import app; import uvicorn; uvicorn.run(app, host='${HOST}', port=${FASTAPI_PORT})" &
FASTAPI_PID=$!

echo "Starting Socket.IO server on port ${SOCKET_PORT}..."
python3 -c "from aicrm.socket_server import socket_app; import uvicorn; uvicorn.run(socket_app, host='${HOST}', port=${SOCKET_PORT})" &
SOCKET_PID=$!

echo "FastAPI PID: ${FASTAPI_PID}"
echo "Socket.IO PID: ${SOCKET_PID}"

# Wait for both processes
wait ${FASTAPI_PID} ${SOCKET_PID}
