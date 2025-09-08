#!/usr/bin/env python3
"""
Script para ejecutar la migración de tablas NSDK
"""
import sqlite3
import os

def run_migration():
    # Conectar a la base de datos
    db_path = 'nsdk_migration.db'
    if not os.path.exists(db_path):
        print('❌ Base de datos no encontrada')
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Leer y ejecutar la migración
        migration_file = 'migrations/003_create_nsdk_documents_tables_sqlite.sql'
        if not os.path.exists(migration_file):
            print(f'❌ Archivo de migración no encontrado: {migration_file}')
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Ejecutar la migración
        cursor.executescript(migration_sql)
        conn.commit()
        
        # Verificar que las tablas se crearon
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'nsdk_%'")
        tables = cursor.fetchall()
        print('✅ Tablas NSDK creadas:', [table[0] for table in tables])
        
        conn.close()
        print('✅ Migración ejecutada exitosamente')
        return True
        
    except Exception as e:
        print(f'❌ Error ejecutando migración: {str(e)}')
        return False

if __name__ == '__main__':
    run_migration()
