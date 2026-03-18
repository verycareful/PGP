const sentenceInput = document.getElementById('sentenceInput');
const parseBtn = document.getElementById('parseBtn');
const statusEl = document.getElementById('status');
const tokensEl = document.getElementById('tokens');
const normalizedEl = document.getElementById('normalized');
const originalEl = document.getElementById('originalDiagram');
const reducedEl = document.getElementById('reducedDiagram');
const originalImageEl = document.getElementById('originalDiagramImage');
const reducedImageEl = document.getElementById('reducedDiagramImage');

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

parseBtn.addEventListener('click', parseSentence);
sentenceInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    parseSentence();
  }
});
