#!/bin/bash
# Start the Call Screening Agents
# This script loads environment variables and starts the dual-agent system
# Note: Uses port 5001 by default (port 5000 is used by AirPlay on macOS)

set -e

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    echo "  cp .env.example .env"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.8 or higher is required"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if ! pip show signalwire-agents > /dev/null 2>&1; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the agents
echo "Starting Call Screening Agents..."
echo "=================================="
python3 screening_agents.py
