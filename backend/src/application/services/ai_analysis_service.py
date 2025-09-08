from typing import Dict, Any, Optional, List
import logging
import re
from pathlib import Path
from ..use_cases.vectorization_use_case import VectorizationUseCase
from ...infrastructure.services.llm_service_impl import LLMServiceImpl
from ...infrastructure.services.vector_store_service_impl import VectorStoreServiceImpl
from .nsdk_query_service import NSDKQueryService

logger = logging.getLogger(__name__)

class AIAnalysisService:
    """Servicio para análisis de ficheros .SCR con IA"""
    
    def __init__(self, vectorization_use_case: VectorizationUseCase, llm_service: LLMServiceImpl, nsdk_query_service: NSDKQueryService = None):
        self.vectorization_use_case = vectorization_use_case
        self.llm_service = llm_service
        self.nsdk_query_service = nsdk_query_service
    
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
            logger.info("1. Buscando código similar vectorizado...")
            similar_code_context = await self._get_similar_code_context(file_content)
            logger.info(f"Contexto de código similar obtenido: {len(similar_code_context)} elementos")
            if similar_code_context:
                for i, ctx in enumerate(similar_code_context):
                    logger.info(f"  Similar {i+1}: {ctx.get('file_path', 'N/A')} - {len(str(ctx.get('content', '')))} chars")
            
            # 2. Consultar documentación NSDK para contexto técnico
            logger.info("2. Consultando documentación NSDK...")
            nsdk_context = await self._get_nsdk_documentation_context(file_content)
            logger.info(f"Contexto NSDK obtenido: {len(nsdk_context)} caracteres")
            if nsdk_context:
                logger.info(f"Contexto NSDK preview: {nsdk_context[:300]}...")
            
            # 3. Crear el prompt para análisis
            analysis_prompt = self._create_analysis_prompt(
                file_name, file_content, similar_code_context, nsdk_context
            )
            logger.info(f"Prompt creado: {len(analysis_prompt)} caracteres")
            
            # 3.1. Verificar si el prompt es demasiado largo y optimizar si es necesario
            # Para GPT-5, permitir prompts mucho más largos (archivo completo)
            is_gpt5 = hasattr(self.llm_service, 'config') and self.llm_service.config and getattr(self.llm_service.config, 'model_name', '').lower() == 'gpt-5'
            max_prompt_length = 50000 if is_gpt5 else 6000  # GPT-5 puede manejar archivos completos
            
            if len(analysis_prompt) > max_prompt_length:
                logger.warning(f"Prompt muy largo ({len(analysis_prompt)} chars), optimizando...")
                analysis_prompt = self._optimize_prompt_for_tokens(
                    file_name, file_content, similar_code_context, nsdk_context
                )
                logger.info(f"Prompt optimizado: {len(analysis_prompt)} caracteres")
            
            # 4. Enviar a la IA para análisis
            logger.info("Enviando a OpenAI...")
            
            # Detectar si es GPT-5 y usar prompt especializado
            is_gpt5 = hasattr(self.llm_service, 'config') and self.llm_service.config and getattr(self.llm_service.config, 'model_name', '').lower() == 'gpt-5'
            
            if is_gpt5:
                logger.info("Usando prompt especializado para GPT-5")
                system_prompt = self._get_gpt5_system_prompt()
            else:
                system_prompt = self._get_system_prompt()
            
            logger.info(f"System prompt: {system_prompt[:200]}...")
            logger.info(f"User prompt length: {len(analysis_prompt)} caracteres")
            logger.info(f"User prompt preview: {analysis_prompt[:500]}...")
            
            ai_response = await self.llm_service.chat_completion([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": analysis_prompt}
            ])
            
            logger.info(f"=== RESPUESTA COMPLETA DE OPENAI ===")
            logger.info(f"Longitud total: {len(ai_response)} caracteres")
            logger.info(f"Respuesta completa:\n{ai_response}")
            logger.info(f"=== FIN RESPUESTA OPENAI ===")
            
            # 5. Procesar respuesta de la IA
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
    
    async def _get_nsdk_documentation_context(self, file_content: str) -> str:
        """Obtiene contexto de la documentación NSDK para elementos específicos"""
        if not self.nsdk_query_service:
            return ""
        
        try:
            # Extraer términos técnicos del contenido del archivo
            technical_terms = self._extract_technical_terms(file_content)
            logger.info(f"Términos técnicos extraídos: {technical_terms}")
            
            if not technical_terms:
                logger.info("No se encontraron términos técnicos en el archivo")
                return ""
            
            # Consultar documentación para cada término
            context_parts = []
            for term in technical_terms[:3]:  # Limitar a 3 consultas
                try:
                    result = await self.nsdk_query_service.query_documentation(term)
                    if result and "Información encontrada" in result:
                        # Truncar resultado para ahorrar tokens
                        truncated_result = result[:300] + "..." if len(result) > 300 else result
                        context_parts.append(f"**{term}:** {truncated_result}")
                except Exception as e:
                    logger.warning(f"Error consultando documentación para '{term}': {e}")
                    continue
            
            if context_parts:
                return "\n\n## DOCUMENTACIÓN NSDK:\n" + "\n".join(context_parts)
            
            return ""
            
        except Exception as e:
            logger.error(f"Error obteniendo contexto NSDK: {e}")
            return ""
    
    def _extract_technical_terms(self, file_content: str) -> List[str]:
        """Extrae términos técnicos del contenido del archivo"""
        terms = []
        
        # Patrones comunes en archivos .SCR
        patterns = [
            r'DEFINE\s+(\w+)',  # Definiciones
            r'CALL\s+(\w+)',    # Llamadas a funciones
            r'USE\s+(\w+)',     # Uso de módulos
            r'INCLUDE\s+(\w+)', # Inclusión de archivos
            r'(\w+)\s*\(',      # Funciones
            r'(\w+)\s*:',       # Etiquetas
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, file_content, re.IGNORECASE)
            terms.extend(matches)
        
        # Filtrar términos comunes y duplicados
        common_terms = {'if', 'then', 'else', 'end', 'begin', 'var', 'const', 'type', 'function', 'procedure'}
        unique_terms = list(set([term.lower() for term in terms if term.lower() not in common_terms and len(term) > 2]))
        
        return unique_terms[:5]  # Limitar a 5 términos para ahorrar tokens
    
    def _optimize_prompt_for_tokens(
        self, 
        file_name: str, 
        file_content: str, 
        similar_code: List[Dict[str, Any]],
        nsdk_context: str = ""
    ) -> str:
        """Optimiza el prompt para que quepa en el límite de tokens manteniendo la calidad"""
        
        # Reducir contexto de código similar
        optimized_context = ""
        if similar_code:
            optimized_context = "\n\n## CÓDIGO SIMILAR:\n"
            for i, code in enumerate(similar_code[:1], 1):  # Solo 1 ejemplo
                optimized_context += f"\n**Ejemplo:** {code.get('file_path', 'N/A')}\n"
                optimized_context += f"{code.get('content', 'N/A')[:150]}...\n"
        
        # Reducir contexto NSDK
        if nsdk_context:
            # Truncar contexto NSDK más agresivamente
            truncated_nsdk = nsdk_context[:400] + "..." if len(nsdk_context) > 400 else nsdk_context
            optimized_context += f"\n\n## DOCUMENTACIÓN NSDK:\n{truncated_nsdk}"
        
        # Prompt optimizado pero completo
        prompt = f"""
# ANÁLISIS DETALLADO DE MIGRACIÓN .SCR A ANGULAR/SPRING BOOT

## FICHERO: {file_name}
```
{file_content[:1600]}{"..." if len(file_content) > 1600 else ""}
```

{optimized_context}

## INSTRUCCIONES CRÍTICAS:
Analiza COMPLETAMENTE este fichero .SCR para migración a Angular/Spring Boot.

**ANÁLISIS EXHAUSTIVO REQUERIDO:**
1. **MENÚ SUPERIOR:** Identifica TODOS los menús, submenús, opciones de navegación principal
2. **TABLAS:** Identifica TODAS las tablas, sus columnas, tipos de datos, funcionalidades
3. **NAVEGACIONES:** Identifica TODAS las navegaciones entre pantallas, botones de navegación
4. **CAMPOS:** Identifica TODOS los campos, sus tipos, validaciones, propiedades
5. **BOTONES:** Identifica TODOS los botones, sus acciones, funcionalidades
6. **FLUJO DE NAVEGACIÓN:** Describe el flujo completo de navegación del usuario

**PATRONES CRÍTICOS A BUSCAR:**
- Menús: MENU, MENUBAR, NAVBAR, HEADER, TOP_MENU, MAIN_MENU, SUBMENU
- Tablas: TABLE, GRID, LIST, DATAGRID, COLUMN, HEADER, ROW, CELL
- Navegación: CALL, GOTO, NAVIGATE, TRANSFER, LINK, BUTTON
- Campos: FIELD, INPUT, COMBOBOX, LISTBOX, CHECKBOX, RADIO
- Validaciones: VALIDATE, CHECK, REQUIRE, MANDATORY

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
    
    def _create_analysis_prompt(
        self, 
        file_name: str, 
        file_content: str, 
        similar_code: List[Dict[str, Any]],
        nsdk_context: str = ""
    ) -> str:
        """Crea el prompt para el análisis con IA"""
        
        context_section = ""
        if similar_code:
            context_section = "\n\n## CÓDIGO SIMILAR:\n"
            for i, code in enumerate(similar_code[:2], 1):  # Solo 2 ejemplos
                context_section += f"\n**Ejemplo {i}:** {code.get('file_path', 'N/A')}\n"
                context_section += f"{code.get('content', 'N/A')[:200]}...\n"
        
        # Agregar contexto NSDK si está disponible
        if nsdk_context:
            context_section += nsdk_context
        
        # Detectar si es GPT-5 para usar más contexto
        is_gpt5 = hasattr(self.llm_service, 'config') and self.llm_service.config and getattr(self.llm_service.config, 'model_name', '').lower() == 'gpt-5'
        
        # Para GPT-5: archivo completo, para otros modelos: límite
        if is_gpt5:
            content_length = len(file_content)  # Archivo completo para GPT-5
            logger.info(f"GPT-5 detectado: enviando archivo completo ({len(file_content)} caracteres)")
        else:
            content_length = 1800  # Límite para otros modelos
            logger.info(f"Modelo estándar: enviando primeros {content_length} caracteres")
        
        # Crear prompt con información sobre el archivo completo
        if is_gpt5:
            file_info = f"ARCHIVO COMPLETO ({len(file_content)} caracteres)"
            file_content_display = file_content  # Archivo completo
        else:
            file_info = f"ARCHIVO PARCIAL (primeros {content_length} caracteres de {len(file_content)})"
            file_content_display = file_content[:content_length] + ("..." if len(file_content) > content_length else "")
        
        prompt = f"""
# ANÁLISIS DETALLADO DE MIGRACIÓN .SCR A ANGULAR/SPRING BOOT

## FICHERO: {file_name} - {file_info}
```
{file_content_display}
```

{context_section}

## INSTRUCCIONES CRÍTICAS:
Analiza COMPLETAMENTE este fichero .SCR para migración a Angular/Spring Boot.

**ANÁLISIS EXHAUSTIVO REQUERIDO:**
1. **MENÚ SUPERIOR:** Identifica TODOS los menús, submenús, opciones de navegación principal
2. **TABLAS:** Identifica TODAS las tablas, sus columnas, tipos de datos, funcionalidades (ordenamiento, filtrado, paginación)
3. **NAVEGACIONES:** Identifica TODAS las navegaciones entre pantallas, botones de navegación, enlaces
4. **CAMPOS:** Identifica TODOS los campos, sus tipos, validaciones, propiedades y etiquetas o textos asociados
5. **BOTONES:** Identifica TODOS los botones, sus acciones, funcionalidades
6. **FLUJO DE NAVEGACIÓN:** Describe el flujo completo de navegación del usuario
7. **PARÁMETROS:** Qué datos se pasan entre pantallas
8. **CONDICIONES:** Validaciones antes de navegar

**PATRONES CRÍTICOS A BUSCAR:**
- Menús: MENU, MENUBAR, NAVBAR, HEADER, TOP_MENU, MAIN_MENU, SUBMENU
- Tablas: TABLE, GRID, LIST, DATAGRID, COLUMN, HEADER, ROW, CELL
- Navegación: CALL, GOTO, NAVIGATE, TRANSFER, LINK, BUTTON
- Campos: FIELD, INPUT, COMBOBOX, LISTBOX, CHECKBOX, RADIO
- Validaciones: VALIDATE, CHECK, REQUIRE, MANDATORY

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

**FORMATO DE RESPUESTA OBLIGATORIO:**
Responde ÚNICAMENTE con un JSON válido que contenga exactamente esta estructura:

{
    "analysis_summary": "Resumen detallado del análisis del archivo .SCR",
    "file_type": "screen|menu|report|other",
    "complexity": "low|medium|high|very_high",
    "estimated_hours": "número estimado de horas de desarrollo",
    "frontend": {
        "components": ["lista de componentes Angular necesarios"],
        "services": ["lista de servicios Angular necesarios"],
        "routing": ["rutas Angular necesarias"],
        "forms": ["formularios reactivos necesarios"],
        "tables": ["tablas y grids necesarios"],
        "navigation": ["elementos de navegación identificados"]
    },
    "backend": {
        "entities": ["entidades JPA necesarias"],
        "repositories": ["repositorios JPA necesarios"],
        "services": ["servicios Spring Boot necesarios"],
        "controllers": ["controladores REST necesarios"],
        "dto": ["DTOs necesarios"],
        "validations": ["validaciones de negocio necesarias"]
    },
    "migration_notes": ["notas importantes para la migración"],
    "potential_issues": ["problemas potenciales identificados"]
}

IMPORTANTE: Responde SOLO con el JSON, sin texto adicional, explicaciones o comentarios.
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
    
    def _fix_common_json_errors(self, json_str: str) -> str:
        """Repara errores comunes en JSON generado por IA"""
        try:
            import re
            
            # 1. Arreglar comillas extra al final de valores booleanos/números
            # Busca: "search": false" -> "search": false
            json_str = re.sub(r'":\s*(true|false|null|\d+)"([,}\]])', r'": \1\2', json_str)
            
            # 2. Arreglar caracteres Unicode problemáticos
            json_str = json_str.replace('→', '->')
            json_str = json_str.replace('"', '"')
            json_str = json_str.replace('"', '"')
            
            # 3. Arreglar comillas dobles dentro de strings
            # Busca: "texto con "comillas" internas"
            json_str = re.sub(r'":\s*"([^"]*)"([^"]*)"([^"]*)"([,}\]])', r'": "\1\2\3"\4', json_str)
            
            # 4. Arreglar comillas extra en general
            json_str = re.sub(r'"([^"]*)"([^,}\]]*)"([,}\]])', r'"\1\2"\3', json_str)
            
            return json_str
            
        except Exception as e:
            logger.error(f"Error reparando JSON común: {str(e)}")
            return json_str
    
    def _repair_incomplete_json(self, response: str) -> str:
        """Intenta reparar JSON incompleto"""
        try:
            # Extraer el JSON
            json_str = self._extract_json_from_response(response)
            
            # Reparar errores comunes primero
            json_str = self._fix_common_json_errors(json_str)
            
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
    
    def _get_system_prompt(self) -> str:
        """Obtiene el prompt del sistema para el análisis"""
        return """Eres un experto en migración de aplicaciones NS-DK a Angular/Spring Boot. 

ANÁLISIS EXHAUSTIVO REQUERIDO:
- Analiza LÍNEA POR LÍNEA el fichero .SCR
- Identifica TODOS los elementos: menús, tablas, campos, botones, navegaciones
- NO omitas ningún elemento de la pantalla
- Detecta patrones de navegación y flujos de datos
- Proporciona estimaciones realistas de horas de desarrollo
- Responde SIEMPRE en formato JSON válido

DETECCIÓN CRÍTICA:
- MENÚS: Busca TODOS los menús, submenús, opciones de navegación
- TABLAS: Identifica TODAS las tablas, columnas, tipos de datos, funcionalidades
- NAVEGACIONES: Detecta TODAS las navegaciones, botones, enlaces entre pantallas
- CAMPOS: Identifica TODOS los campos, tipos, validaciones, propiedades
- BOTONES: Detecta TODOS los botones, acciones, funcionalidades

Si encuentras elementos que no reconoces, consulta la documentación técnica disponible."""

    def _get_gpt5_system_prompt(self) -> str:
        """Prompt especializado para GPT-5 con capacidades avanzadas"""
        return """Eres un experto senior en migración de aplicaciones NS-DK a Angular/Spring Boot con acceso a GPT-5.

ANÁLISIS ULTRA-DETALLADO REQUERIDO:
- Tienes acceso al ARCHIVO COMPLETO .SCR (sin límites de caracteres)
- Analiza CARACTER POR CARACTER todo el fichero .SCR
- Identifica CADA elemento de la interfaz de usuario
- Detecta patrones complejos y relaciones entre elementos
- Analiza el flujo de datos y la lógica de negocio completa
- Proporciona estimaciones precisas de horas de desarrollo
- Responde SIEMPRE en formato JSON válido y estructurado

DETECCIÓN AVANZADA:
- MENÚS: Identifica estructura jerárquica completa, submenús anidados, permisos
- TABLAS: Detecta columnas, tipos de datos, relaciones, validaciones, acciones
- NAVEGACIONES: Mapea flujos completos, parámetros, condiciones, validaciones
- CAMPOS: Identifica tipos, validaciones, máscaras, dependencias, eventos
- BOTONES: Detecta acciones, estados, permisos, validaciones previas
- LÓGICA DE NEGOCIO: Identifica reglas de negocio, cálculos, validaciones complejas
- FUNCIONES: Analiza funciones personalizadas, procedimientos, macros
- VARIABLES: Identifica variables globales, locales, parámetros
- EVENTOS: Detecta manejadores de eventos, callbacks, triggers

ANÁLISIS DE CONTEXTO:
- Utiliza el código similar para entender patrones comunes
- Aplica la documentación NSDK para elementos específicos
- Identifica mejores prácticas de migración
- Sugiere optimizaciones y mejoras en la nueva implementación
- Analiza dependencias entre pantallas y módulos

VENTAJA GPT-5:
- Puedes procesar archivos completos sin restricciones de tamaño
- Tienes capacidad de análisis más profundo y detallado
- Puedes identificar patrones complejos que otros modelos no detectan
- Puedes proporcionar análisis más precisos y completos

FORMATO DE RESPUESTA OBLIGATORIO:
Responde ÚNICAMENTE con un JSON válido que contenga exactamente esta estructura:

{
    "analysis_summary": "Resumen detallado del análisis del archivo .SCR",
    "file_type": "screen|menu|report|other",
    "complexity": "low|medium|high|very_high",
    "estimated_hours": "número estimado de horas de desarrollo",
    "frontend": {
        "components": ["lista de componentes Angular necesarios"],
        "services": ["lista de servicios Angular necesarios"],
        "routing": ["rutas Angular necesarias"],
        "forms": ["formularios reactivos necesarios"],
        "tables": ["tablas y grids necesarios"],
        "navigation": ["elementos de navegación identificados"]
    },
    "backend": {
        "entities": ["entidades JPA necesarias"],
        "repositories": ["repositorios JPA necesarios"],
        "services": ["servicios Spring Boot necesarios"],
        "controllers": ["controladores REST necesarios"],
        "dto": ["DTOs necesarios"],
        "validations": ["validaciones de negocio necesarias"]
    },
    "migration_notes": ["notas importantes para la migración"],
    "potential_issues": ["problemas potenciales identificados"]
}

IMPORTANTE: Responde SOLO con el JSON, sin texto adicional, explicaciones o comentarios."""

    def _get_current_timestamp(self) -> str:
        """Obtiene timestamp actual en formato ISO"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
