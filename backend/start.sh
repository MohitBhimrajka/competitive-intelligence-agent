#!/bin/bash
# Start script for the competitive intelligence agent backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Export environment variables from .env file if it exists
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Start the FastAPI application
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload 