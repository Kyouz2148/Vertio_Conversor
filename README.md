# 🚀 Vertio-conversor (Docker)

Imagem Docker: `kyouz2148/vertio-conversor:latest`

Um ecossistema completo e autocontido em Docker para conversão de **Vídeos**, **Áudios**, **Imagens** e **Documentos do Office / PDFs**. Conta com uma **Interface Web Moderna (Dark Mode)**, suporte a arrastar e soltar (Drag & Drop), processamento em lote e uma **API REST com Swagger interativo**.

---

## 🌟 Recursos Principais

### 🎬 Vídeo & Áudio (FFmpeg)
* **Formatos de Entrada:** `MP4`, `MKV`, `AVI`, `WEBM`, `MOV`, `FLV`, `WMV`, `3GP`, `TS`, `M4V`, `OGV` e mais.
* **Formatos de Saída:** `MP4` (H.264), `WEBM` (VP9), `MKV`, `AVI`, `MOV`, `GIF` animado de alta fidelidade.
* **Extração de Áudio:** Extraia o som de vídeos diretamente para `MP3`, `WAV`, `FLAC`, `AAC`, `OGG`, `M4A`, `OPUS`.
* **Ajustes:** Resolução (`1080p`, `720p`, `480p`, `360p`), presets de qualidade (CRF ajustado), taxa de bits de áudio e opção para silenciar vídeo.
* **Gerador de GIF Otimizado:** Utiliza algoritmo de paleta personalizada (`palettegen` / `paletteuse`) para GIFs nítidos sem perda de cores.

### 🖼️ Imagens (Pillow + ImageMagick)
* **Formatos de Entrada:** `PNG`, `JPG/JPEG`, `WEBP`, `AVIF`, `GIF`, `BMP`, `TIFF`, `ICO`, `SVG` (vetorial), `HEIC`/`HEIF` (fotos de iPhone).
* **Formatos de Saída:** `WEBP`, `PNG`, `JPG`, `AVIF`, `PDF`, `ICO` (Favicons multi-resolução), `BMP`, `TIFF`.
* **Ajustes:** Redimensionamento com preservação de aspecto, slider de qualidade (1–100%), conversão para preto e branco (escala de cinza) e remoção automática de metadados EXIF.

### 📄 Documentos & Office (LibreOffice Headless + Poppler + pdf2docx)
* **Textos:** `DOCX`, `DOC`, `ODT`, `RTF`, `TXT`, `HTML` ➔ `PDF`, `DOCX`, `ODT`, `TXT`, `HTML`.
* **Planilhas:** `XLSX`, `XLS`, `ODS`, `CSV` ➔ `PDF`, `XLSX`, `ODS`, `CSV`, `HTML`.
* **Apresentações:** `PPTX`, `PPT`, `ODP` ➔ `PDF`, `PPTX`, `ODP`.
* **PDF para Word (DOCX):** Extração avançada com reconstrução de tabelas, imagens e layout.
* **PDF para Imagens:** Transforma cada página do PDF em `PNG` ou `JPG`. Se houver mais de uma página, empacota tudo automaticamente em um arquivo `.ZIP`.

### ⚡ Outros Destaques
* **Interface Web Fluida:** Desenvolvida em Tailwind CSS com feedback em tempo real e modo escuro.
* **Conversão em Lote:** Selecione dezenas de arquivos de uma vez e baixe os resultados convertidos individualmente ou agrupados em um único `.ZIP`.
* **Auto-Limpeza Inteligente:** Rotina em segundo plano que remove automaticamente arquivos temporários e convertidos após o tempo configurado (evita que o disco encha).
* **Documentação Swagger:** Navegue e teste a API diretamente em `/docs`.

---

## 📁 Estrutura do Projeto

```text
Conversor/
├── Dockerfile                  # Imagem com FFmpeg, LibreOffice, ImageMagick, Poppler e fontes
├── docker-compose.yml          # Orquestração do contêiner, volumes e portas
├── requirements.txt            # Dependências Python (FastAPI, Pillow, pdf2docx, etc.)
├── .env.example                # Variáveis de ambiente de exemplo
├── .dockerignore               # Arquivos ignorados no build
├── README.md                   # Esta documentação
├── app/
│   ├── main.py                 # FastAPI, endpoints de conversão, lote e limpeza
│   ├── config.py               # Configurações de ambiente e diretórios
│   ├── converters/
│   │   ├── video.py            # Motor FFmpeg (vídeos, áudios e gifs)
│   │   ├── image.py            # Motor Pillow & ImageMagick (imagens e vetores)
│   │   └── document.py         # Motor LibreOffice & Poppler (docs e PDFs)
│   ├── utils/
│   │   ├── file_manager.py     # Upload assíncrono, limpeza e geração de IDs
│   │   └── mime_types.py       # Mapeamento e detecção automática de formatos
│   ├── static/
│   │   ├── css/style.css       # Estilos complementares
│   │   └── js/app.js           # Lógica do frontend, Drag & Drop e progresso
│   └── templates/
│       └── index.html          # Interface web responsiva
└── storage/                    # Montado no contêiner (persistência e cache)
    ├── uploads/
    ├── converted/
    └── temp/
```

---

## 🚀 Como Executar com Docker

### 1. Iniciar com Docker Compose (Recomendado)

Abra o terminal na pasta do projeto e execute:

```bash
docker compose up -d --build
```

### 2. Acessar os Serviços

* **Painel Web:** [http://localhost:8000](http://localhost:8000)
* **Documentação Interativa da API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Healthcheck & Status de Motores:** [http://localhost:8000/api/status](http://localhost:8000/api/status)

---

## ⚙️ Variáveis de Ambiente

As seguintes variáveis podem ser ajustadas no [docker-compose.yml](file:///C:/Users/alanh/Desktop/Projetos/Conversor/docker-compose.yml) ou criando um arquivo `.env`:

| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `PORT` | `8000` | Porta na qual a API responderá |
| `MAX_UPLOAD_SIZE_MB` | `2048` | Tamanho máximo permitido de upload (em MB) |
| `FILE_RETENTION_MINUTES` | `60` | Tempo (minutos) até os arquivos de upload/saída serem apagados |
| `CLEANUP_INTERVAL_MINUTES`| `15` | Frequência em que o script de limpeza é disparado |

---

## 🌐 Exemplos de Uso da API (cURL / Python)

### 1. Converter um Vídeo para MP4 (cURL)
```bash
curl -X POST "http://localhost:8000/api/convert" \
  -F "file=@meu_video.mov" \
  -F "target_format=mp4" \
  -F "resolution=1080p" \
  -F "quality=high"
```

### 2. Extrair Áudio MP3 de um Vídeo (cURL)
```bash
curl -X POST "http://localhost:8000/api/convert" \
  -F "file=@aula.mp4" \
  -F "target_format=mp3" \
  -F "audio_bitrate=320k"
```

### 3. Converter Imagem PNG para WebP Otimizado (cURL)
```bash
curl -X POST "http://localhost:8000/api/convert" \
  -F "file=@foto.png" \
  -F "target_format=webp" \
  -F "quality=85"
```

### 4. Converter Documento DOCX para PDF (cURL)
```bash
curl -X POST "http://localhost:8000/api/convert" \
  -F "file=@proposta.docx" \
  -F "target_format=pdf"
```

### 5. Exemplo de Integração em Python
```python
import requests

url = "http://localhost:8000/api/convert"

files = {'file': open('documento.pdf', 'rb')}
data = {'target_format': 'docx'}

response = requests.post(url, files=files, data=data)
result = response.json()

print(f"Arquivo convertido: {result['filename']}")
print(f"Link para download: http://localhost:8000{result['download_url']}")
```

---

## 🛠️ Comandos Úteis do Docker

* **Visualizar logs em tempo real:**
  ```bash
  docker compose logs -f
  ```
* **Reiniciar o contêiner:**
  ```bash
  docker compose restart
  ```
* **Parar o contêiner:**
  ```bash
  docker compose down
  ```
* **Reconstruir sem usar cache:**
  ```bash
  docker compose build --no-cache
  docker compose up -d
  ```
