document.addEventListener("DOMContentLoaded", () => {
  // Inicializar ícones Lucide
  lucide.createIcons();

  // Alternador de Tema Claro / Escuro
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      const isDark = document.documentElement.classList.toggle("dark");
      localStorage.setItem("theme", isDark ? "dark" : "light");
      lucide.createIcons();
    });
  }

  // Elementos do DOM
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const fileConfigArea = document.getElementById("fileConfigArea");
  const filesList = document.getElementById("filesList");
  const fileCount = document.getElementById("fileCount");
  const clearFilesBtn = document.getElementById("clearFilesBtn");
  const targetFormatSelect = document.getElementById("targetFormatSelect");
  const startConvertBtn = document.getElementById("startConvertBtn");
  
  // Opções
  const optResolution = document.getElementById("optResolution");
  const resolutionSelect = document.getElementById("resolutionSelect");
  const optQuality = document.getElementById("optQuality");
  const qualitySelect = document.getElementById("qualitySelect");
  const optImageResize = document.getElementById("optImageResize");
  const imageWidth = document.getElementById("imageWidth");
  const optGrayscale = document.getElementById("optGrayscale");
  const grayscaleCheck = document.getElementById("grayscaleCheck");
  const optMuteAudio = document.getElementById("optMuteAudio");
  const muteAudioCheck = document.getElementById("muteAudioCheck");
  const bundleZipCheck = document.getElementById("bundleZipCheck");
  const optBundleZip = document.getElementById("optBundleZip");

  // Progresso & Resultados
  const progressArea = document.getElementById("progressArea");
  const progressStatus = document.getElementById("progressStatus");
  const progressPercent = document.getElementById("progressPercent");
  const resultsArea = document.getElementById("resultsArea");
  const resultsList = document.getElementById("resultsList");
  const batchZipDownloadHolder = document.getElementById("batchZipDownloadHolder");
  const historyList = document.getElementById("historyList");
  const emptyHistoryText = document.getElementById("emptyHistoryText");
  const clearHistoryBtn = document.getElementById("clearHistoryBtn");

  // Estado
  let selectedFiles = [];
  let currentMode = "auto";
  let recentConversions = JSON.parse(sessionStorage.getItem("conversions_history") || "[]");

  // Mapeamento de formatos
  const PRESET_FORMATS = {
    video: [
      { ext: "mp4", label: "MP4 (H.264)" },
      { ext: "webm", label: "WEBM (VP9)" },
      { ext: "mkv", label: "MKV" },
      { ext: "avi", label: "AVI" },
      { ext: "mov", label: "MOV" },
      { ext: "gif", label: "GIF Animado" },
      { ext: "mp3", label: "MP3 (Áudio)" },
      { ext: "wav", label: "WAV (Áudio)" },
      { ext: "aac", label: "AAC (Áudio)" }
    ],
    image: [
      { ext: "webp", label: "WEBP" },
      { ext: "png", label: "PNG" },
      { ext: "jpg", label: "JPG" },
      { ext: "avif", label: "AVIF" },
      { ext: "pdf", label: "PDF" },
      { ext: "ico", label: "ICO" },
      { ext: "bmp", label: "BMP" },
      { ext: "tiff", label: "TIFF" }
    ],
    document: [
      { ext: "pdf", label: "PDF" },
      { ext: "docx", label: "DOCX (Word)" },
      { ext: "odt", label: "ODT" },
      { ext: "xlsx", label: "XLSX (Excel)" },
      { ext: "pptx", label: "PPTX (PowerPoint)" },
      { ext: "txt", label: "TXT" },
      { ext: "html", label: "HTML" },
      { ext: "png", label: "PNG (Páginas)" }
    ]
  };

  renderHistory();

  // Tabs Minimalistas
  document.querySelectorAll(".segmented-tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".segmented-tab").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentMode = btn.dataset.mode;
      updateFormatOptions();
    });
  });

  // Drag & Drop
  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFiles(Array.from(e.target.files));
    }
  });

  clearFilesBtn.addEventListener("click", () => {
    selectedFiles = [];
    fileInput.value = "";
    fileConfigArea.classList.add("hidden");
    resultsArea.classList.add("hidden");
  });

  function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  function handleFiles(files) {
    selectedFiles = files;
    fileCount.textContent = files.length;
    filesList.innerHTML = "";

    files.forEach((file) => {
      const ext = file.name.split('.').pop().toLowerCase();
      const div = document.createElement("div");
      div.className = "flex items-center justify-between p-2 rounded-lg bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800/80 text-xs";
      div.innerHTML = `
        <div class="flex items-center gap-2 truncate pr-2">
          <span class="px-1.5 py-0.2 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 font-mono text-[10px] uppercase">${ext}</span>
          <span class="text-zinc-800 dark:text-zinc-300 truncate font-medium">${file.name}</span>
        </div>
        <span class="text-zinc-400 dark:text-zinc-500 font-mono text-[11px] whitespace-nowrap">${formatBytes(file.size)}</span>
      `;
      filesList.appendChild(div);
    });

    fileConfigArea.classList.remove("hidden");
    resultsArea.classList.add("hidden");

    if (files.length > 1) {
      optBundleZip.classList.remove("hidden");
      optBundleZip.classList.add("flex");
    } else {
      optBundleZip.classList.remove("flex");
      optBundleZip.classList.add("hidden");
    }

    updateFormatOptions();
  }

  function detectCategoryFromFile(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const videoExts = ["mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "3gp", "ts", "mp3", "wav", "flac", "aac", "ogg"];
    const imageExts = ["jpg", "jpeg", "png", "webp", "avif", "gif", "bmp", "tiff", "ico", "svg", "heic", "heif"];
    const docExts = ["pdf", "docx", "doc", "odt", "rtf", "txt", "xlsx", "xls", "ods", "csv", "pptx", "ppt", "odp", "html", "md"];

    if (videoExts.includes(ext)) return "video";
    if (imageExts.includes(ext)) return "image";
    if (docExts.includes(ext)) return "document";
    return "auto";
  }

  function updateFormatOptions() {
    targetFormatSelect.innerHTML = "";

    let modeToUse = currentMode;
    if (modeToUse === "auto" && selectedFiles.length > 0) {
      modeToUse = detectCategoryFromFile(selectedFiles[0].name);
    }

    optResolution.classList.add("hidden");
    optImageResize.classList.add("hidden");
    optMuteAudio.classList.remove("flex");
    optMuteAudio.classList.add("hidden");
    optGrayscale.classList.remove("flex");
    optGrayscale.classList.add("hidden");

    let options = [];
    if (modeToUse === "video") {
      options = PRESET_FORMATS.video;
      optResolution.classList.remove("hidden");
      optMuteAudio.classList.remove("hidden");
      optMuteAudio.classList.add("flex");
    } else if (modeToUse === "image") {
      options = PRESET_FORMATS.image;
      optImageResize.classList.remove("hidden");
      optGrayscale.classList.remove("hidden");
      optGrayscale.classList.add("flex");
    } else if (modeToUse === "document") {
      options = PRESET_FORMATS.document;
    } else {
      options = [
        { ext: "pdf", label: "PDF" },
        { ext: "mp4", label: "MP4" },
        { ext: "mp3", label: "MP3" },
        { ext: "webp", label: "WEBP" },
        { ext: "png", label: "PNG" },
        { ext: "docx", label: "DOCX" }
      ];
    }

    options.forEach(opt => {
      const optionEl = document.createElement("option");
      optionEl.value = opt.ext;
      optionEl.textContent = `${opt.ext.toUpperCase()} — ${opt.label}`;
      targetFormatSelect.appendChild(optionEl);
    });
  }

  // Executar Conversão
  startConvertBtn.addEventListener("click", async () => {
    if (selectedFiles.length === 0) return;

    startConvertBtn.disabled = true;
    startConvertBtn.classList.add("opacity-50");
    progressArea.classList.remove("hidden");
    resultsArea.classList.add("hidden");
    progressPercent.textContent = "Processando";

    const targetFormat = targetFormatSelect.value;
    const quality = qualitySelect.value;
    const resolution = resolutionSelect.value;
    const isGrayscale = grayscaleCheck.checked;
    const isMute = muteAudioCheck.checked;
    const widthVal = imageWidth.value;
    const bundleZip = bundleZipCheck.checked;

    try {
      if (selectedFiles.length === 1) {
        const formData = new FormData();
        formData.append("file", selectedFiles[0]);
        formData.append("target_format", targetFormat);
        formData.append("quality", quality);
        if (resolution) formData.append("resolution", resolution);
        if (widthVal) formData.append("width", widthVal);
        if (isGrayscale) formData.append("grayscale", "true");
        if (isMute) formData.append("mute_audio", "true");

        const res = await fetch("/api/convert", {
          method: "POST",
          body: formData
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || "Falha na conversão.");
        }

        const data = await res.json();
        showSingleResult(data);
        addToHistory(data);
      } else {
        const formData = new FormData();
        selectedFiles.forEach(file => {
          formData.append("files", file);
        });
        formData.append("target_format", targetFormat);
        formData.append("quality", quality);
        if (resolution) formData.append("resolution", resolution);
        formData.append("bundle_zip", bundleZip ? "true" : "false");

        const res = await fetch("/api/convert/batch", {
          method: "POST",
          body: formData
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || "Falha na conversão em lote.");
        }

        const data = await res.json();
        showBatchResults(data);
      }
    } catch (err) {
      alert("Erro na conversão: " + err.message);
    } finally {
      startConvertBtn.disabled = false;
      startConvertBtn.classList.remove("opacity-50");
      progressArea.classList.add("hidden");
    }
  });

  function showSingleResult(data) {
    resultsList.innerHTML = "";
    batchZipDownloadHolder.innerHTML = "";

    const item = document.createElement("div");
    item.className = "flex items-center justify-between p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-xs animate-in";
    item.innerHTML = `
      <div class="truncate pr-3">
        <div class="flex items-center gap-2">
          <span class="px-1.5 py-0.5 rounded bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 font-mono text-[10px] uppercase font-bold">${data.target_format}</span>
          <span class="font-medium text-zinc-900 dark:text-zinc-200 truncate">${data.filename}</span>
        </div>
        <div class="text-[11px] text-zinc-400 dark:text-zinc-500 mt-0.5 font-mono">${data.size}</div>
      </div>
      <a href="${data.download_url}" download class="btn-press shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-900 font-semibold text-xs shadow-sm transition">
        <i data-lucide="download" class="w-3.5 h-3.5"></i>
        Baixar
      </a>
    `;
    resultsList.appendChild(item);
    resultsArea.classList.remove("hidden");
    lucide.createIcons();
  }

  function showBatchResults(data) {
    resultsList.innerHTML = "";
    batchZipDownloadHolder.innerHTML = "";

    if (data.zip_download_url) {
      batchZipDownloadHolder.innerHTML = `
        <a href="${data.zip_download_url}" download class="btn-press inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-900 font-semibold text-xs transition">
          <i data-lucide="archive" class="w-3 h-3"></i>
          Baixar Pacote (.ZIP)
        </a>
      `;
    }

    data.results.forEach(res => {
      const item = document.createElement("div");
      item.className = "flex items-center justify-between p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-xs";
      if (res.status === "success") {
        item.innerHTML = `
          <div class="truncate pr-2">
            <span class="text-zinc-900 dark:text-zinc-200 font-medium truncate">${res.filename}</span>
            <span class="text-zinc-400 dark:text-zinc-500 ml-1.5 font-mono text-[11px]">(${res.size})</span>
          </div>
          <a href="${res.download_url}" download class="btn-press text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white font-medium flex items-center gap-1 text-[11px]">
            <i data-lucide="download" class="w-3 h-3"></i>
            Baixar
          </a>
        `;
        addToHistory({
          filename: res.filename,
          size: res.size,
          download_url: res.download_url,
          target_format: res.filename.split('.').pop()
        });
      } else {
        item.innerHTML = `
          <div class="text-rose-500 truncate pr-2 text-[11px]">
            Erro: ${res.original_filename} (${res.error})
          </div>
        `;
      }
      resultsList.appendChild(item);
    });

    resultsArea.classList.remove("hidden");
    lucide.createIcons();
  }

  function addToHistory(item) {
    recentConversions.unshift(item);
    if (recentConversions.length > 6) recentConversions.pop();
    sessionStorage.setItem("conversions_history", JSON.stringify(recentConversions));
    renderHistory();
  }

  clearHistoryBtn.addEventListener("click", () => {
    recentConversions = [];
    sessionStorage.removeItem("conversions_history");
    renderHistory();
  });

  function renderHistory() {
    if (recentConversions.length === 0) {
      emptyHistoryText.style.display = "block";
      clearHistoryBtn.classList.add("hidden");
      historyList.innerHTML = "";
      historyList.appendChild(emptyHistoryText);
      return;
    }

    emptyHistoryText.style.display = "none";
    clearHistoryBtn.classList.remove("hidden");
    historyList.innerHTML = "";

    recentConversions.forEach(item => {
      const div = document.createElement("div");
      div.className = "flex items-center justify-between p-2 rounded-lg bg-white dark:bg-zinc-950 border border-zinc-200/80 dark:border-zinc-900 text-xs hover:border-zinc-300 dark:hover:border-zinc-800 transition";
      div.innerHTML = `
        <div class="flex items-center gap-2 truncate pr-2">
          <span class="px-1 py-0.5 rounded bg-zinc-100 dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 font-mono text-[9px] uppercase">${item.target_format}</span>
          <span class="text-zinc-700 dark:text-zinc-400 truncate text-[11px]">${item.filename}</span>
          <span class="text-zinc-400 dark:text-zinc-600 font-mono text-[10px]">${item.size || ''}</span>
        </div>
        <a href="${item.download_url}" download class="btn-press text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 flex items-center gap-1 text-[11px]">
          <i data-lucide="download" class="w-3 h-3"></i>
          Baixar
        </a>
      `;
      historyList.appendChild(div);
    });
    lucide.createIcons();
  }
});
