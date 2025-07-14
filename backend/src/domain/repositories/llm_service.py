from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..entities import LLMConfig, Analysis, Screen

class LLMService(ABC):
    """Puerto (interface) para servicios de LLM"""
    
    @abstractmethod
    async def initialize(self, config: LLMConfig) -> bool:
        """Inicializa el servicio LLM con la configuración"""
        pass
    
    @abstractmethod
    async def analyze_screen(self, screen: Screen, context: str) -> Analysis:
        """Analiza una pantalla NSDK y genera el análisis completo"""
        pass
    
    @abstractmethod
    async def generate_frontend_code(self, analysis: Analysis, existing_code: str) -> str:
        """Genera código Angular basado en el análisis"""
        pass
    
    @abstractmethod
    async def generate_backend_code(self, analysis: Analysis, existing_code: str) -> str:
        """Genera código Spring Boot basado en el análisis"""
        pass
    
    @abstractmethod
    async def generate_api_spec(self, analysis: Analysis) -> str:
        """Genera especificación OpenAPI basada en el análisis"""
        pass
    
    @abstractmethod
    async def summarize_module(self, screens: List[Screen]) -> str:
        """Genera un resumen de un módulo basado en sus pantallas"""
        pass
    
    @abstractmethod
    async def validate_configuration(self) -> bool:
        """Valida si la configuración del LLM es correcta"""
        pass
    
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Obtiene el embedding de un texto"""
        pass
    
    @abstractmethod
    async def chat_completion(self, messages: List[Dict[str, str]], 
                            system_prompt: Optional[str] = None) -> str:
        """Realiza una completación de chat genérica"""
        pass