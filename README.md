# AI Pentesting Playground

Multi-agent AI system for penetration testing with dynamic model management and intelligent resource optimization.

## 🎯 Features

- **Multi-Agent System**: Deploy multiple AI agents with different roles (Recon, Exploit, Analysis, Custom)
- **Dynamic Model Management**: Automatically download and manage Ollama models on demand
- **Intelligent Resource Optimization**: Agents load/unload dynamically to optimize GPU/RAM usage
- **Web Dashboard**: Modern web interface to manage agents and models
- **Role-Based Configuration**: Pre-configured roles for pentesting workflows
- **System Integration**: Execute commands, control browsers, and integrate with Kali tools

## 📋 Requirements

- **Kali Linux** (tested on latest version)
- **GPU**: NVIDIA GPU with 8GB+ VRAM recommended (16GB+ for multiple large models)
- **RAM**: 16GB minimum, 32GB+ recommended
- **Disk**: 100GB+ free space for models
- **Python**: 3.10 or higher
- **Ollama**: For local model inference

## 🚀 Quick Start

### 1. Clone or Extract

```bash
cd /path/to/ai-pentest-playground
```

### 2. Run Installation

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

This will:
- Check prerequisites
- Install Ollama (if not present)
- Create Python virtual environment
- Install all dependencies
- Setup Playwright browsers

### 3. Download Models (Optional but Recommended)

```bash
# Lightweight models (recommended for start)
ollama pull llama3.2      # 2GB - Fast, general purpose
ollama pull phi3          # 2.3GB - Efficient

# Medium models (good balance)
ollama pull mistral       # 4.1GB - Excellent reasoning
ollama pull codellama     # 3.8GB - Code analysis

# Large models (for analysis)
ollama pull llama3.2:70b  # 40GB - Powerful analysis
```

### 4. Start the Playground

```bash
./scripts/start.sh
```

### 5. Access Web Interface

Open your browser and navigate to:
- Local: `http://localhost:8080`
- Network: `http://<your-kali-ip>:8080`

## 📖 User Guide

### Creating an Agent

1. Click **"+ New Agent"** button
2. Select a **Role**:
   - **Recon**: For reconnaissance and enumeration
   - **Exploit**: For vulnerability analysis and exploitation
   - **Analysis**: For analyzing results and code
   - **Custom**: Fully customizable
3. Select a **Model** (only downloaded models appear)
4. (Optional) Customize the system prompt
5. Review estimated resource requirements
6. Click **"Create Agent"**

### Using an Agent

1. Click **"Chat"** on an agent card
2. Type your instruction or question
3. The agent will respond based on its role and capabilities

### Example Workflows

#### Workflow 1: Web Application Pentest

1. Create **Recon Agent** (llama3.2)
   ```
   "Scan domain: example.com, find subdomains and open ports"
   ```

2. Create **Exploit Agent** (mistral)
   ```
   "Analyze these findings: [paste recon output]"
   ```

3. Create **Analysis Agent** (codellama)
   ```
   "Review this code for vulnerabilities: [paste code]"
   ```

#### Workflow 2: Network Reconnaissance

1. Create **Recon Agent**
   ```
   "Run nmap scan on 192.168.1.0/24, identify all active hosts"
   ```

2. Let agent analyze and provide recommendations

### Managing Models

- **Download**: Click "Download" on any available model
- **Auto-Download**: When creating an agent with an un-downloaded model, it will download automatically
- **Resource Check**: System calculates requirements before creating agents

## ⚙️ Configuration

Edit `config.yaml` to customize:

- **Server Settings**: Host, port, CORS
- **Models Catalog**: Add/remove models, adjust resource estimates
- **Roles**: Customize system prompts and allowed tools
- **Security**: Whitelist commands, set timeouts

### Example: Custom Role

```yaml
roles:
  my_custom_role:
    name: "My Custom Agent"
    description: "Custom agent for specific tasks"
    system_prompt: |
      You are a specialized agent for...
    allowed_tools:
      - "nmap"
      - "custom_scripts"
    recommended_models:
      - "mistral"
```

## 🔧 API Reference

The playground exposes a comprehensive REST API:

### Endpoints

- `GET /api/health` - Health check
- `GET /api/models` - List all models
- `POST /api/models/download` - Download a model
- `GET /api/agents` - List active agents
- `POST /api/agents` - Create new agent
- `DELETE /api/agents/{id}` - Delete agent
- `POST /api/agents/{id}/task` - Execute task
- `GET /api/roles` - List available roles
- `GET /api/system/resources` - Get system resources

### Example: Create Agent via API

```bash
curl -X POST http://localhost:8080/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "role": "recon",
    "model": "llama3.2"
  }'
```

### Example: Execute Task

```bash
curl -X POST http://localhost:8080/api/agents/{agent_id}/task \
  -H "Content-Type: application/json" \
  -d '{
    "type": "chat",
    "content": "Scan 192.168.1.1"
  }'
```

## 🛠️ Troubleshooting

### Ollama Not Running

```bash
sudo systemctl start ollama
sudo systemctl status ollama
```

### Port 8080 Already in Use

Edit `config.yaml`:
```yaml
server:
  port: 9090  # Change to any available port
```

### Model Download Fails

```bash
# Check Ollama directly
ollama pull llama3.2

# Check disk space
df -h
```

### GPU Not Being Used

```bash
# Check NVIDIA drivers
nvidia-smi

# Reinstall Ollama
curl -fsSL https://ollama.com/install.sh | sh
```

### Agent Creation Fails

- Ensure the model is downloaded
- Check system resources (RAM/VRAM)
- Review logs in `backend/playground.log`

## 📁 Project Structure

```
ai-pentest-playground/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── models/              # Model management
│   ├── agents/              # Agent system
│   └── integrations/        # Tool integrations (future)
├── frontend/
│   ├── index.html           # Dashboard
│   └── assets/              # CSS & JS
├── scripts/
│   ├── install.sh           # Installation script
│   └── start.sh             # Startup script
├── config.yaml              # Configuration
└── requirements.txt         # Python dependencies
```

## 🔐 Security Considerations

> **⚠️ WARNING**: This tool has powerful capabilities and can execute system commands. Only use in controlled environments.

- Command execution is restricted to whitelisted tools
- Configurable timeout for all commands
- Isolated workspace at `/tmp/pentest-playground`
- Review `config.yaml` security settings before use

## 📝 Future Enhancements

Coming soon:
- [ ] Browser automation integration (Playwright)
- [ ] Metasploit integration
- [ ] Collaborative multi-agent tasks
- [ ] Real-time output streaming
- [ ] Custom tool plugins
- [ ] Export/import agent configurations

## 🤝 Contributing

This is a specialized tool for penetration testing education and practice. Use responsibly and only on systems you have permission to test.

## 📄 License

For educational and authorized security testing only.

---

**Built for Kali Linux** | **Powered by Ollama** | **Multi-Agent AI**
