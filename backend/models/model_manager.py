"""
Model Manager - Gestión dinámica de modelos Ollama

Responsabilidades:
- Listar modelos disponibles y descargados
- Descargar modelos bajo demanda
- Calcular requisitos de recursos
- Cargar/descargar modelos dinámicamente
"""

import asyncio
import httpx
import psutil
import subprocess
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Información de un modelo"""
    name: str
    size_gb: float
    ram_gb: float
    vram_gb: float
    parameters: str
    description: str
    is_downloaded: bool = False
    is_loaded: bool = False


@dataclass
class ResourceRequirements:
    """Requisitos de recursos"""
    total_ram_gb: float
    total_vram_gb: float
    total_disk_gb: float
    available_ram_gb: float
    available_vram_gb: float
    available_disk_gb: float
    can_allocate: bool
    warnings: List[str]


class ModelManager:
    """Gestor de modelos Ollama"""
    
    def __init__(self, ollama_url: str, models_catalog: Dict):
        self.ollama_url = ollama_url
        self.models_catalog = models_catalog
        self.loaded_models: Dict[str, bool] = {}
    
    async def list_available_models(self) -> List[ModelInfo]:
        """Lista todos los modelos del catálogo con su estado"""
        downloaded = await self.list_downloaded_models()
        downloaded_names = {m['name'] for m in downloaded}
        
        models = []
        for name, info in self.models_catalog.items():
            model = ModelInfo(
                name=name,
                size_gb=info['size_gb'],
                ram_gb=info['ram_gb'],
                vram_gb=info['vram_gb'],
                parameters=info['parameters'],
                description=info['description'],
                is_downloaded=name in downloaded_names,
                is_loaded=self.loaded_models.get(name, False)
            )
            models.append(model)
        
        return models
    
    async def list_downloaded_models(self) -> List[Dict]:
        """Lista modelos descargados en Ollama"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                
                return [
                    {
                        'name': model['name'].split(':')[0],  # Remove tag
                        'size': model.get('size', 0)
                    }
                    for model in data.get('models', [])
                ]
        except Exception as e:
            logger.error(f"Error listing downloaded models: {e}")
            return []
    
    async def download_model(self, model_name: str, progress_callback=None) -> bool:
        """
        Descarga un modelo usando ollama pull
        
        Args:
            model_name: Nombre del modelo
            progress_callback: Función opcional para reportar progreso
        
        Returns:
            True si se descargó exitosamente
        """
        logger.info(f"Downloading model: {model_name}")
        
        try:
            # Ejecutar ollama pull como subprocess
            process = await asyncio.create_subprocess_exec(
                'ollama', 'pull', model_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Leer output en tiempo real
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                output = line.decode().strip()
                logger.info(f"Download progress: {output}")
                
                if progress_callback:
                    await progress_callback(output)
            
            await process.wait()
            
            if process.returncode == 0:
                logger.info(f"Model {model_name} downloaded successfully")
                return True
            else:
                stderr = await process.stderr.read()
                logger.error(f"Error downloading {model_name}: {stderr.decode()}")
                return False
        
        except Exception as e:
            logger.error(f"Exception downloading model: {e}")
            return False
    
    async def load_model(self, model_name: str) -> bool:
        """
        Carga un modelo en memoria (hace un request simple para activarlo)
        
        Args:
            model_name: Nombre del modelo
        
        Returns:
            True si se cargó exitosamente
        """
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                # Hacer un request simple para "activar" el modelo
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": "Hello",
                        "stream": False
                    }
                )
                response.raise_for_status()
                
                self.loaded_models[model_name] = True
                logger.info(f"Model {model_name} loaded into memory")
                return True
        
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return False
    
    async def unload_model(self, model_name: str) -> bool:
        """
        Descarga un modelo de memoria
        
        Nota: Ollama no tiene API directa para esto, pero se puede hacer
        con 'ollama stop <model>' o simplemente marcar como no loaded
        
        Args:
            model_name: Nombre del modelo
        
        Returns:
            True si se descargó exitosamente
        """
        try:
            # Intentar detener el modelo
            process = await asyncio.create_subprocess_exec(
                'ollama', 'stop', model_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.wait()
            
            self.loaded_models[model_name] = False
            logger.info(f"Model {model_name} unloaded from memory")
            return True
        
        except Exception as e:
            logger.warning(f"Could not unload model {model_name}: {e}")
            # Aún así marcarlo como no loaded
            self.loaded_models[model_name] = False
            return True
    
    def calculate_requirements(self, model_names: List[str]) -> ResourceRequirements:
        """
        Calcula requisitos totales para un conjunto de modelos
        
        Args:
            model_names: Lista de nombres de modelos
        
        Returns:
            ResourceRequirements con totales y disponibilidad
        """
        total_ram = 0.0
        total_vram = 0.0
        total_disk = 0.0
        warnings = []
        
        # Calcular totales
        for name in model_names:
            if name in self.models_catalog:
                info = self.models_catalog[name]
                total_ram += info['ram_gb']
                total_vram += info['vram_gb']
                total_disk += info['size_gb']
            else:
                warnings.append(f"Model '{name}' not found in catalog")
        
        # Obtener recursos disponibles del sistema
        available_ram = psutil.virtual_memory().available / (1024**3)  # GB
        available_disk = psutil.disk_usage('/').free / (1024**3)  # GB
        
        # VRAM es más difícil de obtener, estimamos basado en GPU
        # Por ahora, asumimos 16GB (RTX 5070 típica)
        # TODO: Obtener VRAM real con pynvml
        available_vram = 16.0
        
        # Determinar si se puede alocar
        can_allocate = (
            total_ram <= available_ram and
            total_vram <= available_vram and
            total_disk <= available_disk
        )
        
        # Warnings adicionales
        if total_ram > available_ram * 0.8:
            warnings.append(f"RAM usage will be high ({total_ram:.1f}GB / {available_ram:.1f}GB available)")
        
        if total_vram > available_vram * 0.8:
            warnings.append(f"VRAM usage will be high ({total_vram:.1f}GB / {available_vram:.1f}GB available)")
        
        return ResourceRequirements(
            total_ram_gb=total_ram,
            total_vram_gb=total_vram,
            total_disk_gb=total_disk,
            available_ram_gb=available_ram,
            available_vram_gb=available_vram,
            available_disk_gb=available_disk,
            can_allocate=can_allocate,
            warnings=warnings
        )
    
    async def get_system_resources(self) -> Dict:
        """Obtiene recursos actuales del sistema"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'ram': {
                'total_gb': memory.total / (1024**3),
                'used_gb': memory.used / (1024**3),
                'available_gb': memory.available / (1024**3),
                'percent': memory.percent
            },
            'disk': {
                'total_gb': disk.total / (1024**3),
                'used_gb': disk.used / (1024**3),
                'free_gb': disk.free / (1024**3),
                'percent': disk.percent
            },
            'vram': {
                'total_gb': 16.0,  # TODO: Get real VRAM
                'used_gb': sum(
                    self.models_catalog[name]['vram_gb']
                    for name, loaded in self.loaded_models.items()
                    if loaded and name in self.models_catalog
                ),
                'available_gb': 16.0 - sum(
                    self.models_catalog[name]['vram_gb']
                    for name, loaded in self.loaded_models.items()
                    if loaded and name in self.models_catalog
                )
            }
        }
    
    async def health_check(self) -> bool:
        """Verifica que Ollama esté corriendo"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
