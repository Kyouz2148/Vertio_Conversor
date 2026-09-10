import asyncio
import logging
import zipfile
import shutil
from pathlib import Path
from typing import Optional, List

from app.config import settings

logger = logging.getLogger("document_converter")

async def convert_document(
    input_path: Path,
    target_format: str,
    output_filename_base: str
) -> Path:
    """
    Converte documentos de escritório, PDFs e textos usando LibreOffice, pdf2docx ou poppler.
    """
    input_ext = input_path.suffix.lower().strip(".")
    target_ext = target_format.lower().strip(".")
    
    # 1. Caso especial: PDF para DOCX (usando a biblioteca dedicada pdf2docx para máxima fidelidade)
    if input_ext == "pdf" and target_ext in ["docx", "doc"]:
        return await _convert_pdf_to_docx(input_path, output_filename_base)

    # 2. Caso especial: PDF para imagens (PNG / JPG por página)
    if input_ext == "pdf" and target_ext in ["png", "jpg", "jpeg"]:
        return await _convert_pdf_to_images(input_path, output_filename_base, target_ext)

    # 3. Conversão padrão via LibreOffice headless
    return await _convert_with_libreoffice(input_path, target_ext, output_filename_base)

async def _convert_pdf_to_docx(input_path: Path, output_filename_base: str) -> Path:
    """Converte PDF para DOCX preservando layout, tabelas e fontes."""
    output_path = settings.OUTPUT_DIR / f"{output_filename_base}.docx"
    
    def _run_pdf2docx():
        from pdf2docx import Converter
        cv = Converter(str(input_path))
        cv.convert(str(output_path), start=0, end=None)
        cv.close()

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run_pdf2docx)

    if not output_path.exists():
        raise RuntimeError("Falha ao converter PDF para DOCX.")

    return output_path

async def _convert_pdf_to_images(input_path: Path, output_filename_base: str, image_format: str) -> Path:
    """Extrai todas as páginas do PDF como imagens individuais (PNG/JPEG) e empacota em ZIP se houver mais de 1 página."""
    temp_dir = settings.TEMP_DIR / f"pdf_imgs_{output_filename_base}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    img_fmt_flag = "-png" if image_format == "png" else "-jpeg"
    prefix = str(temp_dir / "page")

    cmd = ["pdftoppm", img_fmt_flag, "-r", "150", str(input_path), prefix]
    
    logger.info(f"Executando pdftoppm: {' '.join(cmd)}")
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    generated_images = sorted(list(temp_dir.glob(f"page*.{image_format}")))
    if not generated_images:
        # Tenta pegar qualquer formato de imagem gerada
        generated_images = sorted(list(temp_dir.glob("page*.*")))

    if not generated_images:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Nenhuma página pôde ser extraída do PDF: {stderr.decode(errors='replace')}")

    # Se tiver apenas 1 página, retorna a própria imagem
    if len(generated_images) == 1:
        single_img = generated_images[0]
        final_path = settings.OUTPUT_DIR / f"{output_filename_base}.{image_format}"
        shutil.move(str(single_img), str(final_path))
        shutil.rmtree(temp_dir, ignore_errors=True)
        return final_path

    # Se tiver múltiplas páginas, cria um arquivo ZIP com todas elas
    zip_path = settings.OUTPUT_DIR / f"{output_filename_base}_paginas.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for idx, img in enumerate(generated_images, 1):
            zipf.write(img, arcname=f"pagina_{idx:03d}.{image_format}")

    shutil.rmtree(temp_dir, ignore_errors=True)
    return zip_path

async def _convert_with_libreoffice(
    input_path: Path,
    target_ext: str,
    output_filename_base: str
) -> Path:
    """Executa o LibreOffice em modo headless para converter planilhas, textos e apresentações."""
    # Mapeamento de formatos especiais no LibreOffice
    format_filter = target_ext
    if target_ext == "pdf":
        format_filter = "pdf"
    elif target_ext == "txt":
        format_filter = "txt:Text"
    elif target_ext == "html":
        format_filter = "html"

    # LibreOffice salva o arquivo com o mesmo nome base do arquivo de entrada
    cmd = [
        "libreoffice",
        "--headless",
        "--invisible",
        "--nodefault",
        "--nofirststartwizard",
        "--nolockcheck",
        "--nologo",
        "--convert-to", format_filter,
        "--outdir", str(settings.OUTPUT_DIR),
        str(input_path)
    ]

    logger.info(f"Executando LibreOffice: {' '.join(cmd)}")
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120.0)
    except asyncio.TimeoutError:
        process.kill()
        raise RuntimeError("Tempo limite excedido na conversão com LibreOffice.")

    # O LibreOffice gera o arquivo com o nome base do input_path
    generated_file = settings.OUTPUT_DIR / f"{input_path.stem}.{target_ext}"
    target_file = settings.OUTPUT_DIR / f"{output_filename_base}.{target_ext}"

    if generated_file.exists():
        if generated_file != target_file:
            if target_file.exists():
                target_file.unlink()
            generated_file.rename(target_file)
        return target_file

    # Caso o LibreOffice tenha gerado com outro padrão
    matches = list(settings.OUTPUT_DIR.glob(f"{input_path.stem}.*"))
    if matches and matches[0].exists():
        matches[0].rename(target_file)
        return target_file

    error_detail = stderr.decode(errors="replace") if stderr else "Sem detalhes de erro."
    raise RuntimeError(f"LibreOffice não gerou o arquivo convertido. Detalhes: {error_detail}")
