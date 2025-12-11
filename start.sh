#!/bin/bash

# RepSmith Startup Script

echo "================================================"
echo "  RepSmith - Kodály Repertoire Analysis Tool"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Initialize database if needed
if [ ! -f "data/repsmith.db" ]; then
    echo "Initializing database..."
    python backend/database.py
fi

# Start the server
echo ""
echo "Starting RepSmith server..."
echo "Access the application at: http://localhost:5000"
echo ""
python backend/app.py
