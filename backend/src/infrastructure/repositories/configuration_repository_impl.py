from typing import List, Optional
from ...domain.entities.configuration import Configuration
from ...domain.repositories.configuration_repository import ConfigurationRepository
from ...database import SessionLocal
from sqlalchemy.orm import Session

class ConfigurationRepositoryImpl(ConfigurationRepository):
    def __init__(self):
        self.db: Session = SessionLocal()

    async def save(self, configuration: Configuration) -> Configuration:
        self.db.add(configuration)
        self.db.commit()
        self.db.refresh(configuration)
        return configuration

    async def find_by_id(self, config_id: str) -> Optional[Configuration]:
        return self.db.query(Configuration).filter(Configuration.id == config_id).first()

    async def find_all(self) -> List[Configuration]:
        return self.db.query(Configuration).all()

    async def find_active(self) -> Optional[Configuration]:
        # Suponiendo que hay un campo is_active, si no, devolver la última
        return self.db.query(Configuration).order_by(Configuration.created_at.desc()).first()

    async def update(self, configuration: Configuration) -> Configuration:
        self.db.merge(configuration)
        self.db.commit()
        self.db.refresh(configuration)
        return configuration

    async def delete(self, config_id: str) -> bool:
        config = self.db.query(Configuration).filter(Configuration.id == config_id).first()
        if config:
            self.db.delete(config)
            self.db.commit()
            return True
        return False

    async def set_active(self, config_id: str) -> bool:
        # Implementación dummy, depende de si hay campo is_active
        return True

    async def find_by_name(self, name: str) -> Optional[Configuration]:
        return self.db.query(Configuration).filter(Configuration.name == name).first() 