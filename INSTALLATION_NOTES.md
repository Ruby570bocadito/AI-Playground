# 🐧 Installation Notes for Kali Linux

## Python 3.13 Compatibility

Kali Linux 2024.x comes with **Python 3.13** by default. This project is now fully compatible with Python 3.13.

### Quick Install (Kali Linux)

```bash
# Clone the repository
git clone https://github.com/Ruby570bocadito/AI-Playground
cd AI-Playground

# Run the installer
chmod +x scripts/install.sh
./scripts/install.sh
```

The installer will:
1. ✅ Check Python 3.13
2. ✅ Install/verify Ollama
3. ✅ Create virtual environment
4. ✅ Install all dependencies (Python 3.13 compatible)
5. ✅ Install Playwright browsers

### Manual Installation

If the script fails, run manually:

```bash
# Create venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### Starting the Playground

```bash
# Method 1: Use start script
./scripts/start.sh

# Method 2: Manual start
source venv/bin/activate
python backend/main.py
```

Then open: http://localhost:8000

## Troubleshooting

### Problem: `greenlet` or `pydantic-core` build errors

**Solution:** Make sure you're using the updated `requirements.txt` that specifies:
- `playwright==1.48.0` (includes greenlet 3.1.1+ compatible with Python 3.13)
- `pydantic==2.9.0` (compatible with Python 3.13)

```bash
# Pull latest changes
git pull

# Reinstall
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Problem: Ollama not found

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start service
sudo systemctl start ollama

# Download a model
ollama pull llama2
```

### Problem: Permission denied on scripts

```bash
chmod +x scripts/*.sh
```

## Supported Python Versions

- ✅ Python 3.11
- ✅ Python 3.12  
- ✅ Python 3.13

## Next Steps

1. Download an LLM model: `ollama pull llama2`
2. Create your first agent in the web UI
3. Start pentesting! 🔐
