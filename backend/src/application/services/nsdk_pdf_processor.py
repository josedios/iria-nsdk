"""
Servicio para procesar PDFs técnicos de NSDK
"""
import os
import re
import uuid
import json
from typing import List, Dict, Optional
import PyPDF2
from datetime import datetime

from src.infrastructure.repositories.nsdk_document_repository import NSDKDocumentRepository
from src.infrastructure.repositories.nsdk_document_chunk_repository import NSDKDocumentChunkRepository
from src.infrastructure.services.llm_service_impl import LLMServiceImpl
from src.infrastructure.services.vector_store_service_impl import VectorStoreServiceImpl


class NSDKPDFProcessor:
    def __init__(self, db_session):
        self.document_repo = NSDKDocumentRepository(db_session)
        self.chunk_repo = NSDKDocumentChunkRepository(db_session)
        self.llm_service = LLMServiceImpl()
        self.vector_store = VectorStoreServiceImpl()
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extrae texto del PDF preservando estructura"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text += f"\n--- PAGE {page_num + 1} ---\n{page_text}\n"
                
                return text
        except Exception as e:
            raise Exception(f"Error extrayendo texto del PDF: {str(e)}")
    
    def create_smart_chunks(self, text: str) -> List[Dict]:
        """Crea chunks inteligentes basados en estructura del PDF"""
        chunks = []
        
        # 1. Dividir por secciones (títulos en mayúsculas o con números)
        sections = re.split(r'\n([A-Z][A-Z\s0-9\.\-]+)\n', text)
        
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                title = sections[i].strip()
                content = sections[i + 1].strip()
                
                # Limpiar título
                title = re.sub(r'^[0-9\.\-\s]+', '', title).strip()
                
                # 2. Subdividir contenido largo
                if len(content) > 2000:
                    sub_chunks = self._split_long_content(content)
                    for j, sub_content in enumerate(sub_chunks):
                        chunks.append({
                            'title': f"{title} - Parte {j+1}" if len(sub_chunks) > 1 else title,
                            'content': sub_content,
                            'section': title,
                            'chunk_type': 'section'
                        })
                else:
                    chunks.append({
                        'title': title,
                        'content': content,
                        'section': title,
                        'chunk_type': 'section'
                    })
        
        # Si no se encontraron secciones, dividir por párrafos
        if not chunks:
            chunks = self._split_by_paragraphs(text)
        
        return chunks
    
    def _split_long_content(self, content: str) -> List[str]:
        """Subdivide contenido largo preservando párrafos"""
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk + paragraph) > 1500:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_by_paragraphs(self, text: str) -> List[Dict]:
        """Divide texto por párrafos cuando no hay secciones claras"""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            if len(current_chunk + paragraph) > 1500:
                if current_chunk:
                    chunks.append({
                        'title': f"Sección {chunk_index + 1}",
                        'content': current_chunk.strip(),
                        'section': f"Sección {chunk_index + 1}",
                        'chunk_type': 'paragraph'
                    })
                    chunk_index += 1
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append({
                'title': f"Sección {chunk_index + 1}",
                'content': current_chunk.strip(),
                'section': f"Sección {chunk_index + 1}",
                'chunk_type': 'paragraph'
            })
        
        return chunks
    
    async def process_nsdk_document(self, file_path: str, document_name: str) -> str:
        """Procesa un documento NSDK completo"""
        
        try:
            print(f"📄 Procesando: {document_name}")
            
            # 1. Verificar si el documento ya existe
            existing_document = await self.document_repo.get_by_name(document_name)
            if existing_document and existing_document.status == 'completed':
                print(f"⚠️ Documento {document_name} ya está procesado")
                return str(existing_document.id)
            
            # 2. Si existe pero está en error, eliminar y reprocesar
            if existing_document and existing_document.status == 'error':
                print(f"🔄 Reprocesando documento {document_name} (estado anterior: error)")
                await self.document_repo.delete(str(existing_document.id))
                await self.chunk_repo.delete_by_document_id(str(existing_document.id))
            
            # 3. Crear nuevo registro de documento
            document_id = str(uuid.uuid4())
            file_size = os.path.getsize(file_path)
            document = await self.document_repo.create({
                'id': document_id,
                'name': document_name,
                'file_path': file_path,
                'file_size': file_size,
                'status': 'processing'
            })
            
            # 4. Extraer texto
            text = self.extract_text_from_pdf(file_path)
            print(f"✅ Texto extraído: {len(text)} caracteres")
            
            # 5. Crear chunks inteligentes
            chunks = self.create_smart_chunks(text)
            print(f"✅ Chunks creados: {len(chunks)}")
            
            # 6. Generar embeddings y almacenar chunks
            for i, chunk in enumerate(chunks):
                print(f"🔄 Procesando chunk {i+1}/{len(chunks)}")
                
                # Generar embedding
                embedding = await self.llm_service.get_embedding(chunk['content'])
                
                # Crear chunk en BD
                chunk_data = {
                    'id': str(uuid.uuid4()),
                    'document_id': document_id,
                    'chunk_index': i,
                    'chunk_text': chunk['content'],
                    'chunk_title': chunk['title'],
                    'chunk_section': chunk['section'],
                    'chunk_type': chunk['chunk_type'],
                    'embedding': embedding  # Array de floats para PostgreSQL
                }
                
                await self.chunk_repo.create(chunk_data)
            
            # 7. Actualizar documento
            await self.document_repo.update(document_id, {
                'status': 'completed',
                'total_chunks': len(chunks)
            })
            
            print(f"✅ Documento {document_name} procesado y almacenado")
            return document_id
            
        except Exception as e:
            # Marcar como error si el documento fue creado
            if 'document_id' in locals():
                await self.document_repo.update(document_id, {'status': 'error'})
            raise Exception(f"Error procesando documento: {str(e)}")
    
    async def get_document_status(self, document_id: str) -> Dict:
        """Obtiene el estado de procesamiento de un documento"""
        document = await self.document_repo.get_by_id(document_id)
        if document:
            return document.to_dict()
        return None
