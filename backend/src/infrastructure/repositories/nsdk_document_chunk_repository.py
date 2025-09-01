"""
Repositorio para chunks de documentos NSDK
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

from src.domain.entities.nsdk_document_chunk import NSDKDocumentChunk


class NSDKDocumentChunkRepository:
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, chunk_data: Dict) -> NSDKDocumentChunk:
        """Crea un nuevo chunk"""
        chunk = NSDKDocumentChunk(**chunk_data)
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk
    
    async def get_by_id(self, chunk_id: str) -> Optional[NSDKDocumentChunk]:
        """Obtiene un chunk por ID"""
        stmt = select(NSDKDocumentChunk).where(NSDKDocumentChunk.id == chunk_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_document_id(self, document_id: str) -> List[NSDKDocumentChunk]:
        """Obtiene todos los chunks de un documento"""
        stmt = select(NSDKDocumentChunk).where(
            NSDKDocumentChunk.document_id == document_id
        ).order_by(NSDKDocumentChunk.chunk_index)
        result = self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_all(self) -> List[NSDKDocumentChunk]:
        """Obtiene todos los chunks"""
        stmt = select(NSDKDocumentChunk).order_by(NSDKDocumentChunk.created_at.desc())
        result = self.db.execute(stmt)
        return result.scalars().all()
    
    async def update(self, chunk_id: str, update_data: Dict) -> Optional[NSDKDocumentChunk]:
        """Actualiza un chunk"""
        stmt = update(NSDKDocumentChunk).where(NSDKDocumentChunk.id == chunk_id).values(**update_data)
        self.db_session.execute(stmt)
        self.db_session.commit()
        
        return await self.get_by_id(chunk_id)
    
    async def delete(self, chunk_id: str) -> bool:
        """Elimina un chunk"""
        stmt = delete(NSDKDocumentChunk).where(NSDKDocumentChunk.id == chunk_id)
        result = self.db.execute(stmt)
        self.db_session.commit()
        return result.rowcount > 0
    
    async def delete_by_document_id(self, document_id: str) -> int:
        """Elimina todos los chunks de un documento"""
        stmt = delete(NSDKDocumentChunk).where(NSDKDocumentChunk.document_id == document_id)
        result = self.db.execute(stmt)
        self.db_session.commit()
        return result.rowcount
    
    async def search_similar_chunks(self, query_embedding: List[float], limit: int = 5, threshold: float = 0.7) -> List[NSDKDocumentChunk]:
        """Busca chunks similares usando embeddings (implementación básica)"""
        import json
        
        # Nota: Esta es una implementación básica. Para producción, usar pgvector o FAISS
        all_chunks = await self.get_all()
        
        # Calcular similitud coseno básica
        similar_chunks = []
        for chunk in all_chunks:
            if chunk.embedding and isinstance(chunk.embedding, list):
                similarity = self._cosine_similarity(query_embedding, chunk.embedding)
                if similarity >= threshold:
                    similar_chunks.append((chunk, similarity))
        
        # Ordenar por similitud y devolver los mejores
        similar_chunks.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, _ in similar_chunks[:limit]]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similitud coseno entre dos vectores"""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        
        return dot_product / (magnitude1 * magnitude2)
