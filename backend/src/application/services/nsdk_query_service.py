"""
Servicio para consultar documentación NSDK
"""
from typing import List, Dict, Optional
from src.infrastructure.repositories.nsdk_document_chunk_repository import NSDKDocumentChunkRepository
from src.infrastructure.services.llm_service_impl import LLMServiceImpl


class NSDKQueryService:
    def __init__(self, db_session):
        self.chunk_repo = NSDKDocumentChunkRepository(db_session)
        self.llm_service = LLMServiceImpl()
    
    async def query_documentation(self, query: str, context: str = "") -> str:
        """Consulta la documentación NSDK y devuelve información relevante"""
        try:
            # 1. Generar embedding de la consulta
            query_embedding = await self.llm_service.get_embedding(query)
            
            # 2. Buscar chunks similares
            similar_chunks = await self.chunk_repo.search_similar_chunks(
                query_embedding, 
                limit=3,
                threshold=0.7
            )
            
            # 3. Formatear respuesta
            if similar_chunks:
                response = f"Información encontrada sobre '{query}':\n\n"
                for i, chunk in enumerate(similar_chunks, 1):
                    response += f"**Fuente {i}** ({chunk.chunk_title}):\n"
                    response += f"{chunk.chunk_text[:500]}...\n\n"
            else:
                response = f"No se encontró información específica sobre '{query}' en la documentación NSDK."
            
            return response
            
        except Exception as e:
            return f"Error consultando documentación: {str(e)}"
    
    async def get_documentation_stats(self) -> Dict:
        """Obtiene estadísticas de la documentación"""
        try:
            chunks = await self.chunk_repo.get_all()
            
            # Agrupar por documento
            documents = {}
            for chunk in chunks:
                doc_id = str(chunk.document_id)
                if doc_id not in documents:
                    documents[doc_id] = {
                        'document_id': doc_id,
                        'chunk_count': 0,
                        'total_text_length': 0
                    }
                documents[doc_id]['chunk_count'] += 1
                documents[doc_id]['total_text_length'] += len(chunk.chunk_text)
            
            return {
                'total_documents': len(documents),
                'total_chunks': len(chunks),
                'documents': list(documents.values())
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def test_document_indexing(self, document_name: str = None) -> Dict:
        """Prueba la indexación de documentos"""
        test_queries = [
            "COMBBOX control",
            "LISTBOX tabla",
            "DIALOG ventana",
            "MENU opciones",
            "ENTRY campo entrada"
        ]
        
        results = {}
        for query in test_queries:
            try:
                response = await self.query_documentation(query)
                results[query] = {
                    'success': True,
                    'response_length': len(response),
                    'has_content': 'Información encontrada' in response
                }
            except Exception as e:
                results[query] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
