/* PGP Sentence Lab — client-side logic */

'use strict';

// ----------------------------------------------------------------
// State
// ----------------------------------------------------------------
const state = {
  history: [],
  loading: false,
};

const MAX_HISTORY = 8;

// ----------------------------------------------------------------
// DOM references
// ----------------------------------------------------------------
const $input          = document.getElementById('sentenceInput');
const $parseBtn       = document.getElementById('parseBtn');
const $status         = document.getElementById('status');
const $tokenSection   = document.getElementById('tokenSection');
const $tokenChips     = document.getElementById('tokenChips');
const $guessedNote    = document.getElementById('guessedNote');
const $diagramSection = document.getElementById('diagramSection');
const $emptyState     = document.getElementById('emptyState');
const $originalDiag   = document.getElementById('originalDiagram');
const $reducedDiag    = document.getElementById('reducedDiagram');
const $originalImg    = document.getElementById('originalDiagramImage');
const $reducedImg     = document.getElementById('reducedDiagramImage');
const $originalBox    = document.getElementById('originalBox');
const $reducedBox     = document.getElementById('reducedBox');
const $historySection = document.getElementById('historySection');
const $historyList    = document.getElementById('historyList');
const $clearHistory   = document.getElementById('clearHistory');
const $modal          = document.getElementById('imageModal');
const $modalImg       = document.getElementById('modalImage');
const $modalClose     = document.getElementById('modalClose');
const $modalBackdrop  = document.getElementById('modalBackdrop');

// ----------------------------------------------------------------
// POS label metadata
// ----------------------------------------------------------------
const POS_META = {
  det:   { short: 'Det',   long: 'Determiner' },
  noun:  { short: 'Noun',  long: 'Noun' },
  adj:   { short: 'Adj',   long: 'Adjective' },
  vtr:   { short: 'V·tr',  long: 'Transitive Verb' },
  vintr: { short: 'V·itr', long: 'Intransitive Verb' },
  adv:   { short: 'Adv',   long: 'Adverb' },
  prep:  { short: 'Prep',  long: 'Preposition' },
  conj:  { short: 'Conj',  long: 'Conjunction' },
};

// ----------------------------------------------------------------
// Status
// ----------------------------------------------------------------
function setStatus(msg, kind) {
  $status.textContent = msg;
  $status.className = `status status--${kind}`;
}

// ----------------------------------------------------------------
// Loading state
// ----------------------------------------------------------------
function setLoading(on) {
  state.loading = on;
  $parseBtn.disabled = on;
  $parseBtn.classList.toggle('loading', on);
}

// ----------------------------------------------------------------
// Token chips
// ----------------------------------------------------------------
function renderTokenChips(tokenTags) {
  $tokenChips.innerHTML = '';
  let hasGuessed = false;

  for (const tag of tokenTags) {
    if (tag.guessed) hasGuessed = true;

    const meta = POS_META[tag.pos] ?? { short: tag.pos, long: tag.pos };
    const title = `${meta.long}${tag.guessed ? ' (inferred)' : ''}`;

    const chip = document.createElement('span');
    chip.className = `token-chip pos-${tag.pos}`;
    chip.title = title;
    chip.setAttribute('aria-label', `${tag.word}: ${title}`);

    const wordEl = document.createElement('span');
    wordEl.className = 'token-word';
    wordEl.textContent = tag.word;

    const posEl = document.createElement('span');
    posEl.className = 'token-pos';
    posEl.textContent = meta.short;

    chip.appendChild(wordEl);
    chip.appendChild(posEl);

    if (tag.guessed) {
      const guessEl = document.createElement('span');
      guessEl.className = 'token-guess';
      guessEl.textContent = '?';
      chip.appendChild(guessEl);
    }

    $tokenChips.appendChild(chip);
  }

  $guessedNote.hidden = !hasGuessed;
  $tokenSection.hidden = false;
}

// ----------------------------------------------------------------
// Diagram image helpers
// ----------------------------------------------------------------
function showDiagramImage(imgEl, boxEl, src) {
  const placeholder = boxEl.querySelector('.diagram-placeholder');
  if (src) {
    imgEl.src = src;
    imgEl.classList.add('visible');
    if (placeholder) placeholder.hidden = true;
  } else {
    imgEl.removeAttribute('src');
    imgEl.classList.remove('visible');
    if (placeholder) placeholder.hidden = false;
  }
}

// ----------------------------------------------------------------
// Render a full parse result into the UI
// ----------------------------------------------------------------
function renderResult(data) {
  renderTokenChips(data.token_tags ?? []);

  $originalDiag.textContent = data.original_diagram || '-';
  $reducedDiag.textContent  = data.reduced_diagram  || '-';

  showDiagramImage($originalImg, $originalBox, data.original_diagram_image);
  showDiagramImage($reducedImg,  $reducedBox,  data.reduced_diagram_image);

  $diagramSection.hidden = false;
  $emptyState.hidden     = true;
}

// ----------------------------------------------------------------
// History
// ----------------------------------------------------------------
function addToHistory(data) {
  // Deduplicate consecutive identical sentences.
  if (state.history.length > 0 && state.history[0].sentence === data.sentence) return;

  state.history.unshift({
    sentence:               data.sentence,
    tokens:                 data.tokens,
    token_tags:             data.token_tags,
    original_diagram:       data.original_diagram,
    reduced_diagram:        data.reduced_diagram,
    original_diagram_image: data.original_diagram_image,
    reduced_diagram_image:  data.reduced_diagram_image,
    time:                   new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  });

  if (state.history.length > MAX_HISTORY) state.history.pop();

  renderHistory();
}

function renderHistory() {
  if (state.history.length === 0) {
    $historySection.hidden = true;
    return;
  }

  $historySection.hidden = false;
  $historyList.innerHTML = '';

  for (const [i, item] of state.history.entries()) {
    const li = document.createElement('li');

    const btn = document.createElement('button');
    btn.className = 'history-btn';
    btn.dataset.index = i;
    btn.setAttribute('aria-label', `Restore: ${item.sentence}`);

    const sentEl = document.createElement('span');
    sentEl.className = 'history-sentence';
    sentEl.textContent = item.sentence;

    const metaEl = document.createElement('span');
    metaEl.className = 'history-meta';
    metaEl.textContent = `${item.tokens.length} tok · ${item.time}`;

    btn.appendChild(sentEl);
    btn.appendChild(metaEl);
    li.appendChild(btn);
    $historyList.appendChild(li);
  }
}

function restoreFromHistory(index) {
  const item = state.history[index];
  if (!item) return;
  $input.value = item.sentence;
  renderResult(item);
  setStatus(`Restored: "${item.sentence}"`, 'ok');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ----------------------------------------------------------------
// Parse
// ----------------------------------------------------------------
async function parseSentence() {
  const sentence = $input.value.trim();
  if (!sentence) {
    setStatus('Please enter a sentence.', 'error');
    $input.focus();
    return;
  }

  setLoading(true);
  setStatus('Parsing\u2026', 'neutral');

  try {
    const res  = await fetch('/api/parse', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ sentence }),
    });

    const data = await res.json();

    if (!res.ok || !data.ok) {
      setStatus(data.error || 'Parsing failed.', 'error');
      return;
    }

    renderResult(data);
    addToHistory(data);
    setStatus('Parsed successfully.', 'ok');
  } catch (err) {
    setStatus(`Network error: ${err.message}`, 'error');
  } finally {
    setLoading(false);
  }
}

// ----------------------------------------------------------------
// Copy buttons
// ----------------------------------------------------------------
document.querySelectorAll('.copy-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const target = document.getElementById(btn.dataset.target);
    const text = target?.textContent?.trim();
    if (!text || text === '-') return;

    try {
      await navigator.clipboard.writeText(text);
      btn.classList.add('copied');
      setTimeout(() => btn.classList.remove('copied'), 1600);
    } catch {
      /* clipboard unavailable — fail silently */
    }
  });
});

// ----------------------------------------------------------------
// History events
// ----------------------------------------------------------------
$historyList.addEventListener('click', e => {
  const btn = e.target.closest('.history-btn');
  if (btn) restoreFromHistory(Number(btn.dataset.index));
});

$clearHistory.addEventListener('click', () => {
  state.history = [];
  renderHistory();
});

// ----------------------------------------------------------------
// Image modal
// ----------------------------------------------------------------
function openModal(src) {
  $modalImg.src = src;
  $modal.classList.add('active');
  document.body.style.overflow = 'hidden';
  $modalClose.focus();
}

function closeModal() {
  $modal.classList.remove('active');
  $modalImg.src = '';
  document.body.style.overflow = '';
}

[$originalImg, $reducedImg].forEach(img => {
  img.addEventListener('click', () => {
    if (img.classList.contains('visible')) openModal(img.src);
  });
});

$modalClose.addEventListener('click', closeModal);
$modalBackdrop.addEventListener('click', closeModal);

document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && $modal.classList.contains('active')) closeModal();
});

// ----------------------------------------------------------------
// Parse triggers
// ----------------------------------------------------------------
$parseBtn.addEventListener('click', parseSentence);

$input.addEventListener('keydown', e => {
  if (e.key === 'Enter') parseSentence();
});
