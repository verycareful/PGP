# Changelog

## 2503.26-alpha - 2026-03-25

- Refactored monolithic `sentence_generation.py` into a `pgp/` package (`types`, `parser`, `web`, `cli`).
- Removed hardcoded default lexicon seeds — `lexicon.json` is now the sole source of vocabulary.
- Fixed POS-guessing mutation bug: `_guess_pos` no longer permanently writes inferred tags into the lexicon, preventing state pollution across requests.
- Fixed unused return values in recursive-descent parse methods (`_parse_np` return signature simplified).
- Added `token_tags` field to `/api/parse` response — each token carries its word, POS, human-readable label, and a `guessed` flag.
- Added `/api/health` endpoint returning server status and lexicon size.
- Added input length validation (max 500 characters).
- Security headers added to all responses: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`.
- Internal server errors no longer leak exception details to API clients; full traces go to the server log.
- Added structured logging via Python's `logging` module throughout the `pgp/` package.
- Flask app now uses an app-factory pattern (`create_app()`), decoupling it from module-level state.
- Expanded `lexicon.json` from ~50 to ~150 entries across all POS categories.
- Pinned all dependency version constraints in `requirements.txt`.
- UI: token chips with per-POS color coding and part-of-speech labels.
- UI: parse history panel — last 8 parses with one-click restore.
- UI: loading spinner on the Parse button during in-flight requests.
- UI: copy-to-clipboard buttons on diagram text blocks.
- UI: placeholder graphics in diagram boxes before first parse.
- UI: heuristically guessed tokens marked with a `?` badge and explanatory note.

## 2403.26-alpha - 2026-03-24

- Added click-to-expand modal for diagram images with smooth animations.
- Added image hover effects and keyboard navigation (Escape to close).
- Added mobile-friendly fullscreen diagram viewing.

## 1903.26-alpha - 2026-03-19

- Added support for adverbs in clauses.
- Added support for prepositional phrases in noun and sentence contexts.
- Added support for compound clauses joined by `and` and `or`.
- Added external JSON lexicon loading from `lexicon.json`.
- Added Flask frontend and parse API endpoint.
- Added server-side PNG rendering for original and reduced diagrams.
- Added project documentation and versioned release notes.
