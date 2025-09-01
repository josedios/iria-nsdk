from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
from ..use_cases.vectorization_use_case import VectorizationUseCase
from ...infrastructure.services.llm_service_impl import LLMServiceImpl
from ...infrastructure.services.vector_store_service_impl import VectorStoreServiceImpl

logger = logging.getLogger(__name__)

class AIAnalysisService:
    """Servicio para análisis de ficheros .SCR con IA"""
    
    def __init__(self, vectorization_use_case: VectorizationUseCase, llm_service: LLMServiceImpl):
        self.vectorization_use_case = vectorization_use_case
        self.llm_service = llm_service
    
    async def analyze_scr_file(
        self, 
        file_path: str, 
        file_content: str, 
        file_name: str
    ) -> Dict[str, Any]:
        """
        Analiza un fichero .SCR para migración a Angular/Spring Boot
        
        Args:
            file_path: Ruta completa del fichero
            file_content: Contenido del fichero .SCR
            file_name: Nombre del fichero
            
        Returns:
            Dict con el análisis completo del fichero
        """
        try:
            logger.info(f"Iniciando análisis IA para {file_name}")
            
            # 1. Buscar código similar vectorizado para contexto
            similar_code_context = await self._get_similar_code_context(file_content)
            
            # 2. Crear el prompt para análisis
            analysis_prompt = self._create_analysis_prompt(
                file_name, file_content, similar_code_context
            )
            
            # 3. Enviar a la IA para análisis
            ai_response = await self.llm_service.chat_completion([
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": analysis_prompt}
            ])
            
            # 4. Procesar respuesta de la IA
            analysis_result = self._process_ai_response(ai_response, file_name)
            
            logger.info(f"Análisis IA completado para {file_name}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error en análisis IA para {file_name}: {str(e)}")
            raise
    
    async def _get_similar_code_context(self, file_content: str) -> List[Dict[str, Any]]:
        """Busca código similar vectorizado para proporcionar contexto"""
        try:
            # Extraer fragmentos clave del fichero .SCR para búsqueda
            search_queries = self._extract_search_queries_from_scr(file_content)
            
            similar_code = []
            for query in search_queries[:3]:  # Limitar a 3 búsquedas
                results = await self.vectorization_use_case.search_similar_code(
                    query=query,
                    limit=2
                )
                similar_code.extend(results)
            
            return similar_code[:5]  # Máximo 5 ejemplos de contexto
            
        except Exception as e:
            logger.warning(f"Error obteniendo contexto vectorizado: {str(e)}")
            return []
    
    def _extract_search_queries_from_scr(self, scr_content: str) -> List[str]:
        """Extrae consultas de búsqueda relevantes del contenido .SCR"""
        queries = []
        
        # Buscar patrones comunes en ficheros .SCR
        lines = scr_content.split('\n')
        
        for line in lines[:20]:  # Analizar las primeras 20 líneas
            line = line.strip()
            if line:
                # Agregar líneas que parecen definiciones importantes
                if any(keyword in line.upper() for keyword in [
                    'SCREEN', 'FORM', 'FIELD', 'BUTTON', 'TABLE', 'QUERY', 'PROCEDURE'
                ]):
                    queries.append(line[:100])  # Limitar longitud
        
        # Si no encontramos patrones específicos, usar las primeras líneas
        if not queries:
            queries = [line.strip()[:100] for line in lines[:5] if line.strip()]
        
        return queries
    
    def _create_analysis_prompt(
        self, 
        file_name: str, 
        file_content: str, 
        similar_code: List[Dict[str, Any]]
    ) -> str:
        """Crea el prompt para el análisis con IA"""
        
        context_section = ""
        if similar_code:
            context_section = "\n\n## CÓDIGO SIMILAR VECTORIZADO (para contexto):\n"
            for i, code in enumerate(similar_code, 1):
                context_section += f"\n### Ejemplo {i}:\n"
                context_section += f"Archivo: {code.get('file_path', 'N/A')}\n"
                context_section += f"Contenido: {code.get('content', 'N/A')[:300]}...\n"
        
        prompt = f"""
# ANÁLISIS DE MIGRACIÓN DE FICHERO .SCR A ANGULAR/SPRING BOOT

## FICHERO A ANALIZAR:
**Nombre:** {file_name}

**Contenido del fichero .SCR:**
```
{file_content[:2000]}{"..." if len(file_content) > 2000 else ""}
```

{context_section}

## INSTRUCCIONES:
Analiza este fichero .SCR y proporciona un análisis detallado para su migración a:
- **Frontend:** Angular con Angular Material
- **Backend:** Java Spring Boot con JPA/Hibernate

## ESTRUCTURA DE RESPUESTA REQUERIDA (JSON):
```json
{{
    "analysis_summary": "Resumen del análisis en español",
    "file_type": "screen|form|report|utility",
    "complexity": "low|medium|high",
    "estimated_hours": number,
    "frontend": {{
        "component_type": "form|list|detail|dashboard",
        "fields": [
            {{
                "name": "nombre_campo",
                "type": "text|number|date|select|checkbox",
                "required": true|false,
                "validation": "descripción de validaciones"
            }}
        ],
        "buttons": [
            {{
                "name": "nombre_boton",
                "action": "save|cancel|search|delete|custom",
                "description": "descripción de la acción"
            }}
        ],
        "angular_components": ["MatFormField", "MatButton", "MatTable", "etc"],
        "routing": "ruta sugerida para Angular",
        "dependencies": ["@angular/forms", "@angular/material", "etc"]
    }},
    "backend": {{
        "entity_name": "nombre de la entidad JPA",
        "database_table": "nombre_tabla_sugerido",
        "fields": [
            {{
                "name": "nombreCampo",
                "java_type": "String|Integer|LocalDate|Boolean|etc",
                "jpa_annotations": ["@Column", "@NotNull", "etc"],
                "database_type": "VARCHAR(255)|INT|DATE|etc"
            }}
        ],
        "endpoints": [
            {{
                "method": "GET|POST|PUT|DELETE",
                "path": "/api/ruta",
                "description": "descripción del endpoint"
            }}
        ],
        "business_logic": "descripción de la lógica de negocio identificada",
        "spring_annotations": ["@RestController", "@Service", "@Repository", "etc"]
    }},
    "migration_notes": [
        "Nota importante 1",
        "Nota importante 2"
    ],
    "potential_issues": [
        "Posible problema 1",
        "Posible problema 2"
    ]
}}
```

Responde ÚNICAMENTE con el JSON válido, sin texto adicional.
"""
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Prompt del sistema para configurar el comportamiento de la IA"""
        return """
Eres un experto en migración de aplicaciones legacy a tecnologías modernas, especializado en:
- Análisis de ficheros .SCR (screens/formularios legacy)
- Migración a Angular con Angular Material
- Migración a Java Spring Boot con JPA/Hibernate
- Arquitecturas REST API modernas

Tu tarea es analizar ficheros .SCR y proporcionar análisis detallados para su migración.
Siempre responde en formato JSON válido y en español.
Sé preciso en las estimaciones de complejidad y horas.
Identifica todos los campos, validaciones, botones y lógica de negocio.
"""
    
    def _process_ai_response(self, ai_response: str, file_name: str) -> Dict[str, Any]:
        """Procesa la respuesta de la IA y la estructura"""
        try:
            import json
            
            # Intentar parsear como JSON
            analysis_data = json.loads(ai_response)
            
            # Agregar metadatos adicionales
            analysis_data["file_name"] = file_name
            analysis_data["analysis_timestamp"] = self._get_current_timestamp()
            analysis_data["analysis_version"] = "1.0"
            
            return analysis_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando respuesta JSON de IA: {str(e)}")
            # Crear respuesta de fallback
            return {
                "file_name": file_name,
                "analysis_summary": "Error en el análisis automático",
                "error": "No se pudo procesar la respuesta de la IA",
                "raw_response": ai_response[:500],
                "analysis_timestamp": self._get_current_timestamp(),
                "analysis_version": "1.0"
            }
    
    def _get_current_timestamp(self) -> str:
        """Obtiene timestamp actual en formato ISO"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
