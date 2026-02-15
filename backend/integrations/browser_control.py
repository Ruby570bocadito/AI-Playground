"""
Browser Control - Automatización de navegador con Playwright

Responsabilidades:
- Control de navegador para testing web
- Captura de screenshots
- Interacción con elementos
- Ejecución de JavaScript
"""

import asyncio
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import logging

logger = logging.getLogger(__name__)


class BrowserController:
    """Controlador de navegador con Playwright"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_initialized = False
    
    async def initialize(self, headless: bool = True) -> bool:
        """
        Inicializa el navegador
        
        Args:
            headless: Si debe ejecutarse sin interfaz gráfica
        
        Returns:
            True si se inicializó correctamente
        """
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=headless)
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            )
            self.page = await self.context.new_page()
            self.is_initialized = True
            
            logger.info("Browser initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error initializing browser: {e}")
            return False
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -> Dict:
        """
        Navega a una URL
        
        Args:
            url: URL de destino
            wait_until: Condición de espera (load, domcontentloaded, networkidle)
        
        Returns:
            Información de la navegación
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            response = await self.page.goto(url, wait_until=wait_until, timeout=30000)
            
            return {
                "success": True,
                "url": self.page.url,
                "status": response.status,
                "title": await self.page.title()
            }
        
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def screenshot(self, path: Optional[str] = None, full_page: bool = True) -> Dict:
        """
        Captura screenshot
        
        Args:
            path: Path donde guardar (None = retorna bytes)
            full_page: Capturar página completa
        
        Returns:
            Información del screenshot
        """
        try:
            screenshot_bytes = await self.page.screenshot(
                path=path,
                full_page=full_page
            )
            
            return {
                "success": True,
                "path": path,
                "size": len(screenshot_bytes)
            }
        
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_html(self) -> str:
        """Obtiene HTML de la página actual"""
        if not self.is_initialized:
            return ""
        
        return await self.page.content()
    
    async def get_text(self) -> str:
        """Obtiene texto visible de la página"""
        if not self.is_initialized:
            return ""
        
        return await self.page.inner_text('body')
    
    async def click(self, selector: str) -> Dict:
        """
        Click en elemento
        
        Args:
            selector: Selector CSS del elemento
        
        Returns:
            Resultado de la acción
        """
        try:
            await self.page.click(selector)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error clicking {selector}: {e}")
            return {"success": False, "error": str(e)}
    
    async def fill(self, selector: str, value: str) -> Dict:
        """
        Rellena campo de formulario
        
        Args:
            selector: Selector CSS del campo
            value: Valor a ingresar
        
        Returns:
            Resultado de la acción
        """
        try:
            await self.page.fill(selector, value)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error filling {selector}: {e}")
            return {"success": False, "error": str(e)}
    
    async def submit_form(self, selector: str) -> Dict:
        """
        Envía formulario
        
        Args:
            selector: Selector CSS del formulario
        
        Returns:
            Resultado de la acción
        """
        try:
            await self.page.locator(selector).dispatch_event('submit')
            await self.page.wait_for_load_state('networkidle')
            return {"success": True}
        except Exception as e:
            logger.error(f"Error submitting form {selector}: {e}")
            return {"success": False, "error": str(e)}
    
    async def execute_js(self, script: str) -> Dict:
        """
        Ejecuta JavaScript en la página
        
        Args:
            script: Código JavaScript
        
        Returns:
            Resultado de la ejecución
        """
        try:
            result = await self.page.evaluate(script)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error executing JS: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_cookies(self) -> List[Dict]:
        """Obtiene cookies actuales"""
        if not self.is_initialized:
            return []
        
        return await self.context.cookies()
    
    async def set_cookie(self, name: str, value: str, domain: str) -> bool:
        """
        Establece una cookie
        
        Args:
            name: Nombre de la cookie
            value: Valor
            domain: Dominio
        
        Returns:
            True si se estableció correctamente
        """
        try:
            await self.context.add_cookies([{
                'name': name,
                'value': value,
                'domain': domain,
                'path': '/'
            }])
            return True
        except Exception as e:
            logger.error(f"Error setting cookie: {e}")
            return False
    
    async def intercept_requests(self, url_pattern: str) -> List[Dict]:
        """
        Intercepta requests que matchean el patrón
        
        Args:
            url_pattern: Patrón de URL
        
        Returns:
            Lista de requests interceptadas
        """
        intercepted = []
        
        async def handle_request(request):
            if url_pattern in request.url:
                intercepted.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': request.headers
                })
        
        self.page.on('request', handle_request)
        return intercepted
    
    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> bool:
        """
        Espera a que aparezca un selector
        
        Args:
            selector: Selector CSS
            timeout: Timeout en ms
        
        Returns:
            True si apareció
        """
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False
    
    async def extract_links(self) -> List[str]:
        """Extrae todos los links de la página"""
        try:
            links = await self.page.eval_on_selector_all(
                'a[href]',
                'elements => elements.map(e => e.href)'
            )
            return links
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []
    
    async def extract_forms(self) -> List[Dict]:
        """Extrae información de formularios"""
        try:
            forms = await self.page.eval_on_selector_all(
                'form',
                '''elements => elements.map(form => ({
                    action: form.action,
                    method: form.method,
                    inputs: Array.from(form.querySelectorAll('input')).map(input => ({
                        name: input.name,
                        type: input.type,
                        value: input.value
                    }))
                }))'''
            )
            return forms
        except Exception as e:
            logger.error(f"Error extracting forms: {e}")
            return []
    
    async def close(self) -> bool:
        """Cierra el navegador"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            self.is_initialized = False
            logger.info("Browser closed")
            return True
        
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
            return False
