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
            self.provider = config.provider.value  # Usar el valor del enum
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
                    json={'input': text, 'model': 'text-embedding-3-small'},
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
        try:
            if not self.config:
                raise Exception("LLM service no inicializado con configuración")
            
            if self.provider == 'openai':
                return await self._openai_chat_completion(messages, system_prompt)
            elif self.provider == 'ollama':
                return await self._ollama_chat_completion(messages, system_prompt)
            elif self.provider == 'mistral':
                return await self._mistral_chat_completion(messages, system_prompt)
            else:
                raise Exception(f"Proveedor LLM no soportado: {self.provider}")
                
        except Exception as e:
            print(f"Error en chat completion: {e}")
            print(f"Provider: {self.provider}")
            print(f"Config: {self.config}")
            print(f"API Key: {'Set' if self.api_key else 'Not set'}")
            # Fallback a respuesta temporal si hay error
            return '''{
    "analysis_summary": "Error en análisis automático - Fallback temporal",
    "file_type": "screen",
    "complexity": "unknown",
    "estimated_hours": "0",
    "frontend": {},
    "backend": {},
    "migration_notes": ["Error en análisis automático"],
    "potential_issues": ["Error en análisis automático"]
}'''
    
    async def _openai_chat_completion(self, messages: List[Dict[str, str]], 
                                    system_prompt: Optional[str] = None) -> str:
        """Realiza completación de chat usando OpenAI"""
        try:
            # Preparar mensajes para OpenAI
            openai_messages = []
            if system_prompt:
                openai_messages.append({"role": "system", "content": system_prompt})
            openai_messages.extend(messages)
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.config.model_name if hasattr(self.config, 'model_name') else 'gpt-4',
                'messages': openai_messages,
                'max_tokens': self.config.max_tokens if hasattr(self.config, 'max_tokens') else 4096,
                'temperature': self.config.temperature if hasattr(self.config, 'temperature') else 0.7
            }
            
            # Log de entrada
            print("=== OPENAI REQUEST ===")
            print(f"Model: {payload['model']}")
            print(f"Max tokens: {payload['max_tokens']}")
            print(f"Temperature: {payload['temperature']}")
            print("Messages:")
            for i, msg in enumerate(openai_messages):
                print(f"  {i+1}. Role: {msg['role']}")
                print(f"     Content: {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}")
            print("=====================")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data['choices'][0]['message']['content']
                    
                    # Log de salida
                    print("=== OPENAI RESPONSE ===")
                    print(f"Status: {response.status_code}")
                    print(f"Usage: {data.get('usage', 'N/A')}")
                    print(f"Content length: {len(content)}")
                    print(f"Content: {content[:500]}{'...' if len(content) > 500 else ''}")
                    print("======================")
                    
                    return content
                else:
                    print(f"=== OPENAI ERROR ===")
                    print(f"Status: {response.status_code}")
                    print(f"Response: {response.text}")
                    print("===================")
                    raise Exception(f"OpenAI API error: {response.text}")
                    
        except Exception as e:
            print(f"Error OpenAI chat completion: {e}")
            raise
    
    async def _ollama_chat_completion(self, messages: List[Dict[str, str]], 
                                    system_prompt: Optional[str] = None) -> str:
        """Realiza completación de chat usando Ollama"""
        try:
            base_url = self.base_url or 'http://localhost:11434'
            
            # Preparar mensajes para Ollama
            ollama_messages = []
            if system_prompt:
                ollama_messages.append({"role": "system", "content": system_prompt})
            ollama_messages.extend(messages)
            
            payload = {
                'model': 'llama2',
                'messages': ollama_messages,
                'stream': False
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{base_url}/api/chat',
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['message']['content']
                else:
                    raise Exception(f"Ollama API error: {response.text}")
                    
        except Exception as e:
            print(f"Error Ollama chat completion: {e}")
            raise
    
    async def _mistral_chat_completion(self, messages: List[Dict[str, str]], 
                                     system_prompt: Optional[str] = None) -> str:
        """Realiza completación de chat usando Mistral"""
        try:
            # Preparar mensajes para Mistral
            mistral_messages = []
            if system_prompt:
                mistral_messages.append({"role": "system", "content": system_prompt})
            mistral_messages.extend(messages)
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'mistral-large-latest',
                'messages': mistral_messages,
                'max_tokens': 4096,
                'temperature': 0.7
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://api.mistral.ai/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content']
                else:
                    raise Exception(f"Mistral API error: {response.text}")
                    
        except Exception as e:
            print(f"Error Mistral chat completion: {e}")
            raise
    
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