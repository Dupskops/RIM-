"""
Provider de LLM usando Ollama en contenedor Docker.

MVP v2.3 - Integración completa con chatbot:
- Métricas de tokens y tiempo de respuesta
- Soporte para múltiples tipos de prompts
- Configuración optimizada para Docker Compose
"""
import json
import logging
import time
from typing import AsyncGenerator, Optional, Dict, Any, Tuple
import aiohttp
from aiohttp import ClientTimeout, ClientError

from src.config.settings import settings


logger = logging.getLogger(__name__)


class OllamaProvider:
    """
    Cliente para interactuar con Ollama ejecutándose en contenedor Docker.
    
    Ollama es un servidor local de LLMs que permite ejecutar modelos como:
    - llama2, llama3
    - mistral, mixtral
    - codellama
    - phi, gemma, etc.
    
    Características:
    - Generación de texto con contexto
    - Streaming de respuestas
    - Control de temperatura y tokens
    - Soporte para system prompts
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60
    ):
        """
        Inicializa el provider de Ollama.
        
        Args:
            base_url: URL base de Ollama (default: desde settings o http://localhost:11434)
            model: Nombre del modelo a usar (default: desde settings o llama2)
            timeout: Timeout en segundos para requests (default: 60)
        """
        self.base_url = base_url or getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model_name = model or getattr(settings, 'OLLAMA_MODEL', 'llama2')
        self.timeout = ClientTimeout(total=timeout)
        
        logger.info(f"OllamaProvider inicializado: {self.base_url} - Modelo: {self.model_name}")
    
    async def health_check(self) -> bool:
        """
        Verifica que Ollama esté disponible.
        
        Returns:
            True si Ollama está disponible, False en caso contrario
        """
        try:
            async with aiohttp.ClientSession(timeout=ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    if resp.status == 200:
                        logger.info("Ollama health check: OK")
                        return True
                    logger.warning(f"Ollama health check failed: status {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"Ollama health check error: {e}")
            return False
    
    async def list_models(self) -> list[str]:
        """
        Lista los modelos disponibles en Ollama.
        
        Returns:
            Lista de nombres de modelos
        """
        try:
            async with aiohttp.ClientSession(timeout=ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = [model["name"] for model in data.get("models", [])]
                        logger.info(f"Modelos disponibles: {models}")
                        return models
                    return []
        except Exception as e:
            logger.error(f"Error listando modelos: {e}")
            return []
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        context: Optional[list[int]] = None,
        return_metrics: bool = False
    ) -> str | Tuple[str, Dict[str, Any]]:
        """
        Genera una respuesta completa (sin streaming).
        
        MVP v2.3 - Retorna métricas de generación para el chatbot.
        
        Args:
            prompt: Prompt del usuario
            system_prompt: Prompt del sistema (opcional)
            max_tokens: Máximo de tokens a generar
            temperature: Temperatura de generación (0.0-1.0)
            context: Contexto de conversación previa (opcional)
            return_metrics: Si True, retorna métricas (tokens, tiempo, modelo)
        
        Returns:
            - Si return_metrics=False: str (respuesta)
            - Si return_metrics=True: Tuple[str, Dict] (respuesta, métricas)
        
        Raises:
            aiohttp.ClientError: Si hay error de conexión
            ValueError: Si hay error en la respuesta
        """
        start_time = time.time()
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if context:
            payload["context"] = context
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                logger.info(f"[DEBUG] Enviando request a Ollama: {self.base_url}/api/generate. Model: {self.model_name}")
                req_start = time.time()
                
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as resp:
                    logger.info(f"[DEBUG] Respuesta recibida de Ollama en {time.time() - req_start:.4f}s. Status: {resp.status}")
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Error en Ollama: {resp.status} - {error_text}")
                        raise ValueError(f"Error en Ollama: {resp.status}")
                    
                    result = await resp.json()
                    response_text = result.get("response", "")
                    
                    # Calcular métricas
                    end_time = time.time()
                    tiempo_respuesta_ms = int((end_time - start_time) * 1000)
                    
                    logger.info(f"Respuesta generada: {len(response_text)} caracteres en {tiempo_respuesta_ms}ms")
                    
                    # Retornar con o sin métricas
                    if return_metrics:
                        metrics = {
                            "tokens_usados": result.get("eval_count", 0),  # Tokens generados
                            "tokens_prompt": result.get("prompt_eval_count", 0),  # Tokens del prompt
                            "tiempo_respuesta_ms": tiempo_respuesta_ms,
                            "modelo_usado": result.get("model", self.model_name),
                            "total_duration_ns": result.get("total_duration", 0),  # Duración total en nanosegundos
                        }
                        return response_text, metrics
                    else:
                        return response_text
                    
        except ClientError as e:
            logger.error(f"Error de conexión con Ollama: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado generando respuesta: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        context: Optional[list[int]] = None,
        return_metrics: bool = False
    ) -> AsyncGenerator[str | Dict[str, Any], None]:
        """
        Genera una respuesta con streaming (chunks en tiempo real).
        
        MVP v2.3 - Retorna métricas al final del stream como último elemento.
        
        Args:
            prompt: Prompt del usuario
            system_prompt: Prompt del sistema (opcional)
            max_tokens: Máximo de tokens a generar
            temperature: Temperatura de generación (0.0-1.0)
            context: Contexto de conversación previa (opcional)
            return_metrics: Si True, el último yield será un dict con métricas
        
        Yields:
            - Chunks de texto (str) durante el stream
            - Dict con métricas al final si return_metrics=True
        
        Raises:
            aiohttp.ClientError: Si hay error de conexión
            ValueError: Si hay error en la respuesta
        """
        start_time = time.time()
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if context:
            payload["context"] = context
        
        # Variables para acumular métricas
        total_chars = 0
        last_data = None
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                logger.info(f"Iniciando stream con {self.model_name} (max_tokens={max_tokens})")
                
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Error en Ollama stream: {resp.status} - {error_text}")
                        raise ValueError(f"Error en Ollama: {resp.status}")
                    
                    # Leer línea por línea (cada línea es un JSON)
                    async for line in resp.content:
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                
                                # Ollama retorna chunks en el campo "response"
                                if "response" in data:
                                    chunk = data["response"]
                                    if chunk:  # Solo yield si hay contenido
                                        total_chars += len(chunk)
                                        yield chunk
                                
                                # Verificar si es el último chunk (contiene métricas)
                                if data.get("done", False):
                                    last_data = data  # Guardar para métricas
                                    logger.info(f"Stream completado: {total_chars} caracteres")
                                    break
                                    
                            except json.JSONDecodeError:
                                logger.warning(f"No se pudo decodificar línea: {line}")
                                continue
                    
                    # Enviar métricas al final si se solicitaron
                    if return_metrics and last_data:
                        end_time = time.time()
                        metrics = {
                            "tokens_usados": last_data.get("eval_count", 0),
                            "tokens_prompt": last_data.get("prompt_eval_count", 0),
                            "tiempo_respuesta_ms": int((end_time - start_time) * 1000),
                            "modelo_usado": last_data.get("model", self.model_name),
                            "total_duration_ns": last_data.get("total_duration", 0),
                            "caracteres_generados": total_chars,
                        }
                        yield metrics  # Último yield es un dict con métricas
                    
        except ClientError as e:
            logger.error(f"Error de conexión con Ollama stream: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado en stream: {e}")
            raise
    
    async def chat(
        self,
        messages: list[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """
        Genera respuesta usando el endpoint de chat (formato OpenAI-like).
        
        Args:
            messages: Lista de mensajes [{role: "user/assistant/system", content: "..."}]
            max_tokens: Máximo de tokens a generar
            temperature: Temperatura de generación
        
        Returns:
            Respuesta del asistente
        """
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            }
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                logger.info(f"Chat con {len(messages)} mensajes")
                
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Error en Ollama chat: {resp.status} - {error_text}")
                        raise ValueError(f"Error en Ollama: {resp.status}")
                    
                    result = await resp.json()
                    message = result.get("message", {})
                    response_text = message.get("content", "")
                    
                    logger.info(f"Chat respuesta: {len(response_text)} caracteres")
                    return response_text
                    
        except ClientError as e:
            logger.error(f"Error de conexión con Ollama chat: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado en chat: {e}")
            raise
    
    async def chat_stream(
        self,
        messages: list[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Genera respuesta con streaming usando el endpoint de chat.
        
        Args:
            messages: Lista de mensajes [{role: "user/assistant/system", content: "..."}]
            max_tokens: Máximo de tokens a generar
            temperature: Temperatura de generación
        
        Yields:
            Chunks de texto de la respuesta
        """
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            }
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                logger.info(f"Chat stream con {len(messages)} mensajes")
                
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Error en Ollama chat stream: {resp.status} - {error_text}")
                        raise ValueError(f"Error en Ollama: {resp.status}")
                    
                    async for line in resp.content:
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                
                                # En chat, el contenido está en message.content
                                message = data.get("message", {})
                                chunk = message.get("content", "")
                                
                                if chunk:
                                    yield chunk
                                
                                if data.get("done", False):
                                    logger.info("Chat stream completado")
                                    break
                                    
                            except json.JSONDecodeError:
                                logger.warning(f"No se pudo decodificar línea: {line}")
                                continue
                    
        except ClientError as e:
            logger.error(f"Error de conexión con Ollama chat stream: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado en chat stream: {e}")
            raise


# ============================================
# SINGLETON PROVIDER
# ============================================

_ollama_provider: Optional[OllamaProvider] = None


def get_llm_provider() -> OllamaProvider:
    """
    Obtiene la instancia singleton del provider de LLM.
    
    Returns:
        Instancia de OllamaProvider
    """
    global _ollama_provider
    
    if _ollama_provider is None:
        _ollama_provider = OllamaProvider()
        logger.info("Instancia singleton de OllamaProvider creada")
    
    return _ollama_provider


def reset_llm_provider():
    """Resetea el provider (útil para testing)."""
    global _ollama_provider
    _ollama_provider = None
    logger.info("Provider de LLM reseteado")


# ============================================
# UTILIDADES
# ============================================

async def check_ollama_availability() -> bool:
    """
    Verifica que Ollama esté disponible y tenga modelos.
    
    Returns:
        True si Ollama está disponible, False en caso contrario
    """
    provider = get_llm_provider()
    
    # Check health
    if not await provider.health_check():
        logger.error("Ollama no está disponible")
        return False
    
    # Check models
    models = await provider.list_models()
    if not models:
        logger.error("No hay modelos disponibles en Ollama")
        return False
    
    logger.info(f"Ollama disponible con {len(models)} modelos")
    return True


async def ensure_model_available(model_name: str) -> bool:
    """
    Verifica que un modelo específico esté disponible.
    
    Args:
        model_name: Nombre del modelo a verificar
    
    Returns:
        True si el modelo está disponible
    """
    provider = get_llm_provider()
    models = await provider.list_models()
    
    available = model_name in models
    if available:
        logger.info(f"Modelo {model_name} disponible")
    else:
        logger.warning(f"Modelo {model_name} no disponible. Modelos: {models}")
    
    return available
