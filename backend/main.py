"""
AI Pentesting Playground - Main FastAPI Application

Servidor web que expone la API para gestión de agentes y modelos
"""

import os
import yaml
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from models import ModelManager
from agents import AgentManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variables globales
config: Dict[str, Any] = {}
model_manager: ModelManager = None
agent_manager: AgentManager = None


def load_config() -> Dict[str, Any]:
    """Carga configuración desde config.yaml"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    
    logger.info("Configuration loaded")
    return cfg


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    # Startup
    global config, model_manager, agent_manager
    
    logger.info("=" * 60)
    logger.info("🚀 AI Pentesting Playground - Starting Up")
    logger.info("=" * 60)
    
    config = load_config()
    
    # Inicializar Model Manager
    model_manager = ModelManager(
        ollama_url=config['ollama']['base_url'],
        models_catalog=config['models_catalog']
    )
    
    # Verificar Ollama
    is_healthy = await model_manager.health_check()
    if is_healthy:
        logger.info("✓ Ollama is running")
    else:
        logger.warning("⚠️  Ollama is not running or not accessible")
    
    # Inicializar Agent Manager
    agent_manager = AgentManager(
        model_manager=model_manager,
        roles_config=config['roles'],
        ollama_url=config['ollama']['base_url']
    )
    
    logger.info("✓ Agent Manager initialized")
    logger.info("=" * 60)
    logger.info("✓ Server ready")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await agent_manager.shutdown_all()


# Crear aplicación
app = FastAPI(
    title="AI Pentesting Playground",
    description="Multi-agent AI system for penetration testing",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CreateAgentRequest(BaseModel):
    role: str
    model: str
    custom_prompt: Optional[str] = None
    custom_tools: Optional[List[str]] = None


class TaskRequest(BaseModel):
    type: str  # chat, tool_use, analysis
    content: Optional[str] = None
    context: Optional[Dict] = None
    tool: Optional[str] = None
    params: Optional[Dict] = None
    data: Optional[str] = None
    format: Optional[str] = None


class ModelDownloadRequest(BaseModel):
    model_name: str


# ============================================================================
# ENDPOINTS - SYSTEM
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AI Pentesting Playground",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "models": "/api/models",
            "agents": "/api/agents",
            "health": "/api/health"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check"""
    ollama_healthy = await model_manager.health_check()
    
    return {
        "status": "ok",
        "ollama": "healthy" if ollama_healthy else "unhealthy",
        "models_loaded": len([m for m in await model_manager.list_available_models() if m.is_loaded]),
        "active_agents": len(agent_manager.agents)
    }


@app.get("/api/system/resources")
async def get_system_resources():
    """Obtiene recursos del sistema"""
    return await model_manager.get_system_resources()


# ============================================================================
# ENDPOINTS - MODELS
# ============================================================================

@app.get("/api/models")
async def list_models():
    """Lista todos los modelos disponibles"""
    models = await model_manager.list_available_models()
    
    return {
        "models": [
            {
                "name": m.name,
                "size_gb": m.size_gb,
                "ram_gb": m.ram_gb,
                "vram_gb": m.vram_gb,
                "parameters": m.parameters,
                "description": m.description,
                "is_downloaded": m.is_downloaded,
                "is_loaded": m.is_loaded
            }
            for m in models
        ]
    }


@app.post("/api/models/download")
async def download_model(request: ModelDownloadRequest):
    """Descarga un modelo"""
    logger.info(f"Download request for model: {request.model_name}")
    
    success = await model_manager.download_model(request.model_name)
    
    if success:
        return {"success": True, "model": request.model_name}
    else:
        raise HTTPException(status_code=500, detail="Failed to download model")


@app.get("/api/models/{model_name}/status")
async def get_model_status(model_name: str):
    """Obtiene estado de un modelo"""
    models = await model_manager.list_available_models()
    model = next((m for m in models if m.name == model_name), None)
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {
        "name": model.name,
        "is_downloaded": model.is_downloaded,
        "is_loaded": model.is_loaded,
        "size_gb": model.size_gb
    }


@app.post("/api/models/calculate-requirements")
async def calculate_requirements(model_names: List[str]):
    """Calcula requisitos para un conjunto de modelos"""
    requirements = model_manager.calculate_requirements(model_names)
    
    return {
        "requirements": {
            "total_ram_gb": requirements.total_ram_gb,
            "total_vram_gb": requirements.total_vram_gb,
            "total_disk_gb": requirements.total_disk_gb,
            "available_ram_gb": requirements.available_ram_gb,
            "available_vram_gb": requirements.available_vram_gb,
            "available_disk_gb": requirements.available_disk_gb,
            "can_allocate": requirements.can_allocate,
            "warnings": requirements.warnings
        }
    }


# ============================================================================
# ENDPOINTS - AGENTS
# ============================================================================

@app.get("/api/agents")
async def list_agents():
    """Lista todos los agentes activos"""
    agents = agent_manager.list_agents()
    return {"agents": agents}


@app.post("/api/agents")
async def create_agent(request: CreateAgentRequest):
    """Crea un nuevo agente"""
    logger.info(f"Creating agent: role={request.role}, model={request.model}")
    
    agent = await agent_manager.create_agent(
        role=request.role,
        model=request.model,
        custom_prompt=request.custom_prompt,
        custom_tools=request.custom_tools
    )
    
    if not agent:
        raise HTTPException(status_code=500, detail="Failed to create agent")
    
    return agent.get_info()


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Obtiene información de un agente"""
    agent = agent_manager.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent.get_info()


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Elimina un agente"""
    success = await agent_manager.delete_agent(agent_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"success": True, "agent_id": agent_id}


@app.post("/api/agents/{agent_id}/task")
async def execute_task(agent_id: str, task: TaskRequest):
    """Ejecuta una tarea en un agente"""
    # Convertir TaskRequest a dict
    task_dict = task.model_dump()
    
    result = await agent_manager.execute_task(agent_id, task_dict)
    return result


@app.post("/api/agents/{agent_id}/clear-history")
async def clear_agent_history(agent_id: str):
    """Limpia el historial de un agente"""
    agent = agent_manager.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.clear_history()
    return {"success": True}


@app.get("/api/agents/stats")
async def get_agent_stats():
    """Obtiene estadísticas de agentes"""
    return agent_manager.get_stats()


# ============================================================================
# ENDPOINTS - ROLES
# ============================================================================

@app.get("/api/roles")
async def list_roles():
    """Lista todos los roles disponibles"""
    return {
        "roles": {
            name: {
                "name": conf['name'],
                "description": conf['description'],
                "allowed_tools": conf['allowed_tools'],
                "recommended_models": conf['recommended_models']
            }
            for name, conf in config['roles'].items()
        }
    }


@app.get("/api/roles/{role_name}")
async def get_role(role_name: str):
    """Obtiene detalles de un rol"""
    if role_name not in config['roles']:
        raise HTTPException(status_code=404, detail="Role not found")
    
    role_config = config['roles'][role_name]
    return {
        "name": role_config['name'],
        "description": role_config['description'],
        "system_prompt": role_config['system_prompt'],
        "allowed_tools": role_config['allowed_tools'],
        "recommended_models": role_config['recommended_models']
    }


# ============================================================================
# STATIC FILES (Frontend)
# ============================================================================

# Servir archivos estáticos del frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Sirve el frontend"""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        
        file_path = os.path.join(frontend_path, full_path or "index.html")
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        else:
            # Fallback a index.html para SPA routing
            return FileResponse(os.path.join(frontend_path, "index.html"))


if __name__ == "__main__":
    import uvicorn
    
    cfg = load_config()
    host = cfg['server'].get('host', '0.0.0.0')
    port = cfg['server'].get('port', 8080)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
