from ..dto.configuration_dto import ConfigurationDTO
from ...infrastructure.services.git_service_impl import GitServiceImpl
from ...infrastructure.services.llm_service_impl import LLMServiceImpl
from ...infrastructure.services.vector_store_service_impl import VectorStoreServiceImpl

class TestConnectionsUseCase:
    def execute(self, config_data: dict):
        results = []
        # Repositorios
        for key, label in [
            ("sourceRepo", "Repositorio Origen (NSDK)"),
            ("frontendRepo", "Repositorio Frontend (Angular)"),
            ("backendRepo", "Repositorio Backend (Spring Boot)")
        ]:
            repo = config_data.get(key, {})
            ok, msg = GitServiceImpl.test_connection(repo)
            results.append({"service": label, "status": "success" if ok else "error", "message": msg})
        # LLM
        llm = config_data.get("llmConfig", {})
        ok, msg = LLMServiceImpl.test_connection(llm)
        results.append({"service": "LLM Provider", "status": "success" if ok else "error", "message": msg})
        # Vector Store
        vector = config_data.get("vectorStoreConfig", {})
        ok, msg = VectorStoreServiceImpl.test_connection(vector)
        results.append({"service": "Vector Store", "status": "success" if ok else "error", "message": msg})
        return results 