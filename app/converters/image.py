import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, List
from PIL import Image, ImageOps
import pillow_heif

# Registrar suporte a HEIC/HEIF no Pillow
pillow_heif.register_heif_opener()

from app.config import settings

logger = logging.getLogger("image_converter")

async def convert_image(
    input_path: Path,
    target_format: str,
    output_filename_base: str,
    quality: int = 90,
    width: Optional[int] = None,
    height: Optional[int] = None,
    maintain_aspect_ratio: bool = True,
    grayscale: bool = False,
    strip_metadata: bool = True
) -> Path:
    """
    Converte imagem usando Pillow ou ImageMagick para formatos avançados/vetoriais.
    """
    target_ext = target_format.lower().strip(".")
    output_filename = f"{output_filename_base}.{target_ext}"
    output_path = settings.OUTPUT_DIR / output_filename

    # Se a entrada for SVG ou a saída precisar de ImageMagick CLI
    is_svg_input = input_path.suffix.lower() == ".svg"
    
    if is_svg_input:
        return await _convert_with_imagemagick(input_path, output_path, target_ext, quality, width, height)

    try:
        with Image.open(input_path) as img:
            # Auto-orientação baseada em EXIF (ex: fotos de celular)
            img = ImageOps.exif_transpose(img)

            # Conversão para escala de cinza se solicitado
            if grayscale:
                img = img.convert("L")

            # Redimensionamento
            if width or height:
                orig_w, orig_h = img.size
                if maintain_aspect_ratio:
                    if width and not height:
                        new_w = width
                        new_h = int((orig_h / orig_w) * width)
                    elif height and not width:
                        new_h = height
                        new_w = int((orig_w / orig_h) * height)
                    else:
                        ratio = min(width / orig_w, height / orig_h)
                        new_w = int(orig_w * ratio)
                        new_h = int(orig_h * ratio)
                else:
                    new_w = width or orig_w
                    new_h = height or orig_h

                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Tratamento de canais de cor
            if target_ext in ["jpg", "jpeg"]:
                if img.mode in ("RGBA", "LA", "P"):
                    # Criar fundo branco para transparência ao salvar em JPEG
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != "RGB" and img.mode != "L":
                    img = img.convert("RGB")

            elif target_ext == "ico":
                # Favicon padrão
                icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
                img.save(output_path, format="ICO", sizes=icon_sizes)
                return output_path

            # Parâmetros de salvamento por formato
            save_kwargs = {}
            if strip_metadata:
                save_kwargs["exif"] = b""

            if target_ext in ["jpg", "jpeg"]:
                save_kwargs.update({"quality": quality, "optimize": True})
                img.save(output_path, format="JPEG", **save_kwargs)
            elif target_ext == "png":
                save_kwargs.update({"optimize": True})
                img.save(output_path, format="PNG", **save_kwargs)
            elif target_ext == "webp":
                save_kwargs.update({"quality": quality, "method": 6})
                img.save(output_path, format="WEBP", **save_kwargs)
            elif target_ext == "avif":
                save_kwargs.update({"quality": quality})
                img.save(output_path, format="AVIF", **save_kwargs)
            elif target_ext == "pdf":
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(output_path, format="PDF")
            else:
                img.save(output_path, format=target_ext.upper(), **save_kwargs)

        return output_path

    except Exception as e:
        logger.warning(f"Tentando fallback para ImageMagick devido a: {e}")
        return await _convert_with_imagemagick(input_path, output_path, target_ext, quality, width, height)

async def _convert_with_imagemagick(
    input_path: Path,
    output_path: Path,
    target_ext: str,
    quality: int = 90,
    width: Optional[int] = None,
    height: Optional[int] = None
) -> Path:
    """Fallback poderoso utilizando a CLI do ImageMagick (convert / magick)."""
    # Descobrir comando disponível (magick ou convert)
    cmd_name = "convert"
    
    cmd = [cmd_name, str(input_path)]

    if width and height:
        cmd.extend(["-resize", f"{width}x{height}"])
    elif width:
        cmd.extend(["-resize", f"{width}"])
    elif height:
        cmd.extend(["-resize", f"x{height}"])

    if target_ext in ["jpg", "jpeg", "webp"]:
        cmd.extend(["-quality", str(quality)])

    # Fundo branco para converter transparência para JPEG
    if target_ext in ["jpg", "jpeg"]:
        cmd.extend(["-background", "white", "-flatten"])

    cmd.append(str(output_path))

    logger.info(f"Executando ImageMagick: {' '.join(cmd)}")
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode(errors="replace")
        logger.error(f"Erro no ImageMagick: {error_msg}")
        raise RuntimeError(f"Falha na conversão com ImageMagick: {error_msg[-500:]}")

    if not output_path.exists():
        raise RuntimeError("Arquivo de imagem de saída não foi gerado.")

    return output_path
