# 🚀 Quick Start Guide - Kali Linux

## Installation

```bash
# Clone repo
git clone https://github.com/Ruby570bocadito/AI-Playground
cd AI-Playground

# Run installer
chmod +x scripts/install.sh
./scripts/install.sh

# Download a model
ollama pull llama3.2
```

## Starting the Playground

```bash
# Activate virtual environment
source venv/bin/activate

# Start server
python3 -m backend.main
```

The server will start on:
- **Local**: http://localhost:8080
- **Network**: http://YOUR_IP:8080
- **API Docs**: http://localhost:8080/docs

## First Steps

1. Open http://localhost:8080 in your browser
2. Click "Create Agent"
3. Select a role (e.g., "recon")
4. Select model (llama3.2)
5. Click "Create"
6. Start chatting with your agent!

## Troubleshooting

### Permission denied: ./scripts/start.sh

```bash
chmod +x scripts/start.sh
```

### Import errors

Make sure you run from the project root:

```bash
cd ~/path/to/AI-Playground
source venv/bin/activate
python3 -m backend.main
```

### Ollama not running

```bash
sudo systemctl start ollama
```

## Features

✅ **Multi-Agent System** - Create specialized pentesting agents  
✅ **Real Command Execution** - nmap, gobuster, sqlmap, metasploit  
✅ **Browser Automation** - Playwright for web testing  
✅ **Debug Panel** - Real-time activity logging  
✅ **Permissions Management** - Control agent capabilities  
✅ **Local LLMs** - Privacy-first with Ollama  

Happy pentesting! 🔐
