#!/bin/bash

# Set the working directory to the script's location (same folder as app.py)
cd "$(dirname "$0")"

# Load environment variables from the .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "Environment variables loaded from .env file."
else
    echo ".env file not found! Please ensure it's in the same directory."
    exit 1
fi

# Check if port is set
if [ -z "$port" ]; then
    echo "Error: 'port' is not set in the .env file."
    exit 1
else
    echo "Using port: $port"
fi

# Check if Python 3.10 is installed
if ! python3.10 --version &>/dev/null; then
    echo "Python 3.10 not found. Installing Python 3.10..."
    sudo apt update
    sudo apt install -y python3.10 python3.10-venv python3.10-dev
else
    echo "Python 3.10 is already installed."
fi

# Create a virtual environment (optional, but recommended)
if [ ! -d "venv" ]; then
    python3.10 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
source venv/bin/activate

# Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "No requirements.txt found. Skipping dependencies installation."
fi

# Start Gunicorn with automatic restarts on failure
while true; do
    echo "Starting Gunicorn on port $port..."
    gunicorn --workers 3 --bind 0.0.0.0:$port app:app
    echo "Gunicorn crashed. Restarting in 5 seconds..."
    sleep 5
done

# Deactivate the virtual environment
deactivate
