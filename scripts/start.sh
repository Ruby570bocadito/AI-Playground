#!/bin/bash

# AI Pentesting Playground - Start Script

set -e

echo "============================================================"
echo "  🚀 Starting AI Pentesting Playground"
echo "============================================================"
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠${NC}  Virtual environment not found"
    echo "Please run: ./scripts/install.sh first"
    exit 1
fi

# Activate venv
echo "→ Activating virtual environment..."
source venv/bin/activate

# Check Ollama
echo "→ Checking Ollama..."
if ! systemctl is-active --quiet ollama 2>/dev/null; then
    echo -e "${YELLOW}⚠${NC}  Ollama service is not running"
    echo "Attempting to start Ollama..."
    sudo systemctl start ollama
fi

# Wait for Ollama to be ready
echo "→ Waiting for Ollama to be ready..."
for i in {1..10}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Ollama is ready"
        break
    fi
    sleep 1
done

# Get IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

echo
echo "============================================================"
echo "  Starting server..."
echo "============================================================"
echo
echo "  Local URL:    http://localhost:8080"
echo "  Network URL:  http://${IP_ADDR}:8080"
echo "  API Docs:     http://localhost:8080/docs"
echo
echo "============================================================"
echo

# Start the server
cd backend
python3 main.py
