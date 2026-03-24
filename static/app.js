const sentenceInput = document.getElementById('sentenceInput');
const parseBtn = document.getElementById('parseBtn');
const statusEl = document.getElementById('status');
const tokensEl = document.getElementById('tokens');
const normalizedEl = document.getElementById('normalized');
const originalEl = document.getElementById('originalDiagram');
const reducedEl = document.getElementById('reducedDiagram');
const originalImageEl = document.getElementById('originalDiagramImage');
const reducedImageEl = document.getElementById('reducedDiagramImage');
const imageModal = document.getElementById('imageModal');
const modalImage = document.getElementById('modalImage');
const closeModal = document.querySelector('.close-modal');

function setStatus(message, kind) {
  statusEl.textContent = message;
  statusEl.className = `status ${kind}`;
}

function setResult(data) {
  tokensEl.textContent = JSON.stringify(data.tokens);
  normalizedEl.textContent = data.normalized || '-';
  originalEl.textContent = data.original_diagram || '-';
  reducedEl.textContent = data.reduced_diagram || '-';

   if (data.original_diagram_image) {
    originalImageEl.src = data.original_diagram_image;
    originalImageEl.style.display = 'block';
  } else {
    originalImageEl.removeAttribute('src');
    originalImageEl.style.display = 'none';
  }

  if (data.reduced_diagram_image) {
    reducedImageEl.src = data.reduced_diagram_image;
    reducedImageEl.style.display = 'block';
  } else {
    reducedImageEl.removeAttribute('src');
    reducedImageEl.style.display = 'none';
  }
}

async function parseSentence() {
  const sentence = sentenceInput.value.trim();
  if (!sentence) {
    setStatus('Please enter a sentence.', 'error');
    return;
  }

  setStatus('Parsing...', 'neutral');

  try {
    const response = await fetch('/api/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sentence })
    });

    const data = await response.json();

    if (!response.ok || !data.ok) {
      setStatus(data.error || 'Parsing failed.', 'error');
      return;
    }

    setResult(data);
    setStatus('Parsed successfully.', 'ok');
  } catch (error) {
    setStatus(`Network error: ${error.message}`, 'error');
  }
}

function openImageModal(src) {
  modalImage.src = src;
  imageModal.classList.add('active');
}

function closeImageModalFn() {
  imageModal.classList.remove('active');
  modalImage.src = '';
}

function setupImageClickHandlers() {
  originalImageEl.addEventListener('click', () => {
    if (originalImageEl.src) {
      openImageModal(originalImageEl.src);
    }
  });

  reducedImageEl.addEventListener('click', () => {
    if (reducedImageEl.src) {
      openImageModal(reducedImageEl.src);
    }
  });
}

closeModal.addEventListener('click', closeImageModalFn);

imageModal.addEventListener('click', (event) => {
  if (event.target === imageModal) {
    closeImageModalFn();
  }
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && imageModal.classList.contains('active')) {
    closeImageModalFn();
  }
});

parseBtn.addEventListener('click', parseSentence);
sentenceInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    parseSentence();
  }
});

setupImageClickHandlers();
