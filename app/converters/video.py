import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from app.config import settings

logger = logging.getLogger("video_converter")

RESOLUTIONS: Dict[str, str] = {
    "1080p": "scale=-2:1080",
    "720p": "scale=-2:720",
    "480p": "scale=-2:480",
    "360p": "scale=-2:360",
}

QUALITY_CRF: Dict[str, int] = {
    "high": 18,
    "medium": 23,
    "low": 28,
}

AUDIO_BITRATES: Dict[str, str] = {
    "128k": "128k",
    "192k": "192k",
    "256k": "256k",
    "320k": "320k"
}

async def convert_video(
    input_path: Path,
    target_format: str,
    output_filename_base: str,
    resolution: Optional[str] = None,
    quality: str = "medium",
    audio_bitrate: str = "192k",
    mute_audio: bool = False,
    fps: Optional[int] = None,
    speed: Optional[str] = None
) -> Path:
    """
    Converte ou extrai áudio de arquivos de vídeo/áudio usando FFmpeg.
    """
    target_ext = target_format.lower().strip(".")
    output_filename = f"{output_filename_base}.{target_ext}"
    output_path = settings.OUTPUT_DIR / output_filename

    # Caso especial: Vídeo para GIF de alta qualidade
    if target_ext == "gif":
        return await _convert_to_gif(input_path, output_path, resolution, fps)

    # Caso especial: Extração de áudio puro
    is_audio_output = target_ext in ["mp3", "wav", "aac", "ogg", "flac", "m4a", "opus"]

    cmd = ["ffmpeg", "-y", "-i", str(input_path)]

    if is_audio_output:
        cmd.extend(["-vn"])  # Sem vídeo
        if target_ext == "mp3":
            cmd.extend(["-c:a", "libmp3lame", "-b:a", AUDIO_BITRATES.get(audio_bitrate, "192k")])
        elif target_ext == "aac":
            cmd.extend(["-c:a", "aac", "-b:a", AUDIO_BITRATES.get(audio_bitrate, "192k")])
        elif target_ext == "flac":
            cmd.extend(["-c:a", "flac"])
        elif target_ext == "wav":
            cmd.extend(["-c:a", "pcm_s16le"])
        elif target_ext == "ogg":
            cmd.extend(["-c:a", "libvorbis", "-q:a", "5"])
        elif target_ext == "opus":
            cmd.extend(["-c:a", "libopus", "-b:a", AUDIO_BITRATES.get(audio_bitrate, "128k")])
    else:
        # Configuração de vídeo
        video_filters = []
        if resolution and resolution in RESOLUTIONS:
            video_filters.append(RESOLUTIONS[resolution])

        if fps:
            video_filters.append(f"fps={fps}")

        if video_filters:
            cmd.extend(["-vf", ",".join(video_filters)])

        # Codecs de vídeo e taxa de compressão
        crf = QUALITY_CRF.get(quality, 23)
        if target_ext in ["mp4", "mkv", "mov"]:
            cmd.extend(["-c:v", "libx264", "-crf", str(crf), "-preset", "medium", "-pix_fmt", "yuv420p"])
        elif target_ext == "webm":
            cmd.extend(["-c:v", "libvpx-vp9", "-crf", str(crf + 7), "-b:v", "0"])
        elif target_ext == "avi":
            cmd.extend(["-c:v", "mpeg4", "-qscale:v", "3"])

        # Configuração de áudio do vídeo
        if mute_audio:
            cmd.append("-an")
        else:
            if target_ext == "webm":
                cmd.extend(["-c:a", "libopus"])
            else:
                cmd.extend(["-c:a", "aac", "-b:a", AUDIO_BITRATES.get(audio_bitrate, "192k")])

    cmd.append(str(output_path))

    logger.info(f"Executando FFmpeg: {' '.join(cmd)}")
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode(errors="replace")
        logger.error(f"Erro no FFmpeg: {error_msg}")
        raise RuntimeError(f"Falha na conversão com FFmpeg: {error_msg[-500:]}")

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("Arquivo de saída não foi gerado ou está vazio.")

    return output_path

async def _convert_to_gif(
    input_path: Path,
    output_path: Path,
    resolution: Optional[str] = None,
    fps: Optional[int] = None
) -> Path:
    """
    Gera GIF de alta definição utilizando a técnica palettegen e paletteuse do FFmpeg.
    """
    fps_val = fps or 15
    scale_filter = RESOLUTIONS.get(resolution, "scale=-2:480")

    filter_complex = f"fps={fps_val},{scale_filter},split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer"

    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-filter_complex", filter_complex,
        str(output_path)
    ]

    logger.info(f"Gerando GIF: {' '.join(cmd)}")
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode(errors="replace")
        logger.error(f"Erro gerando GIF: {error_msg}")
        raise RuntimeError(f"Falha ao gerar GIF: {error_msg[-500:]}")

    return output_path
