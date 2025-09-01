#!/usr/bin/env python3
"""
Script para crear las tablas NSDK usando SQLAlchemy
"""
import sys
import os
sys.path.append('src')

from src.database import engine, Base
from src.domain.entities.nsdk_document import NSDKDocument
from src.domain.entities.nsdk_document_chunk import NSDKDocumentChunk

def create_tables():
    try:
        print("🔄 Creando tablas NSDK...")
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        print("✅ Tablas NSDK creadas exitosamente")
        
        # Verificar que las tablas se crearon
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        nsdk_tables = [table for table in tables if 'nsdk' in table.lower()]
        
        print(f"📊 Tablas NSDK encontradas: {nsdk_tables}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando tablas: {str(e)}")
        return False

if __name__ == '__main__':
    create_tables()
