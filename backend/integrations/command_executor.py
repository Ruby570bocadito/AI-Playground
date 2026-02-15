"""
Command Executor - Ejecución de comandos del sistema

Responsabilidades:
- Ejecutar comandos shell con output en tiempo real
- Integración con herramientas de pentesting
- Gestión de procesos y timeouts
"""

import asyncio
import subprocess
import shlex
import os
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class CommandExecutor:
    """Ejecutor de comandos del sistema"""
    
    def __init__(self, workspace_dir: str = "/tmp/pentest-playground", timeout: int = 300):
        self.workspace_dir = workspace_dir
        self.default_timeout = timeout
        
        # Crear workspace si no existe
        os.makedirs(workspace_dir, exist_ok=True)
    
    async def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict] = None
    ) -> Dict:
        """
        Ejecuta un comando del sistema
        
        Args:
            command: Comando a ejecutar
            timeout: Timeout en segundos (None = default)
            cwd: Working directory (None = workspace)
            env: Variables de entorno adicionales
        
        Returns:
            {
                "success": bool,
                "stdout": str,
                "stderr": str,
                "exit_code": int,
                "command": str,
                "timed_out": bool
            }
        """
        timeout = timeout or self.default_timeout
        cwd = cwd or self.workspace_dir
        
        logger.info(f"Executing command: {command}")
        logger.info(f"Working directory: {cwd}")
        
        try:
            # Preparar entorno
            proc_env = os.environ.copy()
            if env:
                proc_env.update(env)
            
            # Ejecutar comando
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=proc_env
            )
            
            # Esperar con timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                timed_out = False
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                stdout, stderr = b"", b"Command timed out"
                timed_out = True
            
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            result = {
                "success": process.returncode == 0 and not timed_out,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "exit_code": process.returncode,
                "command": command,
                "timed_out": timed_out
            }
            
            if result["success"]:
                logger.info(f"Command completed successfully")
            else:
                logger.warning(f"Command failed with exit code {process.returncode}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "command": command,
                "timed_out": False
            }
    
    async def execute_nmap(
        self,
        target: str,
        flags: str = "-sV -sC",
        output_file: Optional[str] = None
    ) -> Dict:
        """
        Ejecuta nmap con parámetros específicos
        
        Args:
            target: IP o dominio objetivo
            flags: Flags de nmap
            output_file: Archivo de salida (opcional)
        
        Returns:
            Resultado de la ejecución
        """
        cmd = f"nmap {flags} {target}"
        
        if output_file:
            output_path = os.path.join(self.workspace_dir, output_file)
            cmd += f" -oN {output_path}"
        
        return await self.execute(cmd, timeout=600)  # 10 min timeout
    
    async def execute_gobuster(
        self,
        url: str,
        wordlist: str = "/usr/share/wordlists/dirb/common.txt",
        extensions: Optional[str] = None
    ) -> Dict:
        """
        Ejecuta gobuster para directory busting
        
        Args:
            url: URL objetivo
            wordlist: Path al wordlist
            extensions: Extensiones a buscar (ej: "php,html")
        
        Returns:
            Resultado de la ejecución
        """
        cmd = f"gobuster dir -u {url} -w {wordlist}"
        
        if extensions:
            cmd += f" -x {extensions}"
        
        return await self.execute(cmd, timeout=600)
    
    async def execute_sqlmap(
        self,
        url: str,
        params: Optional[str] = None,
        extra_args: str = ""
    ) -> Dict:
        """
        Ejecuta SQLMap
        
        Args:
            url: URL objetivo
            params: Parámetros a testear
            extra_args: Argumentos adicionales
        
        Returns:
            Resultado de la ejecución
        """
        cmd = f"sqlmap -u {url}"
        
        if params:
            cmd += f" -p {params}"
        
        if extra_args:
            cmd += f" {extra_args}"
        
        # Batch mode para no interactivo
        cmd += " --batch"
        
        return await self.execute(cmd, timeout=900)  # 15 min timeout
    
    async def execute_metasploit(
        self,
        commands: List[str]
    ) -> Dict:
        """
        Ejecuta comandos en msfconsole
        
        Args:
            commands: Lista de comandos para msfconsole
        
        Returns:
            Resultado de la ejecución
        """
        # Crear archivo de resource
        resource_file = os.path.join(self.workspace_dir, "msf_commands.rc")
        
        with open(resource_file, 'w') as f:
            for cmd in commands:
                f.write(f"{cmd}\n")
            f.write("exit\n")
        
        cmd = f"msfconsole -q -r {resource_file}"
        
        return await self.execute(cmd, timeout=1800)  # 30 min timeout
    
    async def execute_python_script(
        self,
        script_path: str,
        args: str = ""
    ) -> Dict:
        """
        Ejecuta un script Python
        
        Args:
            script_path: Path al script
            args: Argumentos del script
        
        Returns:
            Resultado de la ejecución
        """
        cmd = f"python3 {script_path} {args}"
        return await self.execute(cmd)
    
    async def execute_interactive(
        self,
        command: str,
        inputs: List[str]
    ) -> Dict:
        """
        Ejecuta comando interactivo con inputs predefinidos
        
        Args:
            command: Comando a ejecutar
            inputs: Lista de inputs a enviar
        
        Returns:
            Resultado de la ejecución
        """
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_dir
            )
            
            # Enviar inputs
            input_str = "\n".join(inputs) + "\n"
            stdout, stderr = await process.communicate(input_str.encode())
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "exit_code": process.returncode,
                "command": command,
                "timed_out": False
            }
        
        except Exception as e:
            logger.error(f"Error in interactive command: {e}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "command": command,
                "timed_out": False
            }
    
    def save_output(self, filename: str, content: str) -> str:
        """
        Guarda output en archivo
        
        Args:
            filename: Nombre del archivo
            content: Contenido a guardar
        
        Returns:
            Path completo del archivo
        """
        filepath = os.path.join(self.workspace_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        logger.info(f"Output saved to {filepath}")
        return filepath
    
    def read_file(self, filename: str) -> Optional[str]:
        """
        Lee un archivo del workspace
        
        Args:
            filename: Nombre del archivo
        
        Returns:
            Contenido del archivo o None
        """
        filepath = os.path.join(self.workspace_dir, filename)
        
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return None
        
        with open(filepath, 'r') as f:
            return f.read()
    
    def list_files(self) -> List[str]:
        """Lista archivos en el workspace"""
        return os.listdir(self.workspace_dir)
