-- Script de prueba para verificar que la base de datos IRIA NSDK funciona correctamente
-- Ejecutar este script en pgAdmin después de haber ejecutado init_pgadmin.sql

-- 1. Verificar que las tablas existen
SELECT 
    table_name,
    CASE WHEN table_name IS NOT NULL THEN '✅ CREADA' ELSE '❌ FALTANTE' END as estado
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('configurations', 'analyses', 'modules', 'screens')
ORDER BY table_name;

-- 2. Verificar que la extensión uuid-ossp está instalada
SELECT 
    extname,
    CASE WHEN extname = 'uuid-ossp' THEN '✅ INSTALADA' ELSE '❌ FALTANTE' END as estado
FROM pg_extension 
WHERE extname = 'uuid-ossp';

-- 3. Verificar que la función update_updated_at_column existe
SELECT 
    routine_name,
    CASE WHEN routine_name = 'update_updated_at_column' THEN '✅ CREADA' ELSE '❌ FALTANTE' END as estado
FROM information_schema.routines 
WHERE routine_schema = 'public' 
AND routine_name = 'update_updated_at_column';

-- 4. Verificar que los triggers existen
SELECT 
    trigger_name,
    event_object_table,
    CASE WHEN trigger_name IS NOT NULL THEN '✅ CREADO' ELSE '❌ FALTANTE' END as estado
FROM information_schema.triggers 
WHERE trigger_schema = 'public' 
AND trigger_name LIKE 'update_%_updated_at'
ORDER BY event_object_table;

-- 5. Verificar que los índices existen
SELECT 
    indexname,
    tablename,
    CASE WHEN indexname IS NOT NULL THEN '✅ CREADO' ELSE '❌ FALTANTE' END as estado
FROM pg_indexes 
WHERE schemaname = 'public' 
AND indexname IN ('idx_configurations_name', 'idx_analyses_status', 'idx_modules_type')
ORDER BY tablename;

-- 6. Prueba de inserción en cada tabla
-- Configurations
INSERT INTO configurations (name, description, config_data) 
VALUES ('Test Config', 'Configuración de prueba', '{"test": true, "version": "1.0"}')
RETURNING id, name, created_at;

-- Analyses
INSERT INTO analyses (name, description, status, results) 
VALUES ('Test Analysis', 'Análisis de prueba', 'completed', '{"result": "success", "score": 95}')
RETURNING id, name, status, created_at;

-- Modules
INSERT INTO modules (name, description, module_type, config_data) 
VALUES ('Test Module', 'Módulo de prueba', 'test', '{"enabled": true}')
RETURNING id, name, module_type, created_at;

-- Screens
INSERT INTO screens (name, description, screen_data) 
VALUES ('Test Screen', 'Pantalla de prueba', '{"layout": "grid", "components": []}')
RETURNING id, name, created_at;

-- 7. Verificar que los timestamps se actualizan automáticamente
-- Actualizar un registro para probar el trigger
UPDATE configurations 
SET name = 'Test Config Updated' 
WHERE name = 'Test Config'
RETURNING id, name, created_at, updated_at;

-- 8. Mostrar todos los registros creados
SELECT 'Configurations' as tabla, id::text, name, created_at, updated_at FROM configurations WHERE name LIKE 'Test%'
UNION ALL
SELECT 'Analyses' as tabla, id::text, name, created_at, updated_at FROM analyses WHERE name LIKE 'Test%'
UNION ALL
SELECT 'Modules' as tabla, id::text, name, created_at, updated_at FROM modules WHERE name LIKE 'Test%'
UNION ALL
SELECT 'Screens' as tabla, id::text, name, created_at, updated_at FROM screens WHERE name LIKE 'Test%'
ORDER BY tabla, created_at;

-- 9. Limpiar datos de prueba (opcional - comentar si quieres mantener los datos)
-- DELETE FROM configurations WHERE name LIKE 'Test%';
-- DELETE FROM analyses WHERE name LIKE 'Test%';
-- DELETE FROM modules WHERE name LIKE 'Test%';
-- DELETE FROM screens WHERE name LIKE 'Test%'; 