"""Configuración de entorno de la aplicación.

Usa `pydantic-settings` (`BaseSettings`) para leer variables de entorno (y un
`.env` opcional). La instancia `settings` es importable desde cualquier módulo.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Raíz del repositorio (…/fastapi_template). `settings.py` vive en app/core/,
# por eso subimos dos niveles.
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # App
    PORT: int = 8080
    APP_NAME: str = "fastapi_template"

    # Database (MySQL).
    DB_HOSTNAME: str = "localhost"
    DB_PORT: str = "3306"
    DB_USERNAME: str = "buholegal"
    DB_PASSWORD: str = "changeme"
    DB_NAME: str = "buholegal"

    # CORS. Se lee como JSON array desde el entorno, p. ej. CORS_ORIGINS=["*"].
    CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
