"""
Agent - Clase base para agentes de IA

Representa un agente individual con un modelo y rol específico
"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import httpx
import logging

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Estados posibles de un agente"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"


class Agent:
    """Clase base para un agente de IA"""
    
    def __init__(
        self,
        role: str,
        model: str,
        system_prompt: str,
        allowed_tools: List[str],
        ollama_url: str,
        agent_id: Optional[str] = None
    ):
        self.id = agent_id or str(uuid.uuid4())
        self.role = role
        self.model = model
        self.system_prompt = system_prompt
        self.allowed_tools = allowed_tools
        self.ollama_url = ollama_url
        
        self.status = AgentStatus.INITIALIZING
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        # Historial de conversación
        self.conversation_history: List[Dict] = []
        
        # Estadísticas
        self.tasks_completed = 0
        self.total_tokens_used = 0
    
    async def initialize(self) -> bool:
        """
        Inicializa el agente (carga el modelo si es necesario)
        
        Returns:
            True si se inicializó correctamente
        """
        try:
            logger.info(f"Initializing agent {self.id} with model {self.model}")
            
            # Hacer un request simple para asegurar que el modelo está cargado
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": "Initialize",
                        "stream": False
                    }
                )
                response.raise_for_status()
            
            self.status = AgentStatus.READY
            logger.info(f"Agent {self.id} ready")
            return True
        
        except Exception as e:
            logger.error(f"Error initializing agent {self.id}: {e}")
            self.status = AgentStatus.ERROR
            return False
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una tarea
        
        Args:
            task: Diccionario con la tarea a ejecutar
                  {
                      "type": "chat" | "tool_use" | "analysis",
                      "content": "...",
                      "context": {...}
                  }
        
        Returns:
            Resultado de la tarea
        """
        if self.status != AgentStatus.READY:
            return {
                "success": False,
                "error": f"Agent not ready (status: {self.status})"
            }
        
        self.status = AgentStatus.BUSY
        self.last_activity = datetime.now()
        
        try:
            task_type = task.get("type", "chat")
            
            if task_type == "chat":
                result = await self._execute_chat(task)
            elif task_type == "tool_use":
                result = await self._execute_tool(task)
            elif task_type == "analysis":
                result = await self._execute_analysis(task)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown task type: {task_type}"
                }
            
            if result.get("success"):
                self.tasks_completed += 1
            
            self.status = AgentStatus.READY
            return result
        
        except Exception as e:
            logger.error(f"Error executing task in agent {self.id}: {e}")
            self.status = AgentStatus.ERROR
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_chat(self, task: Dict) -> Dict:
        """
        Ejecuta una tarea de chat
        
        Args:
            task: {
                "content": "user message",
                "context": {...}
            }
        
        Returns:
            Respuesta del modelo
        """
        user_message = task.get("content", "")
        context = task.get("context", {})
        
        # Detectar si el usuario quiere ejecutar herramientas
        tool_result = await self._detect_and_execute_tool(user_message)
        
        if tool_result:
            # Si se ejecutó una herramienta, devolver el resultado
            return tool_result
        
        # Si no, continuar con chat normal
        # Construir mensajes con historial
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Agregar contexto si existe
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            messages.append({
                "role": "system",
                "content": f"Additional context:\n{context_str}"
            })
        
        # Agregar historial reciente (últimos 5 mensajes)
        messages.extend(self.conversation_history[-5:])
        
        # Agregar mensaje actual
        messages.append({"role": "user", "content": user_message})
        
        try:
            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False
                    }
                )
                response.raise_for_status()
                data = response.json()
            
            assistant_message = data["message"]["content"]
            
            # Actualizar historial
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            # Actualizar estadísticas
            self.total_tokens_used += data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
            
            return {
                "success": True,
                "response": assistant_message,
                "tokens_used": data.get("eval_count", 0)
            }
        
        except Exception as e:
            logger.error(f"Chat error in agent {self.id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _detect_and_execute_tool(self, user_message: str) -> Optional[Dict]:
        """
        Detecta si el mensaje del usuario requiere ejecutar herramientas
        y las ejecuta automáticamente
        
        Returns:
            Resultado de la herramienta o None si no se detectó ninguna
        """
        import re
        
        msg_lower = user_message.lower()
        
        # Detectar intención de escaneo con nmap
        if any(keyword in msg_lower for keyword in ["escaneo", "escanea", "scan", "nmap"]):
            # Extraer IP o dominio
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            domain_pattern = r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]\b'
            
            target = None
            ip_match = re.search(ip_pattern, user_message)
            if ip_match:
                target = ip_match.group(0)
            else:
                domain_match = re.search(domain_pattern, user_message)
                if domain_match:
                    target = domain_match.group(0)
            
            if target and "nmap" in self.allowed_tools:
                logger.info(f"Agent {self.id}: Auto-ejecutando nmap en {target}")
                
                result = await self._execute_tool({
                    "tool": "nmap",
                    "params": {
                        "target": target,
                        "flags": "-sV -sC"  # Default: version detection + scripts
                    }
                })
                
                if result.get("success"):
                    response = f"✅ **Escaneo de {target} completado:**\n\n```\n{result.get('output', '')}\n```"
                else:
                    response = f"❌ **Error al escanear {target}:**\n\n{result.get('error', 'Unknown error')}"
                
                # Guardar en historial
                self.conversation_history.append({"role": "user", "content": user_message})
                self.conversation_history.append({"role": "assistant", "content": response})
                
                return {
                    "success": True,
                    "response": response,
                    "tool_executed": "nmap",
                    "target": target
                }
        
        # Detectar gobuster/directory busting
        if any(keyword in msg_lower for keyword in ["gobuster", "dirb", "fuzzing", "directories", "directorios"]):
            url_pattern = r'https?://[^\s]+'
            url_match = re.search(url_pattern, user_message)
            
            if url_match and "gobuster" in self.allowed_tools:
                url = url_match.group(0)
                logger.info(f"Agent {self.id}: Auto-ejecutando gobuster en {url}")
                
                result = await self._execute_tool({
                    "tool": "gobuster",
                    "params": {
                        "url": url,
                        "wordlist": "/usr/share/wordlists/dirb/common.txt"
                    }
                })
                
                if result.get("success"):
                    response = f"✅ **Directory busting de {url} completado:**\n\n```\n{result.get('output', '')}\n```"
                else:
                    response = f"❌ **Error en gobuster:**\n\n{result.get('error', 'Unknown error')}"
                
                self.conversation_history.append({"role": "user", "content": user_message})
                self.conversation_history.append({"role": "assistant", "content": response})
                
                return {
                    "success": True,
                    "response": response,
                    "tool_executed": "gobuster",
                    "target": url
                }
        
        # No se detectó herramienta
        return None
    
    async def _execute_tool(self, task: Dict) -> Dict:
        """
        Ejecuta una tarea que requiere uso de herramientas
        
        Args:
            task: {
                "tool": "nmap" | "gobuster" | "sqlmap" | "browser" | "command",
                "params": {...}
            }
        
        Returns:
            Resultado de la herramienta
        """
        tool_name = task.get("tool")
        params = task.get("params", {})
        
        if tool_name not in self.allowed_tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not allowed for this agent"
            }
        
        # Importar herramientas
        from ..integrations import CommandExecutor, BrowserController
        
        try:
            if tool_name == "nmap":
                # Ejecutar nmap
                executor = CommandExecutor()
                target = params.get("target", "")
                flags = params.get("flags", "-sV -sC")
                
                result = await executor.execute_nmap(target, flags)
                
                return {
                    "success": result["success"],
                    "tool": "nmap",
                    "output": result["stdout"],
                    "error": result["stderr"] if not result["success"] else None
                }
            
            elif tool_name == "gobuster":
                # Directory busting
                executor = CommandExecutor()
                url = params.get("url", "")
                wordlist = params.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
                
                result = await executor.execute_gobuster(url, wordlist)
                
                return {
                    "success": result["success"],
                    "tool": "gobuster",
                    "output": result["stdout"],
                    "error": result["stderr"] if not result["success"] else None
                }
            
            elif tool_name == "sqlmap":
                # SQL injection testing
                executor = CommandExecutor()
                url = params.get("url", "")
                
                result = await executor.execute_sqlmap(url)
                
                return {
                    "success": result["success"],
                    "tool": "sqlmap",
                    "output": result["stdout"],
                    "error": result["stderr"] if not result["success"] else None
                }
            
            elif tool_name == "metasploit":
                # Metasploit commands
                executor = CommandExecutor()
                commands = params.get("commands", [])
                
                result = await executor.execute_metasploit(commands)
                
                return {
                    "success": result["success"],
                    "tool": "metasploit",
                    "output": result["stdout"],
                    "error": result["stderr"] if not result["success"] else None
                }
            
            elif tool_name == "browser":
                # Browser automation
                action = params.get("action", "navigate")
                
                browser = BrowserController()
                await browser.initialize()
                
                if action == "navigate":
                    url = params.get("url", "")
                    result = await browser.navigate(url)
                    
                    # Extraer información útil
                    html = await browser.get_html()
                    links = await browser.extract_links()
                    forms = await browser.extract_forms()
                    
                    await browser.close()
                    
                    return {
                        "success": result["success"],
                        "tool": "browser",
                        "url": result.get("url"),
                        "title": result.get("title"),
                        "links_count": len(links),
                        "forms_count": len(forms),
                        "links": links[:20],  # Primeros 20
                        "forms": forms
                    }
                
                elif action == "screenshot":
                    url = params.get("url", "")
                    path = params.get("path", "/tmp/screenshot.png")
                    
                    await browser.navigate(url)
                    result = await browser.screenshot(path)
                    await browser.close()
                    
                    return {
                        "success": result["success"],
                        "tool": "browser",
                        "action": "screenshot",
                        "path": path
                    }
                
                await browser.close()
            
            elif tool_name == "command":
                # Comando arbitrario
                executor = CommandExecutor()
                cmd = params.get("cmd", "")
                
                if not cmd:
                    return {
                        "success": False,
                        "error": "No command specified"
                    }
                
                result = await executor.execute(cmd)
                
                return {
                    "success": result["success"],
                    "tool": "command",
                    "command": cmd,
                    "output": result["stdout"],
                    "error": result["stderr"] if not result["success"] else None,
                    "exit_code": result["exit_code"]
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }
        
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }

    
    async def _execute_analysis(self, task: Dict) -> Dict:
        """
        Ejecuta una tarea de análisis
        
        Args:
            task: {
                "data": "data to analyze",
                "format": "text" | "json" | "xml"
            }
        
        Returns:
            Análisis del modelo
        """
        data = task.get("data", "")
        format_type = task.get("format", "text")
        
        # Crear prompt de análisis
        analysis_prompt = f"""Analyze the following {format_type} data and provide insights:

{data}

Provide:
1. Summary of findings
2. Key points of interest
3. Potential security implications
4. Recommended next steps
"""
        
        # Usar el método de chat para el análisis
        return await self._execute_chat({
            "content": analysis_prompt
        })
    
    async def stop(self) -> bool:
        """
        Detiene el agente
        
        Returns:
            True si se detuvo correctamente
        """
        logger.info(f"Stopping agent {self.id}")
        self.status = AgentStatus.STOPPED
        return True
    
    def get_info(self) -> Dict:
        """Retorna información del agente"""
        return {
            "id": self.id,
            "role": self.role,
            "model": self.model,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "tasks_completed": self.tasks_completed,
            "total_tokens_used": self.total_tokens_used,
            "conversation_length": len(self.conversation_history),
            "allowed_tools": self.allowed_tools
        }
    
    def clear_history(self):
        """Limpia el historial de conversación"""
        self.conversation_history = []
        logger.info(f"Cleared conversation history for agent {self.id}")
