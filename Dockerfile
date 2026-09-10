# ==============================================================================
# Dockerfile: Conversor Universal Multimídia & Documentos
# Motores: FFmpeg, LibreOffice, ImageMagick, Poppler-Utils & Python FastAPI
# ==============================================================================

FROM python:3.11-slim-bookworm

# Evitar prompts interativos durante instalação do apt
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/appuser

# Instalação de dependências nativas
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Motor de Vídeo e Áudio
    ffmpeg \
    # Motor de Documentos (LibreOffice headless com suporte a texto, planilhas e apresentações)
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    # Fontes essenciais para renderização idêntica de documentos do Office
    fonts-liberation \
    fonts-dejavu \
    fonts-noto \
    # Motor de Imagens e Vetores
    imagemagick \
    # Motor de PDF e Páginas (pdftoppm, pdfinfo)
    poppler-utils \
    # Ferramentas auxiliares
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Ajustar política de segurança do ImageMagick para permitir leitura/escrita de PDFs
RUN if [ -f /etc/ImageMagick-6/policy.xml ]; then \
        sed -i 's/<policy domain="coder" rights="none" pattern="PDF" \/>/<policy domain="coder" rights="read|write" pattern="PDF" \/>/g' /etc/ImageMagick-6/policy.xml; \
    fi

# Criar usuário não-root seguro para rodar o LibreOffice e o servidor web
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/storage/uploads /app/storage/converted /app/storage/temp && \
    chown -R appuser:appuser /app /home/appuser

WORKDIR /app

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código-fonte da aplicação
COPY --chown=appuser:appuser . .

# Alternar para o usuário não-root
USER appuser

# Expor porta padrão
EXPOSE 8000

# Verificação de integridade (Healthcheck)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/status || exit 1

# Inicialização do servidor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
