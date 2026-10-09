const fileInput = document.querySelector("#file-input");
const dropzone = document.querySelector("#dropzone");
const fileList = document.querySelector("#file-list");
const convertButton = document.querySelector("#convert-button");
const clearButton = document.querySelector("#clear-button");
const apiStatus = document.querySelector("#api-status");

// Definido em config.js: "" quando a API roda no mesmo servidor, ou a URL do Render
const API_BASE_URL = window.API_BASE_URL || "";

const maxFileSize = 50 * 1024 * 1024;
const maxFiles = 5;
let selectedFiles = [];

function formatBytes(bytes) {
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function renderFiles(state = "Aguardando") {
  fileList.innerHTML = "";

  if (!selectedFiles.length) {
    fileList.innerHTML = '<li class="empty-state">Nenhum arquivo selecionado ainda.</li>';
    convertButton.disabled = true;
    return;
  }

  selectedFiles.forEach((file) => {
    const item = document.createElement("li");
    const info = document.createElement("div");
    const name = document.createElement("strong");
    const meta = document.createElement("span");
    const fileState = document.createElement("span");

    name.textContent = file.name;
    meta.className = "file-meta";
    meta.textContent = formatBytes(file.size);
    fileState.className = "file-state";
    fileState.textContent = state;

    info.append(name, meta);
    item.append(info, fileState);
    fileList.appendChild(item);
  });

  convertButton.disabled = false;
}

function addFiles(files) {
  const pdfs = Array.from(files).filter((file) => {
    const hasPdfType = file.type === "application/pdf";
    const hasPdfExtension = file.name.toLowerCase().endsWith(".pdf");
    return hasPdfType || hasPdfExtension;
  });

  const validFiles = pdfs.filter((file) => file.size <= maxFileSize);
  const availableSlots = Math.max(maxFiles - selectedFiles.length, 0);
  selectedFiles = [...selectedFiles, ...validFiles.slice(0, availableSlots)];
  renderFiles(validFiles.length && availableSlots ? "Aguardando" : "Arquivo invalido");
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function getEpubName(fileName) {
  return fileName.replace(/\.pdf$/i, "") + ".epub";
}

async function convertFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  let response;

  try {
    response = await fetch(`${API_BASE_URL}/api/convert`, {
      method: "POST",
      body: formData,
    });
  } catch {
    // Falha de rede: servidor fora do ar, dormindo ou sem internet
    marcarServidor("offline");
    throw new Error("Servidor indisponivel no momento. Tente de novo em instantes.");
  }

  if (!response.ok) {
    let message = "Nao foi possivel converter este arquivo.";
    const text = await response.text();

    if (text) {
      try {
        const error = JSON.parse(text);
        message = error.detail || message;
      } catch {
        message = text;
      }
    }

    throw new Error(message);
  }

  const blob = await response.blob();
  downloadBlob(blob, getEpubName(file.name));
}

fileInput.addEventListener("change", (event) => {
  addFiles(event.target.files);
  fileInput.value = "";
});

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("dragging");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragging");
});

dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("dragging");
  addFiles(event.dataTransfer.files);
});

clearButton.addEventListener("click", () => {
  selectedFiles = [];
  /*
 * Status do servidor de conversao.
 * No plano gratuito do Render o servidor "dorme" sem uso e leva ate ~1 minuto para acordar.
 * Ao abrir a pagina, ja mandamos um ping para ele ir acordando enquanto a pessoa escolhe o PDF.
 */
const TEXTOS_STATUS = {
  verificando: "Conectando ao servidor…",
  acordando: "Acordando o servidor…",
  online: "Servidor online",
  offline: "Servidor indisponivel",
};

function marcarServidor(estado) {
  if (!apiStatus) {
    return;
  }

  apiStatus.dataset.estado = estado;
  apiStatus.textContent = TEXTOS_STATUS[estado];
}

async function acordarServidor() {
  const inicio = Date.now();
  const limiteMs = 90 * 1000;

  while (Date.now() - inicio < limiteMs) {
    try {
      const controle = new AbortController();
      const espera = setTimeout(() => controle.abort(), 15000);
      const resposta = await fetch(`${API_BASE_URL}/api/health`, { signal: controle.signal, cache: "no-store" });
      clearTimeout(espera);

      if (resposta.ok) {
        marcarServidor("online");
        return;
      }
    } catch {
      // ainda acordando: tenta de novo
    }

    marcarServidor("acordando");
    await new Promise((resolve) => setTimeout(resolve, 5000));
  }

  marcarServidor("offline");
}

renderFiles();
acordarServidor();
});

convertButton.addEventListener("click", async () => {
  if (!selectedFiles.length) {
    return;
  }

  convertButton.disabled = true;
  convertButton.textContent = "Convertendo...";

  for (const file of selectedFiles) {
    renderFiles(`Convertendo ${file.name}`);

    try {
      await convertFile(file);
      renderFiles("Download iniciado");
    } catch (error) {
      renderFiles(error.message);
      break;
    }
  }

  if (selectedFiles.length) {
    convertButton.textContent = "Converter para EPUB";
    convertButton.disabled = false;
  }
});

renderFiles();
