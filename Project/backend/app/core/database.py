"""
DRIP — Configuración de la base de datos
SQLAlchemy + PostgreSQL con sesión asíncrona-ready
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,       # Reconecta si la conexión está caída
    pool_size=5,
    max_overflow=10,
    echo=settings.DEBUG,      # Logea SQL en modo DEBUG
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """
    Dependency de FastAPI — provee una sesión de BD por request
    y la cierra automáticamente al terminar.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Crea todas las tablas definidas en los modelos.
    Solo para desarrollo — en producción usar Alembic.
    """
    from app.models import (  # noqa: F401
        cultivo, parcela, sensor, lectura_sensor,
        clima, riego, alerta, costo, produccion
    )
    Base.metadata.create_all(bind=engine)
