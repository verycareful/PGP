"""Flask application factory for PGP Sentence Lab."""
from __future__ import annotations

import logging
import os

from flask import Flask, jsonify, render_template, request

from .parser import SentenceGenerator
from .types import ParseError

logger = logging.getLogger(__name__)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(parser: SentenceGenerator | None = None) -> Flask:
    """Create and configure the Flask app.

    Pass a pre-built *parser* for testing or custom lexicon paths.
    """
    app = Flask(
        __name__,
        template_folder=os.path.join(_ROOT, "templates"),
        static_folder=os.path.join(_ROOT, "static"),
    )

    _parser = parser or SentenceGenerator()

    # ------------------------------------------------------------------
    # Security headers on every response
    # ------------------------------------------------------------------

    @app.after_request
    def _security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "lexicon_size": len(_parser.lexicon)})

    @app.post("/api/parse")
    def api_parse():
        payload = request.get_json(silent=True) or {}
        text = str(payload.get("sentence", "")).strip()

        if not text:
            return jsonify({"ok": False, "error": "Please enter a sentence."}), 400

        try:
            diagram = _parser.parse_sentence(text)
            result = _parser.build_result(text, diagram)
            return jsonify(
                {
                    "ok": True,
                    "sentence": result.text,
                    "tokens": result.tokens,
                    "token_tags": [t.to_dict() for t in result.token_tags],
                    "normalized": result.normalized,
                    "original_diagram": result.original_diagram,
                    "reduced_diagram": result.reduced_diagram,
                    "original_diagram_image": result.original_diagram_image,
                    "reduced_diagram_image": result.reduced_diagram_image,
                }
            )
        except ParseError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        except Exception:
            logger.exception("Unexpected error parsing: %.60r", text)
            return jsonify({"ok": False, "error": "An internal error occurred."}), 500

    return app
