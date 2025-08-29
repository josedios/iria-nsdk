import httpx
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class VectorStoreServiceImpl:
    def __init__(self):
        self.collections = {}
        self.faiss_index = None
        self.faiss_metadata = []
    
    @staticmethod
    def test_connection(config: dict) -> (bool, str):
        tipo = config.get('type')
        if tipo == 'qdrant':
            url = config.get('connectionString', 'http://localhost:6333')
            try:
                resp = httpx.get(f'{url}/collections', timeout=5)
                if resp.status_code == 200:
                    return True, 'Conexión exitosa a Qdrant'
                else:
                    return False, f'Error Qdrant: {resp.text}'
            except Exception as e:
                return False, f'Error de conexión Qdrant: {str(e)}'
        elif tipo == 'chroma':
            url = config.get('connectionString', 'http://localhost:8000')
            try:
                resp = httpx.get(url, timeout=5)
                if resp.status_code == 200:
                    return True, 'Conexión exitosa a Chroma'
                else:
                    return False, f'Error Chroma: {resp.text}'
            except Exception as e:
                return False, f'Error de conexión Chroma: {str(e)}'
        elif tipo == 'faiss':
            # FAISS es local, solo comprobamos el tipo
            return True, 'FAISS configurado (local)'
        else:
            return False, 'Tipo de Vector Store no soportado o no especificado'
    
    def initialize_collection(self, config: dict, collection_name: str = None) -> bool:
        """Inicializa una colección en el vector store"""
        try:
            tipo = config.get('type')
            collection_name = collection_name or config.get('collectionName', 'nsdk-embeddings')
            
            if tipo == 'qdrant':
                return self._init_qdrant_collection(config, collection_name)
            elif tipo == 'chroma':
                return self._init_chroma_collection(config, collection_name)
            elif tipo == 'faiss':
                return self._init_faiss_collection(config, collection_name)
            else:
                logger.error(f"Tipo de vector store no soportado: {tipo}")
                return False
                
        except Exception as e:
            logger.error(f"Error inicializando colección: {str(e)}")
            return False
    
    def clear_collection(self, config: dict, collection_name: str = None) -> bool:
        """Limpia completamente una colección del vector store"""
        try:
            tipo = config.get('type')
            collection_name = collection_name or config.get('collectionName', 'nsdk-embeddings')
            
            logger.info(f"Limpiando colección '{collection_name}' del tipo {tipo}")
            
            if tipo == 'qdrant':
                return self._clear_qdrant_collection(config, collection_name)
            elif tipo == 'chroma':
                return self._clear_chroma_collection(config, collection_name)
            elif tipo == 'faiss':
                return self._clear_faiss_collection(config, collection_name)
            else:
                logger.error(f"Tipo de vector store no soportado para limpieza: {tipo}")
                return False
                
        except Exception as e:
            logger.error(f"Error limpiando colección: {str(e)}")
            return False
    
    def _init_qdrant_collection(self, config: dict, collection_name: str) -> bool:
        """Inicializa colección en Qdrant"""
        try:
            url = config.get('connectionString', 'http://localhost:6333')
            dimension = config.get('dimension', 1536)
            
            # Crear colección si no existe
            collection_data = {
                "name": collection_name,
                "vectors": {
                    "size": dimension,
                    "distance": "Cosine"
                }
            }
            
            resp = httpx.post(
                f'{url}/collections/{collection_name}',
                json=collection_data,
                timeout=10
            )
            
            if resp.status_code in [200, 409]:  # 409 = ya existe
                logger.info(f"Colección Qdrant '{collection_name}' inicializada")
                return True
            else:
                logger.error(f"Error creando colección Qdrant: {resp.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error inicializando colección Qdrant: {str(e)}")
            return False
    
    def _init_chroma_collection(self, config: dict, collection_name: str) -> bool:
        """Inicializa colección en Chroma"""
        try:
            url = config.get('connectionString', 'http://localhost:8000')
            
            # Chroma crea colecciones automáticamente
            resp = httpx.get(f'{url}/api/v1/collections', timeout=5)
            
            if resp.status_code == 200:
                logger.info(f"Colección Chroma '{collection_name}' inicializada")
                return True
            else:
                logger.error(f"Error conectando a Chroma: {resp.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error inicializando colección Chroma: {str(e)}")
            return False
    
    def _init_faiss_collection(self, config: dict, collection_name: str) -> bool:
        """Inicializa colección FAISS local"""
        try:
            dimension = config.get('dimension', 1536)
            
            # Importar FAISS solo cuando sea necesario
            try:
                import faiss
            except ImportError:
                logger.error("FAISS no está instalado. Instala con: pip install faiss-cpu")
                return False
            
            # Crear índice FAISS
            self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner Product para similitud coseno
            self.faiss_metadata = []
            
            logger.info(f"Colección FAISS '{collection_name}' inicializada con dimensión {dimension}")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando colección FAISS: {str(e)}")
            return False
    
    def add_embeddings(self, config: dict, embeddings: List[List[float]], 
                       metadata: List[Dict[str, Any]], ids: List[str] = None) -> bool:
        """Añade embeddings al vector store"""
        try:
            tipo = config.get('type')
            collection_name = config.get('collectionName', 'nsdk-embeddings')
            
            if tipo == 'qdrant':
                return self._add_qdrant_embeddings(config, collection_name, embeddings, metadata, ids)
            elif tipo == 'chroma':
                return self._add_chroma_embeddings(config, collection_name, embeddings, metadata, ids)
            elif tipo == 'faiss':
                return self._add_faiss_embeddings(config, collection_name, embeddings, metadata, ids)
            else:
                logger.error(f"Tipo de vector store no soportado: {tipo}")
                return False
                
        except Exception as e:
            logger.error(f"Error añadiendo embeddings: {str(e)}")
            return False
    
    def _add_qdrant_embeddings(self, config: dict, collection_name: str, 
                               embeddings: List[List[float]], metadata: List[Dict[str, Any]], 
                               ids: List[str] = None) -> bool:
        """Añade embeddings a Qdrant"""
        try:
            url = config.get('connectionString', 'http://localhost:6333')
            
            # Generar IDs si no se proporcionan
            if not ids:
                import uuid
                ids = [str(uuid.uuid4()) for _ in embeddings]
            
            # Preparar puntos para Qdrant
            points = []
            for i, (embedding, meta, point_id) in enumerate(zip(embeddings, metadata, ids)):
                point = {
                    "id": point_id,
                    "vector": embedding,
                    "payload": meta
                }
                points.append(point)
            
            # Añadir puntos en lotes
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                
                resp = httpx.put(
                    f'{url}/collections/{collection_name}/points',
                    json={"points": batch},
                    timeout=30
                )
                
                if resp.status_code != 200:
                    logger.error(f"Error añadiendo lote a Qdrant: {resp.text}")
                    return False
            
            logger.info(f"Añadidos {len(embeddings)} embeddings a Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Error añadiendo embeddings a Qdrant: {str(e)}")
            return False
    
    def _add_chroma_embeddings(self, config: dict, collection_name: str, 
                               embeddings: List[List[float]], metadata: List[Dict[str, Any]], 
                               ids: List[str] = None) -> bool:
        """Añade embeddings a Chroma"""
        try:
            url = config.get('connectionString', 'http://localhost:8000')
            
            # Generar IDs si no se proporcionan
            if not ids:
                import uuid
                ids = [str(uuid.uuid4()) for _ in embeddings]
            
            # Preparar datos para Chroma
            chroma_data = {
                "ids": ids,
                "embeddings": embeddings,
                "metadatas": metadata,
                "documents": [meta.get('content', '') for meta in metadata]
            }
            
            # Añadir embeddings
            resp = httpx.post(
                f'{url}/api/v1/collections/{collection_name}/add',
                json=chroma_data,
                timeout=30
            )
            
            if resp.status_code == 200:
                logger.info(f"Añadidos {len(embeddings)} embeddings a Chroma")
                return True
            else:
                logger.error(f"Error añadiendo embeddings a Chroma: {resp.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error añadiendo embeddings a Chroma: {str(e)}")
            return False
    
    def _add_faiss_embeddings(self, config: dict, collection_name: str, 
                              embeddings: List[List[float]], metadata: List[Dict[str, Any]], 
                              ids: List[str] = None) -> bool:
        """Añade embeddings a FAISS"""
        try:
            if not self.faiss_index:
                logger.error("Índice FAISS no inicializado")
                return False
            
            # Convertir embeddings a numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Añadir al índice FAISS
            self.faiss_index.add(embeddings_array)
            
            # Añadir metadatos
            if not ids:
                import uuid
                ids = [str(uuid.uuid4()) for _ in embeddings]
            
            for meta, point_id in zip(metadata, ids):
                meta['id'] = point_id
                self.faiss_metadata.append(meta)
            
            logger.info(f"Añadidos {len(embeddings)} embeddings a FAISS")
            return True
            
        except Exception as e:
            logger.error(f"Error añadiendo embeddings a FAISS: {str(e)}")
            return False
    
    def search_similar(self, query_embedding: List[float], config: dict, 
                      limit: int = 10, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Busca embeddings similares"""
        try:
            tipo = config.get('type')
            collection_name = config.get('collectionName', 'nsdk-embeddings')
            
            if tipo == 'qdrant':
                return self._search_qdrant_similar(config, collection_name, query_embedding, limit, threshold)
            elif tipo == 'chroma':
                return self._search_chroma_similar(config, collection_name, query_embedding, limit, threshold)
            elif tipo == 'faiss':
                return self._search_faiss_similar(config, collection_name, query_embedding, limit, threshold)
            else:
                logger.error(f"Tipo de vector store no soportado: {tipo}")
                return []
                
        except Exception as e:
            logger.error(f"Error en búsqueda similar: {str(e)}")
            return []
    
    def _search_qdrant_similar(self, config: dict, collection_name: str, 
                               query_embedding: List[float], limit: int, threshold: float) -> List[Dict[str, Any]]:
        """Busca similares en Qdrant"""
        try:
            url = config.get('connectionString', 'http://localhost:6333')
            
            search_data = {
                "vector": query_embedding,
                "limit": limit,
                "score_threshold": threshold,
                "with_payload": True
            }
            
            resp = httpx.post(
                f'{url}/collections/{collection_name}/search',
                json=search_data,
                timeout=10
            )
            
            if resp.status_code == 200:
                results = resp.json()['result']
                return [
                    {
                        'id': result['id'],
                        'score': result['score'],
                        'metadata': result['payload']
                    }
                    for result in results
                ]
            else:
                logger.error(f"Error en búsqueda Qdrant: {resp.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error en búsqueda Qdrant: {str(e)}")
            return []
    
    def _search_chroma_similar(self, config: dict, collection_name: str, 
                               query_embedding: List[float], limit: int, threshold: float) -> List[Dict[str, Any]]:
        """Busca similares en Chroma"""
        try:
            url = config.get('connectionString', 'http://localhost:8000')
            
            search_data = {
                "query_embeddings": [query_embedding],
                "n_results": limit,
                "where": {},
                "where_document": {}
            }
            
            resp = httpx.post(
                f'{url}/api/v1/collections/{collection_name}/query',
                json=search_data,
                timeout=10
            )
            
            if resp.status_code == 200:
                results = resp.json()
                return [
                    {
                        'id': results['ids'][0][i],
                        'score': results['distances'][0][i],
                        'metadata': results['metadatas'][0][i]
                    }
                    for i in range(min(limit, len(results['ids'][0])))
                ]
            else:
                logger.error(f"Error en búsqueda Chroma: {resp.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error en búsqueda Chroma: {str(e)}")
            return []
    
    def _search_faiss_similar(self, config: dict, collection_name: str, 
                              query_embedding: List[float], limit: int, threshold: float) -> List[Dict[str, Any]]:
        """Busca similares en FAISS"""
        try:
            if not self.faiss_index or not self.faiss_metadata:
                logger.error("Índice FAISS no inicializado o sin datos")
                return []
            
            # Convertir query a numpy array
            query_array = np.array([query_embedding], dtype=np.float32)
            
            # Buscar en FAISS
            scores, indices = self.faiss_index.search(query_array, limit)
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if score >= threshold and idx < len(self.faiss_metadata):
                    metadata = self.faiss_metadata[idx].copy()
                    metadata['score'] = float(score)
                    results.append(metadata)
            
            return results
            
        except Exception as e:
            logger.error(f"Error en búsqueda FAISS: {str(e)}")
            return []
    
    def get_collection_stats(self, config: dict, collection_name: str = None) -> Dict[str, Any]:
        """Obtiene estadísticas de la colección"""
        try:
            tipo = config.get('type')
            collection_name = collection_name or config.get('collectionName', 'nsdk-embeddings')
            
            if tipo == 'qdrant':
                return self._get_qdrant_stats(config, collection_name)
            elif tipo == 'chroma':
                return self._get_chroma_stats(config, collection_name)
            elif tipo == 'faiss':
                return self._get_faiss_stats(config, collection_name)
            else:
                return {'error': f'Tipo no soportado: {tipo}'}
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {'error': str(e)}
    
    def _get_qdrant_stats(self, config: dict, collection_name: str) -> Dict[str, Any]:
        """Obtiene estadísticas de Qdrant"""
        try:
            url = config.get('connectionString', 'http://localhost:6333')
            
            resp = httpx.get(f'{url}/collections/{collection_name}', timeout=5)
            
            if resp.status_code == 200:
                collection_info = resp.json()['result']
                return {
                    'type': 'qdrant',
                    'name': collection_name,
                    'vectors_count': collection_info.get('vectors_count', 0),
                    'points_count': collection_info.get('points_count', 0),
                    'status': collection_info.get('status', 'unknown')
                }
            else:
                return {'error': f'Error obteniendo info: {resp.text}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _get_chroma_stats(self, config: dict, collection_name: str) -> Dict[str, Any]:
        """Obtiene estadísticas de Chroma"""
        try:
            url = config.get('connectionString', 'http://localhost:8000')
            
            resp = httpx.get(f'{url}/api/v1/collections/{collection_name}/count', timeout=5)
            
            if resp.status_code == 200:
                count_info = resp.json()
                return {
                    'type': 'chroma',
                    'name': collection_name,
                    'count': count_info.get('count', 0)
                }
            else:
                return {'error': f'Error obteniendo count: {resp.text}'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _get_faiss_stats(self, config: dict, collection_name: str) -> Dict[str, Any]:
        """Obtiene estadísticas de FAISS"""
        try:
            if not self.faiss_index:
                return {'error': 'Índice FAISS no inicializado'}
            
            return {
                'type': 'faiss',
                'name': collection_name,
                'vectors_count': self.faiss_index.ntotal,
                'dimension': self.faiss_index.d,
                'metadata_count': len(self.faiss_metadata)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _clear_qdrant_collection(self, config: dict, collection_name: str) -> bool:
        """Limpia completamente una colección de Qdrant"""
        try:
            url = config.get('connectionString', 'http://localhost:6333')
            
            # Eliminar todos los puntos de la colección
            resp = httpx.post(
                f'{url}/collections/{collection_name}/points/delete',
                json={"filter": {}},  # Filtro vacío = eliminar todo
                timeout=10
            )
            
            if resp.status_code in [200, 202]:
                logger.info(f"Colección Qdrant '{collection_name}' limpiada exitosamente")
                return True
            else:
                logger.error(f"Error limpiando colección Qdrant: {resp.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error limpiando colección Qdrant: {str(e)}")
            return False
    
    def _clear_chroma_collection(self, config: dict, collection_name: str) -> bool:
        """Limpia completamente una colección de Chroma"""
        try:
            url = config.get('connectionString', 'http://localhost:8000')
            
            # Eliminar todos los documentos de la colección
            resp = httpx.delete(
                f'{url}/api/v1/collections/{collection_name}/delete',
                timeout=10
            )
            
            if resp.status_code in [200, 204]:
                logger.info(f"Colección Chroma '{collection_name}' limpiada exitosamente")
                return True
            else:
                logger.error(f"Error limpiando colección Chroma: {resp.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error limpiando colección Chroma: {str(e)}")
            return False
    
    def _clear_faiss_collection(self, config: dict, collection_name: str) -> bool:
        """Limpia completamente una colección de FAISS"""
        try:
            # Reinicializar índices y metadatos
            self.faiss_index = None
            self.faiss_metadata = []
            
            logger.info(f"Colección FAISS '{collection_name}' limpiada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error limpiando colección FAISS: {str(e)}")
            return False