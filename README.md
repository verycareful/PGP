# PGP Sentence Lab
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License: Polyform NC](https://img.shields.io/badge/License-Polyform%20NC%201.0.0-blue.svg)](https://polyformproject.org/licenses/noncommercial/1.0.0/)
[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)](.)
Version: 1903.26-alpha

PGP Sentence Lab is a pregroup-grammar sentence parser built with Python and Flask.
It accepts user input, parses supported sentence structures, and returns both textual and visual (PNG) diagrams for original and reduced forms.

## Features

- Interactive CLI parsing mode
- Web frontend for sentence input and parse results
- Support for:
  - adverbs
  - prepositional phrases
  - compound clauses with `and` and `or`
- Editable JSON lexicon (`lexicon.json`) for vocabulary updates without code changes
- Diagram rendering as text and image output

## Project Structure

- `sentence_generation.py`: main parser + CLI + Flask backend
- `lexicon.json`: configurable lexical categories and words
- `templates/index.html`: web page template
- `static/style.css`: frontend styles
- `static/app.js`: frontend interaction logic
- `requirements.txt`: Python dependencies

## Prerequisites

- Python 3.10+
- pip

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run (Web)

```bash
python sentence_generation.py --web
```

Open:

- `http://127.0.0.1:5000/`

## Run (CLI)

```bash
python sentence_generation.py
```

Type sentences in the prompt. Use `quit`, `exit`, or `q` to stop.

## Version Check

```bash
python sentence_generation.py --version
```

Expected:

- `sentence-lab 1903.26-alpha`

## API

### POST `/api/parse`

Request body:

```json
{
  "sentence": "the cat sat on the mat"
}
```

Success response (shape):

```json
{
  "ok": true,
  "sentence": "the cat sat on the mat",
  "tokens": ["the", "cat", "sat", "on", "the", "mat"],
  "normalized": "the cat sat on the mat",
  "original_diagram": "...",
  "reduced_diagram": "...",
  "original_diagram_image": "data:image/png;base64,...",
  "reduced_diagram_image": "data:image/png;base64,..."
}
```

Failure response (shape):

```json
{
  "ok": false,
  "error": "message"
}
```

## Lexicon Editing

Update `lexicon.json` categories:

- `det`
- `adj`
- `noun`
- `vintr`
- `vtr`
- `adv`
- `prep`
- `conj`

All words are normalized to lowercase when loaded.

## Notes

- This parser is intentionally constrained to supported grammar patterns.
- Unknown words fall back to nouns unless heuristic rules apply.
- Diagram generation requires plotting dependencies from `requirements.txt`.

## License

Copyright © 2026 Sricharan Suresh (github.com/verycareful)

This project is licensed under the **[Polyform Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/)**.
You may use, copy, and modify this software for non-commercial purposes only.
Commercial use of any kind is prohibited without explicit written permission from the author.

See the [LICENSE](LICENSE) file for the full license text, or visit
[https://polyformproject.org/licenses/noncommercial/1.0.0/](https://polyformproject.org/licenses/noncommercial/1.0.0/).

For commercial licensing inquiries, contact [sricharanc03@gmail.com](mailto:sricharanc03@gmail.com).

