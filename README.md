# PGP Sentence Lab
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License: Polyform NC](https://img.shields.io/badge/License-Polyform%20NC%201.0.0-blue.svg)](https://polyformproject.org/licenses/noncommercial/1.0.0/)
[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)](.)

Version: 2503.26-alpha

PGP Sentence Lab is a pregroup-grammar sentence parser built with Python and Flask.
It accepts English sentences, parses their syntactic structure using formal pregroup grammar rules, and returns both textual and visual (PNG) string diagrams for the original and reduced (normal form) representations.

## Features

- Interactive CLI parsing mode
- Web frontend with real-time parse results
- Color-coded token visualization with part-of-speech labels
- Parse history with one-click restore (last 8 parses)
- Support for:
  - determiners and adjectives
  - adverbs (pre-verb, post-verb, post-object)
  - prepositional phrases (noun-attached and sentence-level)
  - compound clauses with `and` and `or`
- Editable JSON lexicon (`lexicon.json`) — no code changes needed to add vocabulary
- Diagram rendering as text notation and PNG images
- Click-to-expand modal for diagram visualization
- Security headers and a `/api/health` endpoint

## Project Structure

```
├── sentence_generation.py   entry point (CLI + web server)
├── pgp/
│   ├── __init__.py
│   ├── types.py             ParseError, TokenTag, ParseResult, grammar types
│   ├── parser.py            SentenceGenerator — core parser logic
│   ├── web.py               Flask app factory and API routes
│   └── cli.py               interactive CLI runner
├── lexicon.json             lexical categories and vocabulary
├── templates/index.html     web UI template
├── static/style.css         styles
├── static/app.js            frontend logic
└── requirements.txt         Python dependencies
```

## Prerequisites

- Python 3.10+
- pip

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

## Run (Web)

```bash
python sentence_generation.py --web
```

Open `http://127.0.0.1:5000/` in your browser.

Optional flags:

```bash
python sentence_generation.py --web --host 0.0.0.0 --port 8080
```

## Run (CLI)

```bash
python sentence_generation.py
```

Type sentences at the `Sentence>` prompt. Use `quit`, `exit`, or `q` to stop, or press `Ctrl-C`.

## Version Check

```bash
python sentence_generation.py --version
# sentence-lab 2503.26-alpha
```

## API

### `GET /api/health`

```json
{ "status": "ok", "lexicon_size": 152 }
```

### `POST /api/parse`

Request:

```json
{ "sentence": "the cat sits on the mat" }
```

Success response:

```json
{
  "ok": true,
  "sentence": "the cat sits on the mat",
  "tokens": ["the", "cat", "sits", "on", "the", "mat"],
  "token_tags": [
    { "word": "the",  "pos": "det",   "label": "Determiner",        "guessed": false },
    { "word": "cat",  "pos": "noun",  "label": "Noun",               "guessed": false },
    { "word": "sits", "pos": "vintr", "label": "Intransitive Verb",  "guessed": false },
    { "word": "on",   "pos": "prep",  "label": "Preposition",        "guessed": false },
    { "word": "the",  "pos": "det",   "label": "Determiner",         "guessed": false },
    { "word": "mat",  "pos": "noun",  "label": "Noun",               "guessed": false }
  ],
  "normalized": "the cat sits on the mat",
  "original_diagram": "...",
  "reduced_diagram": "...",
  "original_diagram_image": "data:image/png;base64,...",
  "reduced_diagram_image":  "data:image/png;base64,..."
}
```

Error response (HTTP 400 / 500):

```json
{ "ok": false, "error": "Missing verb after subject noun phrase." }
```

`token_tags[].guessed: true` means the part-of-speech was inferred heuristically (not found in the lexicon) and may be incorrect.

## Lexicon

Edit `lexicon.json` to add or change vocabulary. Supported categories:

| Key     | Part of speech      | Example words             |
|---------|---------------------|---------------------------|
| `det`   | Determiner          | the, a, my, this          |
| `adj`   | Adjective           | smart, big, beautiful      |
| `noun`  | Noun                | alice, book, city         |
| `vintr` | Intransitive verb   | runs, sits, laughs        |
| `vtr`   | Transitive verb     | reads, loves, builds      |
| `adv`   | Adverb              | quickly, carefully        |
| `prep`  | Preposition         | in, on, with, near        |
| `conj`  | Conjunction         | and, or                   |

All words are normalized to lowercase on load. Unknown words fall back to heuristic POS inference (indicated by `guessed: true` in the API and a `?` badge in the UI).

## License

Copyright © 2026 Sricharan Suresh (github.com/verycareful)

This project is licensed under the **[Polyform Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/)**.
You may use, copy, and modify this software for non-commercial purposes only.
Commercial use of any kind is prohibited without explicit written permission from the author.

See the [LICENSE](LICENSE) file for the full license text, or visit
[https://polyformproject.org/licenses/noncommercial/1.0.0/](https://polyformproject.org/licenses/noncommercial/1.0.0/).

For commercial licensing inquiries, contact [sricharanc03@gmail.com](mailto:sricharanc03@gmail.com).
