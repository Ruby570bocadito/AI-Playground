#!/bin/bash

# AI Pentesting Playground - Installation Script for Kali Linux

set -e  # Exit on error

echo "============================================================"
echo "  🔐 AI Pentesting Playground - Installation"
echo "============================================================"
echo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   print_error "Please do not run as root"
   exit 1
fi

echo "→ Checking prerequisites..."

# Check Python 3
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    print_warning "Install with: sudo apt-get install python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
print_success "Python 3 found (version $PYTHON_VERSION)"

# Check pip
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed"
    print_warning "Install with: sudo apt-get install python3-pip"
    exit 1
fi

print_success "pip3 found"

# Check Ollama
echo
echo "→ Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    print_warning "Ollama is not installed"
    read -p "Do you want to install Ollama? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
        print_success "Ollama installed"
        
        # Start Ollama service
        echo "Starting Ollama service..."
        sudo systemctl start ollama
        sudo systemctl enable ollama
        print_success "Ollama service started"
    else
        print_warning "Skipping Ollama installation. You'll need to install it manually."
    fi
else
    print_success "Ollama found"
    
    # Check if Ollama is running
    if systemctl is-active --quiet ollama 2>/dev/null; then
        print_success "Ollama service is running"
    else
        print_warning "Ollama service is not running"
        echo "Starting Ollama service..."
        sudo systemctl start ollama
        print_success "Ollama service started"
    fi
fi

echo
echo "→ Creating Python virtual environment..."

# Create venv
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate venv
source venv/bin/activate
print_success "Virtual environment activated"

echo
echo "→ Installing Python dependencies..."

# Upgrade pip
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Install Playwright browsers
echo
echo "→ Installing Playwright browsers..."
playwright install chromium
print_success "Playwright browsers installed"

echo
echo "→ Creating workspace directory..."

# Create workspace
WORKSPACE_DIR="/tmp/pentest-playground"
if [ ! -d "$WORKSPACE_DIR" ]; then
    mkdir -p "$WORKSPACE_DIR"
    print_success "Workspace created at $WORKSPACE_DIR"
else
    print_success "Workspace already exists"
fi

echo
echo "→ Configuration..."

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    print_error "config.yaml not found"
    exit 1
fi

print_success "Configuration file found"

echo
echo "============================================================"
echo "  ✅ Installation Complete!"
echo "============================================================"
echo
echo "Next steps:"
echo "  1. (Optional) Download models:"
echo "     ollama pull llama3.2"
echo "     ollama pull mistral"
echo "     ollama pull codellama"
echo
echo "  2. Start the playground:"
echo "     ./scripts/start.sh"
echo
echo "  3. Access the web interface:"
echo "     http://$(hostname -I | awk '{print $1}'):8080"
echo
echo "============================================================"
