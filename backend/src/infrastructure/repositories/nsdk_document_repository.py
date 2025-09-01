"""
Repositorio para documentos NSDK
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

from src.domain.entities.nsdk_document import NSDKDocument


class NSDKDocumentRepository:
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, document_data: Dict) -> NSDKDocument:
        """Crea un nuevo documento"""
        document = NSDKDocument(**document_data)
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
    
    async def get_by_id(self, document_id: str) -> Optional[NSDKDocument]:
        """Obtiene un documento por ID"""
        stmt = select(NSDKDocument).where(NSDKDocument.id == document_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[NSDKDocument]:
        """Obtiene un documento por nombre (el más reciente)"""
        stmt = select(NSDKDocument).where(NSDKDocument.name == name).order_by(NSDKDocument.created_at.desc()).limit(1)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self) -> List[NSDKDocument]:
        """Obtiene todos los documentos"""
        stmt = select(NSDKDocument).order_by(NSDKDocument.created_at.desc())
        result = self.db.execute(stmt)
        return result.scalars().all()
    
    async def update(self, document_id: str, update_data: Dict) -> Optional[NSDKDocument]:
        """Actualiza un documento"""
        stmt = update(NSDKDocument).where(NSDKDocument.id == document_id).values(**update_data)
        self.db.execute(stmt)
        self.db.commit()
        
        return await self.get_by_id(document_id)
    
    async def delete(self, document_id: str) -> bool:
        """Elimina un documento"""
        stmt = delete(NSDKDocument).where(NSDKDocument.id == document_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0
    
    async def get_by_status(self, status: str) -> List[NSDKDocument]:
        """Obtiene documentos por estado"""
        stmt = select(NSDKDocument).where(NSDKDocument.status == status)
        result = self.db.execute(stmt)
        return result.scalars().all()
