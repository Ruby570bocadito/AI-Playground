"""
Agent Manager - Orquestador de agentes

Responsabilidades:
- Crear y destruir agentes
- Gestionar pool de agentes activos
- Coordinar tareas entre múltiples agentes
- Optimizar uso de recursos
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import logging

from .agent import Agent, AgentStatus
from ..models import ModelManager

logger = logging.getLogger(__name__)


class AgentManager:
    """Gestor centralizado de agentes"""
    
    def __init__(self, model_manager: ModelManager, roles_config: Dict, ollama_url: str):
        self.model_manager = model_manager
        self.roles_config = roles_config
        self.ollama_url = ollama_url
        
        # Pool de agentes activos
        self.agents: Dict[str, Agent] = {}
        
        # Estadísticas
        self.total_agents_created = 0
    
    async def create_agent(
        self,
        role: str,
        model: str,
        custom_prompt: Optional[str] = None,
        custom_tools: Optional[List[str]] = None
    ) -> Optional[Agent]:
        """
        Crea un nuevo agente
        
        Args:
            role: Rol del agente (recon, exploit, analysis, custom)
            model: Modelo a usar
            custom_prompt: Prompt personalizado (opcional)
            custom_tools: Herramientas permitidas custom (opcional)
        
        Returns:
            Agent creado o None si falla
        """
        logger.info(f"Creating agent with role={role}, model={model}")
        
        # Verificar que el rol existe
        if role not in self.roles_config:
            logger.error(f"Role '{role}' not found in config")
            return None
        
        # Obtener configuración del rol
        role_config = self.roles_config[role]
        
        # Determinar prompt y tools
        system_prompt = custom_prompt or role_config['system_prompt']
        allowed_tools = custom_tools or role_config['allowed_tools']
        
        # Verificar que el modelo esté descargado
        models = await self.model_manager.list_available_models()
        model_info = next((m for m in models if m.name == model), None)
        
        if not model_info:
            logger.error(f"Model '{model}' not found")
            return None
        
        if not model_info.is_downloaded:
            logger.info(f"Model '{model}' not downloaded, downloading now...")
            success = await self.model_manager.download_model(model)
            if not success:
                logger.error(f"Failed to download model '{model}'")
                return None
        
        # Crear agente
        agent = Agent(
            role=role,
            model=model,
            system_prompt=system_prompt,
            allowed_tools=allowed_tools,
            ollama_url=self.ollama_url
        )
        
        # Inicializar (cargar modelo)
        success = await agent.initialize()
        if not success:
            logger.error(f"Failed to initialize agent")
            return None
        
        # Registrar en el pool
        self.agents[agent.id] = agent
        self.total_agents_created += 1
        
        logger.info(f"Agent {agent.id} created successfully")
        return agent
    
    async def delete_agent(self, agent_id: str) -> bool:
        """
        Elimina un agente
        
        Args:
            agent_id: ID del agente
        
        Returns:
            True si se eliminó correctamente
        """
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not found")
            return False
        
        agent = self.agents[agent_id]
        
        # Detener agente
        await agent.stop()
        
        # Intentar descargar el modelo si no hay más agentes usándolo
        model_in_use = any(
            a.model == agent.model and a.id != agent_id
            for a in self.agents.values()
        )
        
        if not model_in_use:
            logger.info(f"No other agents using model {agent.model}, unloading")
            await self.model_manager.unload_model(agent.model)
        
        # Remover del pool
        del self.agents[agent_id]
        
        logger.info(f"Agent {agent_id} deleted")
        return True
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Obtiene un agente por ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict]:
        """Lista todos los agentes activos"""
        return [agent.get_info() for agent in self.agents.values()]
    
    async def execute_task(self, agent_id: str, task: Dict) -> Dict:
        """
        Ejecuta una tarea en un agente específico
        
        Args:
            agent_id: ID del agente
            task: Tarea a ejecutar
        
        Returns:
            Resultado de la tarea
        """
        agent = self.get_agent(agent_id)
        
        if not agent:
            return {
                "success": False,
                "error": f"Agent {agent_id} not found"
            }
        
        return await agent.execute_task(task)
    
    async def broadcast_task(self, task: Dict, roles: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Ejecuta una tarea en múltiples agentes en paralelo
        
        Args:
            task: Tarea a ejecutar
            roles: Lista de roles a incluir (None = todos)
        
        Returns:
            Diccionario con resultados por agent_id
        """
        # Filtrar agentes
        target_agents = [
            agent for agent in self.agents.values()
            if roles is None or agent.role in roles
        ]
        
        if not target_agents:
            return {}
        
        logger.info(f"Broadcasting task to {len(target_agents)} agents")
        
        # Ejecutar en paralelo
        tasks = [
            agent.execute_task(task)
            for agent in target_agents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Mapear resultados
        return {
            agent.id: result if not isinstance(result, Exception) else {
                "success": False,
                "error": str(result)
            }
            for agent, result in zip(target_agents, results)
        }
    
    async def collaborative_task(self, agents_tasks: List[Dict]) -> List[Dict]:
        """
        Ejecuta tareas colaborativas entre agentes
        
        Args:
            agents_tasks: Lista de {agent_id, task}
        
        Returns:
            Lista de resultados en orden
        """
        tasks = []
        
        for item in agents_tasks:
            agent_id = item['agent_id']
            task = item['task']
            
            agent = self.get_agent(agent_id)
            if agent:
                tasks.append(agent.execute_task(task))
            else:
                tasks.append(asyncio.coroutine(lambda: {
                    "success": False,
                    "error": f"Agent {agent_id} not found"
                })())
        
        results = await asyncio.gather(*tasks)
        return results
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del manager"""
        return {
            "active_agents": len(self.agents),
            "total_created": self.total_agents_created,
            "agents_by_role": {
                role: sum(1 for a in self.agents.values() if a.role == role)
                for role in self.roles_config.keys()
            },
            "agents_by_status": {
                status.value: sum(1 for a in self.agents.values() if a.status == status)
                for status in AgentStatus
            }
        }
    
    async def shutdown_all(self) -> bool:
        """Detiene todos los agentes"""
        logger.info("Shutting down all agents")
        
        agent_ids = list(self.agents.keys())
        
        for agent_id in agent_ids:
            await self.delete_agent(agent_id)
        
        logger.info("All agents shut down")
        return True
