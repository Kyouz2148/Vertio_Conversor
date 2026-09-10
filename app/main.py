import os
import shutil
import asyncio
import logging
import zipfile
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.utils.mime_types import detect_category, get_allowed_targets, EXTENSION_CATEGORY_MAP
from app.utils.file_manager import (
    save_upload_file,
    cleanup_old_files,
    get_file_size_formatted,
    generate_file_id,
    sanitize_filename
)
from app.converters.video import convert_video
from app.converters.image import convert_image
from app.converters.document import convert_document

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("conversor_api")

# Rotina de limpeza em segundo plano periódica
async def periodic_cleanup_task():
    while True:
        try:
            cleanup_old_files()
        except Exception as e:
            logger.error(f"Erro na limpeza periódica: {e}")
        await asyncio.sleep(settings.CLEANUP_INTERVAL_MINUTES * 60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialização: criar tarefas em segundo plano
    cleanup_job = asyncio.create_task(periodic_cleanup_task())
    logger.info("Sistema de conversão iniciado com sucesso.")
    yield
    # Finalização
    cleanup_job.cancel()
    logger.info("Sistema de conversão finalizado.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API Completa para conversão de Vídeos, Áudios, Imagens e Documentos",
    lifespan=lifespan
)

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar Arquivos Estáticos e Templates
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renderiza o Painel Web do Conversor."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "max_size_mb": settings.MAX_UPLOAD_SIZE_MB
        }
    )

@app.get("/api/status")
async def get_system_status():
    """Verifica status de ferramentas instaladas no contêiner e espaço em disco."""
    tools = {
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "libreoffice": shutil.which("libreoffice") is not None,
        "imagemagick": (shutil.which("convert") is not None) or (shutil.which("magick") is not None),
        "pdftoppm": shutil.which("pdftoppm") is not None
    }
    
    total, used, free = shutil.disk_usage(settings.STORAGE_DIR)
    
    return {
        "status": "online",
        "version": settings.APP_VERSION,
        "tools_ready": tools,
        "storage": {
            "total": get_file_size_formatted(total),
            "used": get_file_size_formatted(used),
            "free": get_file_size_formatted(free)
        },
        "supported_extensions": list(EXTENSION_CATEGORY_MAP.keys())
    }

@app.get("/api/detect-format")
async def detect_file_format(filename: str):
    """Detecta a categoria e retorna formatos de saída compatíveis para o arquivo."""
    ext = Path(filename).suffix.lower().strip(".")
    category = detect_category(ext)
    targets = get_allowed_targets(ext)
    return {
        "filename": filename,
        "extension": ext,
        "category": category,
        "allowed_targets": targets
    }

@app.post("/api/convert")
async def convert_single_file(
    file: UploadFile = File(...),
    target_format: str = Form(...),
    quality: Optional[str] = Form("medium"),
    resolution: Optional[str] = Form(None),
    audio_bitrate: Optional[str] = Form("192k"),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    maintain_aspect_ratio: bool = Form(True),
    grayscale: bool = Form(False),
    mute_audio: bool = Form(False),
    fps: Optional[int] = Form(None)
):
    """
    Endpoint principal e universal de conversão de arquivos.
    Detecta automaticamente se é vídeo, áudio, imagem ou documento e processa com a engine adequada.
    """
    input_path, file_id, original_name = await save_upload_file(file)
    input_ext = Path(original_name).suffix.lower().strip(".")
    category = detect_category(input_ext)
    
    output_base_name = f"{Path(original_name).stem}_{file_id}"
    target_fmt = target_format.lower().strip(".")

    try:
        if category in ["video", "audio"]:
            output_path = await convert_video(
                input_path=input_path,
                target_format=target_fmt,
                output_filename_base=output_base_name,
                resolution=resolution,
                quality=quality or "medium",
                audio_bitrate=audio_bitrate or "192k",
                mute_audio=mute_audio,
                fps=fps
            )
        elif category == "image":
            # Para imagem, quality é convertido para inteiro se for número
            img_quality = 90
            if quality and quality.isdigit():
                img_quality = int(quality)
            elif quality == "high":
                img_quality = 95
            elif quality == "low":
                img_quality = 65

            output_path = await convert_image(
                input_path=input_path,
                target_format=target_fmt,
                output_filename_base=output_base_name,
                quality=img_quality,
                width=width,
                height=height,
                maintain_aspect_ratio=maintain_aspect_ratio,
                grayscale=grayscale
            )
        elif category == "document":
            output_path = await convert_document(
                input_path=input_path,
                target_format=target_fmt,
                output_filename_base=output_base_name
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Extensão '.{input_ext}' não suportada ou não reconhecida."
            )

        file_size = output_path.stat().st_size
        return {
            "status": "success",
            "filename": output_path.name,
            "original_filename": original_name,
            "category": category,
            "target_format": target_fmt,
            "size": get_file_size_formatted(file_size),
            "size_bytes": file_size,
            "download_url": f"/api/download/{output_path.name}"
        }

    except Exception as e:
        logger.exception("Erro durante a conversão do arquivo.")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Remover o arquivo de upload original para poupar espaço
        if input_path.exists():
            input_path.unlink(missing_ok=True)

@app.post("/api/convert/batch")
async def convert_batch_files(
    files: List[UploadFile] = File(...),
    target_format: str = Form(...),
    quality: Optional[str] = Form("medium"),
    resolution: Optional[str] = Form(None),
    audio_bitrate: Optional[str] = Form("192k"),
    bundle_zip: bool = Form(True)
):
    """
    Conversão de múltiplos arquivos em lote.
    Pode retornar a lista de downloads individuais ou um ZIP consolidado.
    """
    results = []
    converted_paths = []
    batch_id = generate_file_id()
    target_fmt = target_format.lower().strip(".")

    for file in files:
        input_path, file_id, original_name = await save_upload_file(file)
        input_ext = Path(original_name).suffix.lower().strip(".")
        category = detect_category(input_ext)
        output_base_name = f"{Path(original_name).stem}_{file_id}"

        try:
            if category in ["video", "audio"]:
                out_path = await convert_video(
                    input_path=input_path,
                    target_format=target_fmt,
                    output_filename_base=output_base_name,
                    resolution=resolution,
                    quality=quality or "medium",
                    audio_bitrate=audio_bitrate or "192k"
                )
            elif category == "image":
                out_path = await convert_image(
                    input_path=input_path,
                    target_format=target_fmt,
                    output_filename_base=output_base_name
                )
            elif category == "document":
                out_path = await convert_document(
                    input_path=input_path,
                    target_format=target_fmt,
                    output_filename_base=output_base_name
                )
            else:
                continue

            converted_paths.append(out_path)
            results.append({
                "original_filename": original_name,
                "status": "success",
                "filename": out_path.name,
                "download_url": f"/api/download/{out_path.name}",
                "size": get_file_size_formatted(out_path.stat().st_size)
            })
        except Exception as e:
            results.append({
                "original_filename": original_name,
                "status": "error",
                "error": str(e)
            })
        finally:
            if input_path.exists():
                input_path.unlink(missing_ok=True)

    # Empacotar em ZIP se solicitado
    zip_url = None
    if bundle_zip and converted_paths:
        zip_filename = f"lote_convertido_{batch_id}.zip"
        zip_file_path = settings.OUTPUT_DIR / zip_filename
        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for c_path in converted_paths:
                zipf.write(c_path, arcname=c_path.name)
        zip_url = f"/api/download/{zip_filename}"

    return {
        "total_files": len(files),
        "successful": len(converted_paths),
        "results": results,
        "zip_download_url": zip_url
    }

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Permite download do arquivo convertido com cabeçalhos apropriados."""
    safe_name = sanitize_filename(filename)
    file_path = settings.OUTPUT_DIR / safe_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado ou já expirado.")

    return FileResponse(
        path=file_path,
        filename=safe_name,
        media_type="application/octet-stream"
    )
