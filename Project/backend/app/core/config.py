"""
DRIP — Configuración central de la aplicación
Carga variables de entorno desde .env usando Pydantic Settings
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "DRIP AgTech API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    PORT: int = 8000

    # Base de datos
    DATABASE_URL: str = "postgresql://drip_user:drip_pass@localhost:5432/drip_db"

    # Seguridad
    SECRET_KEY: str = "drip-secret-key-agtech-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas

    # CORS
    ALLOWED_ORIGINS: list = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    # Usuario demo
    DEMO_USER: str = "Danae"
    DEMO_PASSWORD: str = "drip2024"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
