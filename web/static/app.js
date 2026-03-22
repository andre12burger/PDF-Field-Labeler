const get = (id) => document.getElementById(id);

// Modo de preview via servidor (sem PDF.js): imagens produzidas pelo endpoint /api/preview/page.
const pdfRenderAvailable = true;

let currentPageNum = 1;
let currentPdfPath = null;
let currentPdfUrl = null;
let fieldMap = {};
let fieldsData = [];
let pageMetrics = {};
let pageDimensions = {};
let pdfPagePointWidth = 0;
let pdfPagePointHeight = 0;
let pdfPagePixelWidth = 0;
let pdfPagePixelHeight = 0;
let zoom = 1; // fixa em 1 (sem zoom dinâmico)
let renderState = {
  scale: 1,
  offsetX: 0,
  offsetY: 0,
  displayWidth: 0,
  displayHeight: 0,
};

let uploadStatus;
let applyStatus;
let zoomSlider;
let zoomValue;
let prevPageBtn;
let nextPageBtn;
let pageNumberInput;
let pdfContainer;
let fieldCountElement;

function loadElements() {
  uploadStatus = get('uploadStatus');
  applyStatus = get('applyStatus');
  prevPageBtn = get('btnPrevPage');
  nextPageBtn = get('btnNextPage');
  pageNumberInput = get('pageNumber');
  pdfContainer = get('pdfContainer');
  fieldCountElement = get('fieldCount');
}


const setStatus = (el, txt) => { el.textContent = txt; };

function attachListeners() {

  if (prevPageBtn) {
    prevPageBtn.addEventListener('click', () => {
      if (currentPageNum > 1) {
        currentPageNum -= 1;
        if (pageNumberInput) pageNumberInput.value = currentPageNum;
        renderPage(currentPageNum);
      }
    });
  }

  if (nextPageBtn) {
    nextPageBtn.addEventListener('click', () => {
      currentPageNum += 1;
      if (pageNumberInput) pageNumberInput.value = currentPageNum;
      renderPage(currentPageNum);
    });
  }

  if (pageNumberInput) {
    pageNumberInput.addEventListener('change', () => {
      const v = parseInt(pageNumberInput.value, 10) || 1;
      currentPageNum = v;
      renderPage(currentPageNum);
    });
  }

  const btnUpload = get('btnUpload');
  if (btnUpload) {
    btnUpload.addEventListener('click', async () => {
      const fileInput = get('fileInput');
      if (!fileInput || !fileInput.files.length) {
        setStatus(uploadStatus, 'Selecione um PDF primeiro.');
        return;
      }
      const file = fileInput.files[0];
      const formData = new FormData();
      formData.append('file', file);

      setStatus(uploadStatus, 'Enviando PDF...');
      const resp = await fetch('/api/upload', { method: 'POST', body: formData });
      if (!resp.ok) {
        const erro = await resp.json();
        setStatus(uploadStatus, `Upload falhou: ${erro.detail || resp.statusText}`);
        return;
      }
      const data = await resp.json();
      await openPdf(data.input_pdf, data.file_url);
    });
  }

  const btnRenderPage = get('btnRenderPage');
  if (btnRenderPage) {
    btnRenderPage.addEventListener('click', async () => {
      const pageNumber = parseInt(pageNumberInput?.value, 10) || 1;
      if (pageNumber < 1) return;
      currentPageNum = pageNumber;
      await renderPage(pageNumber);
    });
  }

  const btnApply = get('btnApplyOnMap');
  if (btnApply) {
    btnApply.addEventListener('click', async () => {
      if (!currentPdfPath) {
        setStatus(applyStatus, 'Carregue um PDF primeiro.');
        return;
      }

      const outName = `data/out/normalized-${Date.now()}.pdf`;
      const payload = {
        input_pdf: currentPdfPath,
        output_pdf: outName,
        map: fieldMap,
        fill: true,
        fill_template: '{new}',
        verify: true,
      };

      setStatus(applyStatus, 'Aplicando renomeações...');
      const resp = await fetch('/api/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        const erro = await resp.json();
        setStatus(applyStatus, `Aplicação falhou: ${JSON.stringify(erro)}`);
        return;
      }

      const data = await resp.json();
      setStatus(applyStatus, `PDF gerado: ${data.output_pdf}`);
      const downloadLink = get('downloadLink');
      if (downloadLink) {
        downloadLink.href = `/api/download?path=${encodeURIComponent(data.output_pdf)}`;
        downloadLink.style.display = 'inline-block';
        downloadLink.textContent = 'Baixar PDF Normalizado';
      }
    });
  }
}

window.addEventListener('DOMContentLoaded', () => {
  loadElements();
  attachListeners();
});

if (nextPageBtn) {
  nextPageBtn.addEventListener('click', () => {
    currentPageNum += 1;
    get('pageNumber').value = currentPageNum;
    renderPage(currentPageNum);
  });
}

async function renderPage(pageNum = 1) {
  if (!pdfRenderAvailable) {
    setStatus(uploadStatus, 'preview PDF desabilitado (modo sem pdfjs)');
    return;
  }
  if (!currentPdfPath) {
    return;
  }

  currentPageNum = pageNum;
  const previewImg = get('pdfPreview');
  const overlay = get('overlayCanvas');
  const container = get('pdfContainer');
  setStatus(uploadStatus, `Renderizando página ${pageNum}...`);

  try {
    const resp = await fetch(`/api/preview/page/${pageNum}?input_pdf=${encodeURIComponent(currentPdfPath)}`);
    if (!resp.ok) {
      throw new Error(`Falha preview: ${resp.status}`);
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);

    previewImg.onload = () => {
      pdfPagePixelWidth = previewImg.naturalWidth;
      pdfPagePixelHeight = previewImg.naturalHeight;

      const pageMetric = pageMetrics[currentPageNum] || {};
      pdfPagePointWidth = pageMetric.width || pdfPagePointWidth || 1;
      pdfPagePointHeight = pageMetric.height || pdfPagePointHeight || 1;

      const containerWidth = container.clientWidth;
      const containerHeight = container.clientHeight;
      const fitScale = Math.min(containerWidth / pdfPagePixelWidth, containerHeight / pdfPagePixelHeight, 1);
      const displayWidth = Math.round(pdfPagePixelWidth * fitScale);
      const displayHeight = Math.round(pdfPagePixelHeight * fitScale);
      const offsetX = Math.round((containerWidth - displayWidth) / 2);
      const offsetY = Math.round((containerHeight - displayHeight) / 2);
      const dpr = window.devicePixelRatio || 1;

      renderState = {
        scale: displayWidth / pdfPagePointWidth,
        offsetX,
        offsetY,
        displayWidth,
        displayHeight,
      };

      pdfContainer.style.width = '100%';
      pdfContainer.style.height = '100%';

      previewImg.style.position = 'absolute';
      previewImg.style.left = `${offsetX}px`;
      previewImg.style.top = `${offsetY}px`;
      previewImg.style.width = `${Math.round(displayWidth)}px`;
      previewImg.style.height = `${Math.round(displayHeight)}px`;
      previewImg.style.objectFit = 'contain';

      overlay.style.position = 'absolute';
      overlay.style.left = `${offsetX}px`;
      overlay.style.top = `${offsetY}px`;
      overlay.style.width = `${Math.round(displayWidth)}px`;
      overlay.style.height = `${Math.round(displayHeight)}px`;
      overlay.width = Math.round(displayWidth * dpr);
      overlay.height = Math.round(displayHeight * dpr);

      const ctx = overlay.getContext('2d');
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, displayWidth, displayHeight);

      setStatus(uploadStatus, `Preview da página ${pageNum} carregado (${Math.round(displayWidth)}x${Math.round(displayHeight)})`);

      clearOverlay();
      drawHighlight({ page: currentPageNum, x: 0, y: 0, width: 0, height: 0 });
    };

    previewImg.src = url;
    setStatus(uploadStatus, `Preview da página ${pageNum} carregado`);
  } catch (err) {
    setStatus(uploadStatus, `Erro no preview: ${err.message}`);
  }
}

function clearOverlay() {
  const ov = get('overlayCanvas');
  if (!ov) return;
  const ctx = ov.getContext('2d');
  ctx.clearRect(0, 0, ov.width, ov.height);
}

function drawHighlight(field) {
  if (!pdfRenderAvailable) return;
  if (!field) return;
  if (field.page !== currentPageNum) return;

  const overlay = get('overlayCanvas');
  if (!overlay || !pdfPagePointWidth || !pdfPagePointHeight) return;

  const dpr = window.devicePixelRatio || 1;
  const { scale, displayWidth, displayHeight } = renderState;
  if (!scale || !displayWidth || !displayHeight) return;

  const ctx = overlay.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, displayWidth, displayHeight);

  const x = field.x * scale;
  const y = (pdfPagePointHeight - field.y - field.height) * scale;
  const width = field.width * scale;
  const height = field.height * scale;

  ctx.strokeStyle = 'rgba(255, 0, 0, 0.9)';
  ctx.lineWidth = 2;
  ctx.fillStyle = 'rgba(255, 0, 0, 0.2)';
  ctx.strokeRect(x, y, width, height);
  ctx.fillRect(x, y, width, height);
}

function buildFieldRow(field) {
  const row = document.createElement('div');
  row.className = 'field-row';
  row.innerHTML = `
    <div class="field-title">Page ${field.page}: ${field.name || '(sem nome)'}</div>
    <div class="field-details">Type: ${field.type} x:${field.x.toFixed(1)} y:${field.y.toFixed(1)} w:${field.width.toFixed(1)} h:${field.height.toFixed(1)}</div>
    <label>Novo nome:</label>
    <input type="text" class="field-name-input" data-old="${field.name}" value="${fieldMap[field.name] || field.name}" />
  `;

  row.addEventListener('mouseenter', () => {
    drawHighlight(field);
  });
  row.addEventListener('mouseleave', () => {
    clearOverlay();
  });

  row.querySelector('.field-name-input').addEventListener('input', (event) => {
    const newName = event.target.value.trim();
    fieldMap[field.name] = newName;
  });

  return row;
}

async function loadFields(pdfPath) {
  const fieldsContainer = get('fieldsContainer');
  fieldsContainer.innerHTML = 'Carregando campos...';
  const resp = await fetch(`/api/fields?input_pdf=${encodeURIComponent(pdfPath)}`);
  if (!resp.ok) {
    const err = await resp.json();
    fieldsContainer.innerText = 'Erro: ' + (err.detail || resp.statusText);
    return;
  }

  const data = await resp.json();
  fieldsData = data.fields || [];
  fieldMap = {};
  fieldsContainer.innerHTML = '';
  pageDimensions = {};

  fieldsData.forEach((field) => {
    if (field.name) {
      fieldMap[field.name] = field.name;
    }

    const page = field.page || 1;
    if (field.page_width && field.page_height) {
      pageMetrics[page] = {
        width: field.page_width,
        height: field.page_height,
      };
    }

    const maxX = (pageDimensions[page]?.width || 0);
    const maxY = (pageDimensions[page]?.height || 0);
    pageDimensions[page] = {
      width: Math.max(maxX, field.x + field.width),
      height: Math.max(maxY, field.y + field.height),
    };

    const row = buildFieldRow(field);
    fieldsContainer.appendChild(row);
  });

  if (fieldCountElement) {
    fieldCountElement.textContent = `Campos: ${fieldsData.length}`;
  }
};

async function openPdf(pdfPath, pdfUrl) {
  currentPdfPath = pdfPath;
  currentPdfUrl = pdfUrl || pdfPath;
  setStatus(uploadStatus, 'Carregando PDF...');

  await loadFields(pdfPath);

  if (pdfRenderAvailable && pageNumberInput) {
    pageNumberInput.value = 1;
    await renderPage(1);
  }

  setStatus(uploadStatus, `PDF carregado: ${pdfPath}`);
  if (fieldCountElement) {
    fieldCountElement.textContent = `Campos: ${fieldsData.length}`;
  }
}



