from typing import Dict, Any, Optional, List
import logging
import re
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
            logger.info(f"Prompt creado: {len(analysis_prompt)} caracteres")
            
            # 3. Enviar a la IA para análisis
            logger.info("Enviando a OpenAI...")
            ai_response = await self.llm_service.chat_completion([
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": analysis_prompt}
            ])
            logger.info(f"Respuesta de OpenAI recibida: {len(ai_response)} caracteres")
            
            # 4. Procesar respuesta de la IA
            logger.info("Procesando respuesta...")
            analysis_result = self._process_ai_response(ai_response, file_name)
            logger.info(f"Análisis procesado: {list(analysis_result.keys())}")
            
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

**IMPORTANTE:** Presta especial atención a:
1. **Menú Superior:** Identifica el menú de navegación principal en la parte superior de la pantalla, opciones del menú, submenús, etc.
2. **Tablas:** Identifica TODAS las tablas, sus columnas, tipos de datos, y funcionalidades (ordenamiento, filtrado, paginación)
3. **Navegaciones:** Identifica todas las navegaciones entre pantallas, botones que cambian de pantalla, enlaces, etc.
4. **Flujo de navegación:** Describe cómo el usuario navega por la aplicación
5. **Parámetros de navegación:** Qué datos se pasan entre pantallas
6. **Condiciones de navegación:** Si hay validaciones antes de navegar
7. **Campos, validaciones, botones y lógica de negocio**

**DETECCIÓN DE MENÚS:** Busca patrones como: MENU, MENUBAR, NAVBAR, HEADER, TOP_MENU, MAIN_MENU, etc.
**DETECCIÓN DE TABLAS:** Busca patrones como: TABLE, GRID, LIST, DATAGRID, COLUMN, HEADER, etc.

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
        "tables": [
            {{
                "name": "nombre_tabla",
                "description": "descripción de la tabla",
                "columns": [
                    {{
                        "name": "nombre_columna",
                        "type": "text|number|date|boolean|etc",
                        "width": "ancho de la columna",
                        "sortable": true|false,
                        "filterable": true|false,
                        "description": "descripción de la columna"
                    }}
                ],
                "actions": ["editar", "eliminar", "ver_detalle", "etc"],
                "pagination": true|false,
                "search": true|false
            }}
        ],
        "navigations": [
            {{
                "trigger": "botón|enlace|evento",
                "destination": "nombre_pantalla_destino",
                "condition": "condición de navegación (si existe)",
                "parameters": ["parametros que se pasan"],
                "description": "descripción de la navegación"
            }}
        ],
        "angular_components": ["MatFormField", "MatButton", "MatTable", "etc"],
        "routing": "ruta sugerida para Angular",
        "dependencies": ["@angular/forms", "@angular/material", "etc"],
        "navigation_flow": "descripción del flujo de navegación completo",
        "top_menu": {{
            "menu_items": [
                {{
                    "name": "nombre_opcion_menu",
                    "label": "etiqueta visible",
                    "action": "navegación|submenu|acción",
                    "destination": "pantalla_destino",
                    "submenu": [
                        {{
                            "name": "submenu_item",
                            "label": "etiqueta submenu",
                            "action": "navegación|acción",
                            "destination": "pantalla_destino"
                        }}
                    ]
                }}
            ],
            "position": "top|header|navigation_bar",
            "style": "horizontal|vertical|dropdown"
        }}
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
        "related_tables": [
            {{
                "table_name": "nombre_tabla_relacionada",
                "relationship": "one_to_many|many_to_one|many_to_many",
                "description": "descripción de la relación",
                "columns": [
                    {{
                        "name": "nombre_columna",
                        "type": "String|Integer|Date|etc",
                        "description": "descripción de la columna"
                    }}
                ]
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

**ANÁLISIS CRÍTICO REQUERIDO:**
1. **Menú Superior:** Identifica el menú principal de navegación en la parte superior, opciones, submenús, estructura jerárquica
2. **Tablas:** Identifica TODAS las tablas, sus columnas, tipos de datos, y funcionalidades
3. **Navegaciones:** Identifica TODAS las navegaciones entre pantallas, botones de navegación, enlaces, etc.
4. **Flujo de usuario:** Describe cómo el usuario navega por la aplicación
5. **Parámetros de navegación:** Qué datos se pasan entre pantallas
6. **Condiciones de navegación:** Validaciones antes de navegar
7. **Campos, validaciones, botones y lógica de negocio**

**PATRONES A BUSCAR:**
- Menús: MENU, MENUBAR, NAVBAR, HEADER, TOP_MENU, MAIN_MENU, SUBMENU, etc.
- Navegación: CALL, GOTO, NAVIGATE, TRANSFER, etc.
- Tablas: TABLE, GRID, LIST, DATAGRID, COLUMN, HEADER, ROW, etc.
"""
    
    def _process_ai_response(self, ai_response: str, file_name: str) -> Dict[str, Any]:
        """Procesa la respuesta de la IA y la estructura"""
        try:
            import json
            import re
            
            logger.info(f"Intentando parsear JSON de {len(ai_response)} caracteres")
            logger.info(f"Primeros 200 caracteres: {ai_response[:200]}")
            
            # Limpiar la respuesta - extraer solo el JSON
            cleaned_response = self._extract_json_from_response(ai_response)
            logger.info(f"Respuesta limpiada: {len(cleaned_response)} caracteres")
            
            # Intentar parsear como JSON
            analysis_data = json.loads(cleaned_response)
            logger.info(f"JSON parseado exitosamente. Claves: {list(analysis_data.keys())}")
            
            # Agregar metadatos adicionales
            analysis_data["file_name"] = file_name
            analysis_data["analysis_timestamp"] = self._get_current_timestamp()
            analysis_data["analysis_version"] = "1.0"
            
            return analysis_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando respuesta JSON de IA: {str(e)}")
            logger.error(f"Respuesta completa: {ai_response}")
            
            # Intentar reparar JSON incompleto
            try:
                repaired_json = self._repair_incomplete_json(ai_response)
                if repaired_json:
                    analysis_data = json.loads(repaired_json)
                    analysis_data["file_name"] = file_name
                    analysis_data["analysis_timestamp"] = self._get_current_timestamp()
                    analysis_data["analysis_version"] = "1.0"
                    logger.info("JSON reparado exitosamente")
                    return analysis_data
            except Exception as repair_error:
                logger.error(f"Error reparando JSON: {str(repair_error)}")
            
            # Crear respuesta de fallback
            return {
                "file_name": file_name,
                "analysis_summary": "Error en el análisis automático",
                "error": "No se pudo procesar la respuesta de la IA",
                "raw_response": ai_response[:500],
                "analysis_timestamp": self._get_current_timestamp(),
                "analysis_version": "1.0"
            }
    
    def _extract_json_from_response(self, response: str) -> str:
        """Extrae el JSON de la respuesta de la IA"""
        # Buscar JSON entre backticks
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Buscar JSON sin backticks
        json_match = re.search(r'(\{.*\})', response, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Si no encuentra JSON, devolver la respuesta completa
        return response
    
    def _repair_incomplete_json(self, response: str) -> str:
        """Intenta reparar JSON incompleto"""
        try:
            # Extraer el JSON
            json_str = self._extract_json_from_response(response)
            
            # Si el JSON termina abruptamente en un array o objeto, completarlo
            if json_str.strip().endswith(','):
                json_str = json_str.rstrip(',')
            
            # Buscar el último objeto completo
            last_complete_brace = json_str.rfind('}')
            if last_complete_brace > 0:
                # Verificar si hay arrays abiertos antes del último }
                before_last_brace = json_str[:last_complete_brace]
                open_brackets = before_last_brace.count('[')
                close_brackets = before_last_brace.count(']')
                
                # Cerrar arrays abiertos
                while close_brackets < open_brackets:
                    json_str = json_str[:last_complete_brace] + ']' + json_str[last_complete_brace:]
                    close_brackets += 1
                    last_complete_brace += 1
            
            # Contar llaves abiertas y cerradas
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            
            # Cerrar llaves faltantes
            while close_braces < open_braces:
                json_str += '}'
                close_braces += 1
            
            # Si hay comas al final, quitarlas
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
            
            # Verificar que el JSON sea válido
            import json
            json.loads(json_str)  # Test parse
            
            logger.info(f"JSON reparado exitosamente: {len(json_str)} caracteres")
            return json_str
            
        except Exception as e:
            logger.error(f"Error reparando JSON: {str(e)}")
            return None
    
    def _get_current_timestamp(self) -> str:
        """Obtiene timestamp actual en formato ISO"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
