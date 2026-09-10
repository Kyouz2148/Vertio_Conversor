import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Vertio-conversor"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # Diretórios de trabalho
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    OUTPUT_DIR: Path = STORAGE_DIR / "converted"
    TEMP_DIR: Path = STORAGE_DIR / "temp"

    # Retenção e Limites
    MAX_UPLOAD_SIZE_MB: int = 1024  # 1GB padrão
    FILE_RETENTION_MINUTES: int = 60  # Auto-limpeza de arquivos após 60 minutos
    CLEANUP_INTERVAL_MINUTES: int = 15  # Intervalo para rodar a rotina de limpeza

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Garantir que os diretórios necessários existem
for directory in [settings.STORAGE_DIR, settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
