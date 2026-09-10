import os
import time
import shutil
import uuid
import logging
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile
import aiofiles

from app.config import settings

logger = logging.getLogger("file_manager")

def generate_file_id() -> str:
    """Gera um identificador único para o arquivo/sessão."""
    return str(uuid.uuid4())[:8]

def sanitize_filename(filename: str) -> str:
    """Remove caracteres perigosos do nome do arquivo."""
    clean = "".join(c for c in filename if c.isalnum() or c in "._- ")
    return clean.strip() or "arquivo"

async def save_upload_file(upload_file: UploadFile) -> Tuple[Path, str, str]:
    """
    Salva o arquivo enviado no diretório de uploads.
    Retorna: (caminho_arquivo, file_id, nome_original)
    """
    file_id = generate_file_id()
    original_name = sanitize_filename(upload_file.filename or "upload.bin")
    file_ext = Path(original_name).suffix.lower()
    
    # Nome seguro salvo em disco
    saved_filename = f"{file_id}_{original_name}"
    file_path = settings.UPLOAD_DIR / saved_filename

    # Salvar em streaming assíncrono para eficiência de memória
    async with aiofiles.open(file_path, "wb") as buffer:
        while chunk := await upload_file.read(1024 * 1024):  # 1MB chunks
            await buffer.write(chunk)

    return file_path, file_id, original_name

def cleanup_old_files():
    """Remove arquivos antigos de uploads, converted e temp."""
    now = time.time()
    cutoff_seconds = settings.FILE_RETENTION_MINUTES * 60
    removed_count = 0

    directories = [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.TEMP_DIR]
    
    for directory in directories:
        if not directory.exists():
            continue
            
        for item in directory.iterdir():
            try:
                if item.is_file():
                    mtime = item.stat().st_mtime
                    if (now - mtime) > cutoff_seconds:
                        item.unlink(missing_ok=True)
                        removed_count += 1
                elif item.is_dir():
                    mtime = item.stat().st_mtime
                    if (now - mtime) > cutoff_seconds:
                        shutil.rmtree(item, ignore_errors=True)
                        removed_count += 1
            except Exception as e:
                logger.error(f"Erro ao limpar arquivo {item}: {e}")

    if removed_count > 0:
        logger.info(f"Limpeza concluída: {removed_count} arquivos expirados removidos.")

def get_file_size_formatted(num_bytes: int) -> str:
    """Retorna tamanho legível (KB, MB, GB)."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"
