import httpx
import asyncio
from typing import List, Dict, Any, Optional
from ...domain.repositories.llm_service import LLMService
from ...domain.entities import LLMConfig, Analysis, Screen

class LLMServiceImpl(LLMService):
    def __init__(self):
        self.config = None
        self.provider = None
        self.api_key = None
        self.base_url = None
    
    async def initialize(self, config: LLMConfig) -> bool:
        """Inicializa el servicio LLM con la configuración"""
        try:
            self.config = config
            self.provider = config.provider
            self.api_key = config.api_key
            self.base_url = config.base_url
            return True
        except Exception as e:
            print(f"Error inicializando LLM service: {e}")
            return False
    
    async def get_embedding(self, text: str) -> List[float]:
        """Obtiene el embedding de un texto usando el proveedor configurado"""
        try:
            if not self.config:
                # Si no hay configuración, usar embedding simple
                return self._simple_embedding(text)
            
            if self.provider == 'openai':
                return await self._openai_embedding(text)
            elif self.provider == 'ollama':
                return await self._ollama_embedding(text)
            elif self.provider == 'mistral':
                return await self._mistral_embedding(text)
            else:
                # Fallback a embedding simple
                return self._simple_embedding(text)
        except Exception as e:
            print(f"Error obteniendo embedding: {e}")
            # Fallback a embedding simple
            return self._simple_embedding(text)
    
    def _simple_embedding(self, text: str) -> List[float]:
        """Embedding simple basado en hash para desarrollo/testing"""
        import hashlib
        # Crear un embedding simple basado en el hash del texto
        hash_obj = hashlib.sha256(text.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # Convertir el hash a una lista de floats (128 dimensiones)
        embedding = []
        for i in range(0, len(hash_hex), 2):
            if len(embedding) >= 128:
                break
            hex_pair = hash_hex[i:i+2]
            float_val = float(int(hex_pair, 16)) / 255.0  # Normalizar a [0,1]
            embedding.append(float_val)
        
        # Rellenar hasta 128 dimensiones si es necesario
        while len(embedding) < 128:
            embedding.append(0.0)
        
        return embedding[:128]
    
    async def _openai_embedding(self, text: str) -> List[float]:
        """Obtiene embedding usando OpenAI"""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://api.openai.com/v1/embeddings',
                    headers=headers,
                    json={'input': text, 'model': 'text-embedding-ada-002'},
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    return data['data'][0]['embedding']
                else:
                    raise Exception(f"OpenAI API error: {response.text}")
        except Exception as e:
            print(f"Error OpenAI embedding: {e}")
            return self._simple_embedding(text)
    
    async def _ollama_embedding(self, text: str) -> List[float]:
        """Obtiene embedding usando Ollama"""
        try:
            base_url = self.base_url or 'http://localhost:11434'
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{base_url}/api/embeddings',
                    json={'model': 'llama2', 'prompt': text},
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    return data['embedding']
                else:
                    raise Exception(f"Ollama API error: {response.text}")
        except Exception as e:
            print(f"Error Ollama embedding: {e}")
            return self._simple_embedding(text)
    
    async def _mistral_embedding(self, text: str) -> List[float]:
        """Obtiene embedding usando Mistral"""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://api.mistral.ai/v1/embeddings',
                    headers=headers,
                    json={'input': text, 'model': 'mistral-embed'},
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    return data['data'][0]['embedding']
                else:
                    raise Exception(f"Mistral API error: {response.text}")
        except Exception as e:
            print(f"Error Mistral embedding: {e}")
            return self._simple_embedding(text)
    
    # Métodos temporales para cumplir con la interfaz
    async def analyze_screen(self, screen: Screen, context: str) -> Analysis:
        """Analiza una pantalla NSDK y genera el análisis completo"""
        # TODO: Implementar análisis real
        return Analysis(
            id="temp",
            screen_id=screen.id,
            analysis_type="screen_analysis",
            content="Análisis temporal",
            metadata={}
        )
    
    async def generate_frontend_code(self, analysis: Analysis, existing_code: str) -> str:
        """Genera código Angular basado en el análisis"""
        # TODO: Implementar generación real
        return "// Código Angular temporal"
    
    async def generate_backend_code(self, analysis: Analysis, existing_code: str) -> str:
        """Genera código Spring Boot basado en el análisis"""
        # TODO: Implementar generación real
        return "// Código Spring Boot temporal"
    
    async def generate_api_spec(self, analysis: Analysis) -> str:
        """Genera especificación OpenAPI basada en el análisis"""
        # TODO: Implementar generación real
        return "# OpenAPI spec temporal"
    
    async def summarize_module(self, screens: List[Screen]) -> str:
        """Genera un resumen de un módulo basado en sus pantallas"""
        # TODO: Implementar resumen real
        return "Resumen temporal del módulo"
    
    async def validate_configuration(self) -> bool:
        """Valida si la configuración del LLM es correcta"""
        return self.test_connection(self.config.__dict__ if self.config else {})[0]
    
    async def chat_completion(self, messages: List[Dict[str, str]], 
                            system_prompt: Optional[str] = None) -> str:
        """Realiza una completación de chat genérica"""
        # TODO: Implementar chat real con proveedores LLM
        # Por ahora, devolver una respuesta JSON válida temporal
        return '''{
    "analysis_summary": "Análisis automático de pantalla .SCR - Pantalla de alta de usuarios con campos de formulario y botones de acción",
    "file_type": "screen",
    "complexity": "medium",
    "estimated_hours": "8",
    "frontend": {
        "screen_type": "form",
        "title": "Alta de Usuarios",
        "fields": [
            {
                "name": "nombre",
                "type": "text",
                "required": true,
                "validation": "Campo obligatorio"
            },
            {
                "name": "email",
                "type": "text",
                "required": true,
                "validation": "Formato de email válido"
            }
        ],
        "buttons": [
            {
                "name": "guardar",
                "action": "save",
                "description": "Guardar usuario"
            },
            {
                "name": "cancelar",
                "action": "cancel",
                "description": "Cancelar operación"
            }
        ],
        "angular_components": ["MatFormField", "MatButton", "MatInput"],
        "routing": "/usuarios/alta",
        "dependencies": ["@angular/forms", "@angular/material"]
    },
    "backend": {
        "entity_name": "Usuario",
        "database_table": "usuarios",
        "fields": [
            {
                "name": "nombre",
                "java_type": "String",
                "jpa_annotations": ["@Column", "@NotNull"],
                "database_type": "VARCHAR(255)"
            },
            {
                "name": "email",
                "java_type": "String",
                "jpa_annotations": ["@Column", "@NotNull", "@Email"],
                "database_type": "VARCHAR(255)"
            }
        ],
        "endpoints": [
            {
                "method": "POST",
                "path": "/api/usuarios",
                "description": "Crear nuevo usuario"
            }
        ],
        "business_logic": "Validación de datos de usuario y persistencia en base de datos",
        "spring_annotations": ["@RestController", "@Service", "@Repository"]
    },
    "migration_notes": [
        "Implementar validaciones de frontend con Angular Reactive Forms",
        "Configurar CORS para comunicación frontend-backend",
        "Implementar manejo de errores en ambos lados"
    ],
    "potential_issues": [
        "Verificar compatibilidad de tipos de datos entre NSDK y Java",
        "Considerar migración de reglas de negocio existentes",
        "Validar permisos y seguridad en la nueva implementación"
    ]
}'''
    
    @staticmethod
    def test_connection(config: dict) -> (bool, str):
        provider = config.get('provider')
        if provider == 'openai':
            api_key = config.get('apiKey')
            if not api_key:
                return False, 'API Key no especificada'
            try:
                headers = {'Authorization': f'Bearer {api_key}'}
                resp = httpx.get('https://api.openai.com/v1/models', headers=headers, timeout=5)
                if resp.status_code == 200:
                    return True, 'Conexión exitosa a OpenAI'
                else:
                    return False, f'Error OpenAI: {resp.text}'
            except Exception as e:
                return False, f'Error de conexión OpenAI: {str(e)}'
        elif provider == 'ollama':
            base_url = config.get('baseUrl', 'http://localhost:11434')
            try:
                resp = httpx.get(f'{base_url}/api/tags', timeout=5)
                if resp.status_code == 200:
                    return True, 'Conexión exitosa a Ollama'
                else:
                    return False, f'Error Ollama: {resp.text}'
            except Exception as e:
                return False, f'Error de conexión Ollama: {str(e)}'
        elif provider == 'mistral':
            api_key = config.get('apiKey')
            if not api_key:
                return False, 'API Key no especificada'
            try:
                headers = {'Authorization': f'Bearer {api_key}'}
                resp = httpx.get('https://api.mistral.ai/v1/models', headers=headers, timeout=5)
                if resp.status_code == 200:
                    return True, 'Conexión exitosa a Mistral'
                else:
                    return False, f'Error Mistral: {resp.text}'
            except Exception as e:
                return False, f'Error de conexión Mistral: {str(e)}'
        else:
            return False, 'Proveedor LLM no soportado o no especificado' 