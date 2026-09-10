from typing import Dict, List, Set

VIDEO_EXTENSIONS: Set[str] = {
    "mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "m4v", "ts", "3gp", "ogv"
}

AUDIO_EXTENSIONS: Set[str] = {
    "mp3", "wav", "flac", "aac", "ogg", "m4a", "opus", "wma"
}

IMAGE_EXTENSIONS: Set[str] = {
    "jpg", "jpeg", "png", "webp", "avif", "gif", "bmp", "tiff", "tif", "ico", "svg", "heic", "heif"
}

DOCUMENT_EXTENSIONS: Set[str] = {
    "pdf", "docx", "doc", "odt", "rtf", "txt", "xlsx", "xls", "ods", "csv", "pptx", "ppt", "odp", "html", "md"
}

# Mapeamento de extensões para categorias
EXTENSION_CATEGORY_MAP: Dict[str, str] = {}
for ext in VIDEO_EXTENSIONS:
    EXTENSION_CATEGORY_MAP[ext] = "video"
for ext in AUDIO_EXTENSIONS:
    EXTENSION_CATEGORY_MAP[ext] = "audio"
for ext in IMAGE_EXTENSIONS:
    EXTENSION_CATEGORY_MAP[ext] = "image"
for ext in DOCUMENT_EXTENSIONS:
    EXTENSION_CATEGORY_MAP[ext] = "document"

# Conversões recomendadas por categoria / formato de origem
TARGET_FORMATS: Dict[str, List[str]] = {
    "video": ["mp4", "webm", "mkv", "avi", "mov", "gif", "mp3", "wav", "aac"],
    "audio": ["mp3", "wav", "flac", "aac", "ogg", "m4a", "opus"],
    "image": ["png", "jpg", "webp", "avif", "pdf", "gif", "bmp", "tiff", "ico"],
    "document": {
        "text": ["pdf", "docx", "odt", "txt", "html", "rtf"],
        "sheet": ["pdf", "xlsx", "ods", "csv", "html"],
        "presentation": ["pdf", "pptx", "odp"],
        "pdf": ["docx", "txt", "png", "jpg"]
    }
}

def detect_category(extension: str) -> str:
    """Detecta a categoria principal com base na extensão do arquivo."""
    ext = extension.lower().strip(".")
    return EXTENSION_CATEGORY_MAP.get(ext, "unknown")

def get_allowed_targets(extension: str) -> List[str]:
    """Retorna a lista de formatos alvo recomendados para a extensão dada."""
    ext = extension.lower().strip(".")
    category = detect_category(ext)
    
    if category == "video":
        return TARGET_FORMATS["video"]
    elif category == "audio":
        return TARGET_FORMATS["audio"]
    elif category == "image":
        return TARGET_FORMATS["image"]
    elif category == "document":
        if ext in ["pdf"]:
            return TARGET_FORMATS["document"]["pdf"]
        elif ext in ["xlsx", "xls", "ods", "csv"]:
            return TARGET_FORMATS["document"]["sheet"]
        elif ext in ["pptx", "ppt", "odp"]:
            return TARGET_FORMATS["document"]["presentation"]
        else:
            return TARGET_FORMATS["document"]["text"]
    return ["pdf", "zip"]
