"""Interactive CLI for PGP Sentence Lab."""
from __future__ import annotations

import logging

from .parser import SentenceGenerator
from .types import ParseError

logger = logging.getLogger(__name__)


def run_cli(parser: SentenceGenerator | None = None) -> None:
    p = parser or SentenceGenerator()
    print("PGP Sentence Lab — Interactive Parser")
    print("Supports adverbs, prepositional phrases, and compound clauses with and/or.")
    print("Example: 'the smart student quickly reads a book in the city and bob runs'")
    print("Type 'quit' or press Ctrl-C to exit.\n")

    while True:
        try:
            raw = input("Sentence> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not raw:
            continue
        if raw.lower() in {"quit", "exit", "q"}:
            print("Goodbye.")
            break

        try:
            diagram = p.parse_sentence(raw)
            result = p.build_result(raw, diagram)

            print(f"\n--- {result.text} ---")
            tags = [(t.word, t.pos + ("?" if t.guessed else "")) for t in result.token_tags]
            print("Tokens :", tags)
            print("Original:", result.original_diagram)
            print("Reduced :", result.reduced_diagram)

            p.draw_result(diagram)
        except ParseError as exc:
            print(f"Parse error: {exc}")
        except Exception as exc:
            logger.debug("CLI error", exc_info=True)
            print(f"Error: {exc}")
