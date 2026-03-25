"""Core pregroup grammar parser."""
from __future__ import annotations

import base64
import io
import json
import logging
import os
import re
from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from discopy.grammar.pregroup import Word

from .types import ALLOWED_POS, N, S, ParseError, ParseResult, TokenTag

logger = logging.getLogger(__name__)

MAX_INPUT_LENGTH = 500

# Heuristic fallback prepositions (for words not in the lexicon)
_PREP_SET = frozenset(
    {"in", "on", "at", "with", "by", "to", "from", "under", "over", "near"}
)


class SentenceGenerator:
    """Pregroup grammar sentence parser backed by a JSON lexicon."""

    def __init__(self, lexicon_path: str | None = None) -> None:
        self.lexicon: Dict[str, str] = {}
        self.lexicon_path = lexicon_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "lexicon.json",
        )
        self.load_lexicon(self.lexicon_path)

    # ------------------------------------------------------------------
    # Lexicon management
    # ------------------------------------------------------------------

    def load_lexicon(self, path: str) -> None:
        if not os.path.exists(path):
            logger.warning("Lexicon file not found at %s; starting with empty lexicon.", path)
            return

        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)

        if not isinstance(data, dict):
            raise ParseError("Lexicon JSON must be an object mapping categories to word arrays.")

        for category, words in data.items():
            if category not in ALLOWED_POS:
                raise ParseError(f"Unsupported lexicon category '{category}'.")
            if not isinstance(words, list):
                raise ParseError(f"Lexicon category '{category}' must be an array.")
            for w in words:
                if not isinstance(w, str):
                    raise ParseError(f"Every entry in '{category}' must be a string.")
                self.lexicon[w.lower()] = category

        logger.debug("Loaded %d lexicon entries from %s.", len(self.lexicon), path)

    # ------------------------------------------------------------------
    # Tokenisation
    # ------------------------------------------------------------------

    @staticmethod
    def tokenize(text: str) -> List[str]:
        tokens = re.findall(r"[A-Za-z']+", text)
        return [t.lower() for t in tokens]

    # ------------------------------------------------------------------
    # Part-of-speech lookup (non-mutating)
    # ------------------------------------------------------------------

    def _lookup_pos(self, token: str) -> Tuple[str, bool]:
        """Return (pos, is_guessed).  Never mutates self.lexicon."""
        if token in self.lexicon:
            return self.lexicon[token], False

        # Heuristic fallbacks — ordered most-specific first.
        if token in {"and", "or"}:
            return "conj", True
        if token in _PREP_SET:
            return "prep", True
        if token.endswith("ly"):
            return "adv", True
        if token.endswith(("ing", "ed")):
            return "vintr", True

        return "noun", True  # last-resort default

    def _guess_pos(self, token: str) -> str:
        pos, _ = self._lookup_pos(token)
        return pos

    # ------------------------------------------------------------------
    # Word → discopy type mapping
    # ------------------------------------------------------------------

    def _word(self, token: str, pos: str) -> Word:
        if pos == "noun":
            return Word(token, N)
        if pos in {"adj", "det"}:
            return Word(token, N @ N.l)
        if pos == "vintr":
            return Word(token, N.r @ S)
        if pos == "vtr":
            return Word(token, N.r @ S @ N.l)
        if pos == "adv":
            return Word(token, S.r @ S)
        if pos == "prep":
            return Word(token, S.r @ S @ N.l)
        if pos == "conj":
            return Word(token, S.r @ S @ S.l)
        raise ParseError(f"Unknown POS tag '{pos}' for token '{token}'.")

    # ------------------------------------------------------------------
    # Phrase composition
    # ------------------------------------------------------------------

    @staticmethod
    def _compose(words: Sequence[Word]):
        if not words:
            raise ParseError("Cannot compose an empty phrase.")
        phrase = words[0]
        for w in words[1:]:
            phrase = phrase @ w
        return phrase

    # ------------------------------------------------------------------
    # Recursive-descent grammar rules
    # ------------------------------------------------------------------

    def _parse_pp(self, tokens: List[str], start: int) -> Tuple[List[Word], int]:
        """Parse a prepositional phrase starting at *start*."""
        if start >= len(tokens):
            raise ParseError("Expected preposition but reached end of sentence.")
        prep = tokens[start]
        if self._guess_pos(prep) != "prep":
            raise ParseError(f"Expected preposition, got '{prep}'.")
        words = [self._word(prep, "prep")]
        i, np_words = self._parse_np(tokens, start + 1)
        words.extend(np_words)
        return words, i

    def _parse_np(self, tokens: List[str], start: int) -> Tuple[int, List[Word]]:
        """Parse a noun phrase; returns (end_index, word_list)."""
        i = start
        words: List[Word] = []

        if i < len(tokens) and self._guess_pos(tokens[i]) == "det":
            words.append(self._word(tokens[i], "det"))
            i += 1

        while i < len(tokens) and self._guess_pos(tokens[i]) == "adj":
            words.append(self._word(tokens[i], "adj"))
            i += 1

        if i >= len(tokens):
            raise ParseError("Expected a noun but reached end of sentence.")

        noun_pos = self._guess_pos(tokens[i])
        if noun_pos != "noun":
            raise ParseError(f"Expected a noun in noun phrase, got '{tokens[i]}'.")

        words.append(self._word(tokens[i], "noun"))
        i += 1

        # Optional noun-attached prepositional phrases.
        while i < len(tokens) and self._guess_pos(tokens[i]) == "prep":
            pp_words, i = self._parse_pp(tokens, i)
            words.extend(pp_words)

        return i, words

    def _parse_clause(self, tokens: List[str], start: int) -> Tuple[object, int]:
        """Parse a single clause (subject + verb [+ object] [+ adverbs/PPs])."""
        i, words = self._parse_np(tokens, start)

        # Pre-verb adverbs.
        while i < len(tokens) and self._guess_pos(tokens[i]) == "adv":
            words.append(self._word(tokens[i], "adv"))
            i += 1

        if i >= len(tokens):
            raise ParseError("Missing verb after subject noun phrase.")

        verb_token = tokens[i]
        verb_pos = self._guess_pos(verb_token)
        if verb_pos not in {"vintr", "vtr"}:
            raise ParseError(f"Expected a verb after subject, got '{verb_token}'.")

        words.append(self._word(verb_token, verb_pos))
        i += 1

        # Post-verb adverbs.
        while i < len(tokens) and self._guess_pos(tokens[i]) == "adv":
            words.append(self._word(tokens[i], "adv"))
            i += 1

        if verb_pos == "vtr":
            i, obj_words = self._parse_np(tokens, i)
            words.extend(obj_words)

            # Adverbs after object.
            while i < len(tokens) and self._guess_pos(tokens[i]) == "adv":
                words.append(self._word(tokens[i], "adv"))
                i += 1

        # Sentence-level trailing prepositional phrases.
        while i < len(tokens) and self._guess_pos(tokens[i]) == "prep":
            pp_words, i = self._parse_pp(tokens, i)
            words.extend(pp_words)

        return self._compose(words), i

    # ------------------------------------------------------------------
    # Public parse entry point
    # ------------------------------------------------------------------

    def parse_sentence(self, text: str):
        """Parse *text* and return a discopy diagram, or raise ParseError."""
        if len(text) > MAX_INPUT_LENGTH:
            raise ParseError(
                f"Input too long ({len(text)} chars). Maximum is {MAX_INPUT_LENGTH}."
            )

        tokens = self.tokenize(text)
        if not tokens:
            raise ParseError(
                "Empty input. Try something like: 'the smart student reads a book'."
            )

        clause, i = self._parse_clause(tokens, 0)
        diagram = clause

        while i < len(tokens):
            conj_token = tokens[i]
            if self._guess_pos(conj_token) != "conj":
                remainder = " ".join(tokens[i:])
                raise ParseError(f"Could not parse trailing tokens: '{remainder}'.")

            conj_word = self._word(conj_token, "conj")
            i += 1
            if i >= len(tokens):
                raise ParseError(
                    f"Conjunction '{conj_token}' must be followed by another clause."
                )

            next_clause, i = self._parse_clause(tokens, i)
            diagram = diagram @ conj_word @ next_clause

        return diagram

    # ------------------------------------------------------------------
    # Result building
    # ------------------------------------------------------------------

    def _tag_tokens(self, tokens: List[str]) -> List[TokenTag]:
        return [
            TokenTag(word=t, pos=pos, guessed=guessed)
            for t in tokens
            for pos, guessed in [self._lookup_pos(t)]
        ]

    def build_result(self, text: str, diagram) -> ParseResult:
        tokens = self.tokenize(text)
        token_tags = self._tag_tokens(tokens)
        reduced = diagram.normal_form()
        return ParseResult(
            text=text,
            tokens=tokens,
            token_tags=token_tags,
            normalized=" ".join(tokens),
            original_diagram=str(diagram),
            reduced_diagram=str(reduced),
            original_diagram_image=self._diagram_to_data_url(diagram),
            reduced_diagram_image=self._diagram_to_data_url(reduced),
        )

    # ------------------------------------------------------------------
    # Diagram rendering
    # ------------------------------------------------------------------

    @staticmethod
    def _diagram_to_data_url(diagram) -> Optional[str]:
        """Render a discopy diagram to a PNG data-URL, or return None on failure."""
        try:
            diagram.draw(figsize=(10, 3), fontsize=11, show=False)
            fig = plt.gcf()
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
            buf.seek(0)
            encoded = base64.b64encode(buf.read()).decode("ascii")
            return f"data:image/png;base64,{encoded}"
        except Exception:
            logger.exception("Failed to render diagram to PNG.")
            return None
        finally:
            plt.close("all")

    @staticmethod
    def draw_result(diagram) -> None:
        """CLI helper: display the reduced diagram via matplotlib."""
        reduced = diagram.normal_form()
        try:
            reduced.draw(figsize=(8, 4), fontsize=12, show=False)
            plt.show()
        except Exception as exc:
            logger.warning("Diagram draw skipped: %s", exc)
