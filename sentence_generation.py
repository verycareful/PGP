import argparse
import base64
import io
import json
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from discopy.grammar.pregroup import Ty, Word
from flask import Flask, jsonify, render_template, request


VERSION = "1903.26-alpha"


# =========================
# 1. DEFINE TYPES
# =========================
N = Ty("N")
S = Ty("S")


class ParseError(ValueError):
    """Raised when the current grammar cannot parse a sentence."""


@dataclass
class ParseResult:
    text: str
    tokens: List[str]
    normalized: str
    original_diagram: str
    reduced_diagram: str
    original_diagram_image: str | None
    reduced_diagram_image: str | None


class SentenceGenerator:
    """Interactive pregroup sentence parser with a dynamic lexicon."""

    def __init__(self, lexicon_path: str | None = None) -> None:
        self.lexicon: Dict[str, str] = {}
        self._seed_default_lexicon()
        self.lexicon_path = lexicon_path or os.path.join(
            os.path.dirname(__file__), "lexicon.json"
        )
        self.load_lexicon(self.lexicon_path)

    def _seed_default_lexicon(self) -> None:
        # Determiners
        for w in ("a", "an", "the", "this", "that", "these", "those", "my", "your"):
            self.lexicon[w] = "det"

        # Adjectives
        for w in ("smart", "happy", "good", "bad", "big", "small", "new", "old"):
            self.lexicon[w] = "adj"

        # Common nouns
        for w in (
            "alice",
            "bob",
            "students",
            "student",
            "teacher",
            "cat",
            "dog",
            "book",
            "city",
            "music",
            "pizza",
            "car",
            "child",
            "children",
        ):
            self.lexicon[w] = "noun"

        # Intransitive verbs
        for w in (
            "run",
            "runs",
            "sit",
            "sits",
            "sat",
            "sleep",
            "sleeps",
            "swim",
            "swims",
            "laugh",
            "laughs",
            "dance",
            "dances",
            "arrive",
            "arrives",
        ):
            self.lexicon[w] = "vintr"

        # Transitive verbs
        for w in (
            "love",
            "loves",
            "see",
            "sees",
            "like",
            "likes",
            "eat",
            "eats",
            "read",
            "reads",
            "watch",
            "watches",
            "build",
            "builds",
            "know",
            "knows",
        ):
            self.lexicon[w] = "vtr"

        # Adverbs
        for w in (
            "quickly",
            "slowly",
            "silently",
            "happily",
            "sadly",
            "carefully",
            "loudly",
        ):
            self.lexicon[w] = "adv"

        # Prepositions
        for w in ("in", "on", "at", "with", "by", "to", "from", "under", "over", "near"):
            self.lexicon[w] = "prep"

        # Conjunctions
        for w in ("and", "or"):
            self.lexicon[w] = "conj"

    def load_lexicon(self, path: str) -> None:
        if not os.path.exists(path):
            return

        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)

        if not isinstance(data, dict):
            raise ParseError("Lexicon JSON must be an object of category arrays.")

        allowed = {"det", "adj", "noun", "vintr", "vtr", "adv", "prep", "conj"}
        for category, words in data.items():
            if category not in allowed:
                raise ParseError(f"Unsupported lexicon category '{category}'.")
            if not isinstance(words, list):
                raise ParseError(f"Lexicon category '{category}' must be an array.")
            for w in words:
                if not isinstance(w, str):
                    raise ParseError(f"Lexicon value in '{category}' must be a string.")
                self.lexicon[w.lower()] = category

    @staticmethod
    def tokenize(text: str) -> List[str]:
        tokens = re.findall(r"[A-Za-z']+", text)
        return [t.lower() for t in tokens]

    def _guess_pos(self, token: str) -> str:
        if token in self.lexicon:
            return self.lexicon[token]

        # Heuristic fallback for unknown words.
        if token.endswith("ly"):
            self.lexicon[token] = "adv"
            return "adv"

        if token in {"and", "or"}:
            self.lexicon[token] = "conj"
            return "conj"

        if token in {"in", "on", "at", "with", "by", "to", "from", "under", "over", "near"}:
            self.lexicon[token] = "prep"
            return "prep"

        if token.endswith(("ing", "ed")):
            self.lexicon[token] = "vintr"
            return "vintr"

        # Default unknown words to nouns to keep interaction resilient.
        self.lexicon[token] = "noun"
        return "noun"

    def _word(self, token: str, pos: str) -> Word:
        if pos == "noun":
            return Word(token, N)
        if pos == "adj":
            return Word(token, N @ N.l)
        if pos == "det":
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
        raise ParseError(f"Unknown part-of-speech tag '{pos}' for token '{token}'.")

    @staticmethod
    def _compose(words: Sequence[Word]):
        if not words:
            raise ParseError("Cannot compose an empty phrase.")
        phrase = words[0]
        for w in words[1:]:
            phrase = phrase @ w
        return phrase

    def _parse_pp(self, tokens: List[str], start: int) -> Tuple[List[Word], int]:
        if start >= len(tokens):
            raise ParseError("Expected preposition but reached end of sentence.")

        prep = tokens[start]
        if self._guess_pos(prep) != "prep":
            raise ParseError(f"Expected preposition, got '{prep}'.")

        words = [self._word(prep, "prep")]
        np_phrase, i, np_words = self._parse_np(tokens, start + 1)
        _ = np_phrase
        words.extend(np_words)
        return words, i

    def _parse_np(self, tokens: List[str], start: int) -> Tuple[object, int, List[Word]]:
        i = start
        words = []

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

        phrase = self._compose(words)

        return phrase, i, words

    def _parse_clause(self, tokens: List[str], start: int) -> Tuple[object, int]:
        subj, i, words = self._parse_np(tokens, start)
        _ = subj

        # Allow pre-verb adverbs.
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

        # Allow post-verb adverbs.
        while i < len(tokens) and self._guess_pos(tokens[i]) == "adv":
            words.append(self._word(tokens[i], "adv"))
            i += 1

        if verb_pos == "vtr":
            obj, i, obj_words = self._parse_np(tokens, i)
            _ = obj
            words.extend(obj_words)

            # Allow adverbs after object as sentence modifiers.
            while i < len(tokens) and self._guess_pos(tokens[i]) == "adv":
                words.append(self._word(tokens[i], "adv"))
                i += 1

        # Sentence-level trailing prepositional phrases.
        while i < len(tokens) and self._guess_pos(tokens[i]) == "prep":
            pp_words, i = self._parse_pp(tokens, i)
            words.extend(pp_words)

        return self._compose(words), i

    def parse_sentence(self, text: str):
        tokens = self.tokenize(text)
        if not tokens:
            raise ParseError("Empty input. Type a sentence like 'the smart student reads a book'.")

        i = 0
        clause, i = self._parse_clause(tokens, i)
        diagram = clause

        while i < len(tokens):
            conj_token = tokens[i]
            if self._guess_pos(conj_token) != "conj":
                remainder = " ".join(tokens[i:])
                raise ParseError(f"Could not parse trailing tokens: '{remainder}'.")

            conj_word = self._word(conj_token, "conj")
            i += 1
            if i >= len(tokens):
                raise ParseError(f"Conjunction '{conj_token}' must be followed by another clause.")

            next_clause, i = self._parse_clause(tokens, i)
            diagram = diagram @ conj_word @ next_clause

        return diagram

    @staticmethod
    def build_result(text: str, tokens: List[str], sentence) -> ParseResult:
        reduced = sentence.normal_form()
        original_image = SentenceGenerator.diagram_to_data_url(sentence)
        reduced_image = SentenceGenerator.diagram_to_data_url(reduced)
        return ParseResult(
            text=text,
            tokens=tokens,
            normalized=" ".join(tokens),
            original_diagram=str(sentence),
            reduced_diagram=str(reduced),
            original_diagram_image=original_image,
            reduced_diagram_image=reduced_image,
        )

    @staticmethod
    def diagram_to_data_url(diagram) -> str | None:
        """Render a discopy diagram to a PNG data URL for web display."""
        try:
            diagram.draw(figsize=(10, 3), fontsize=11, show=False)
            fig = plt.gcf()
            buffer = io.BytesIO()
            fig.savefig(buffer, format="png", dpi=140, bbox_inches="tight")
            buffer.seek(0)
            encoded = base64.b64encode(buffer.read()).decode("ascii")
            return f"data:image/png;base64,{encoded}"
        except Exception:
            return None
        finally:
            plt.close("all")

    @staticmethod
    def draw_result(sentence) -> None:
        reduced = sentence.normal_form()

        # If diagram backend is unavailable, the parse result is still useful.
        try:
            reduced.draw(figsize=(8, 4), fontsize=12, show=False)
            plt.show()
        except Exception as exc:  # pragma: no cover - backend dependent
            print(f"Diagram draw skipped: {exc}")


app = Flask(__name__)
PARSER = SentenceGenerator()


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/parse")
def api_parse():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("sentence", "")).strip()
    if not text:
        return jsonify({"ok": False, "error": "Please enter a sentence."}), 400

    try:
        tokens = PARSER.tokenize(text)
        diagram = PARSER.parse_sentence(text)
        result = PARSER.build_result(text, tokens, diagram)
        return jsonify(
            {
                "ok": True,
                "sentence": result.text,
                "tokens": result.tokens,
                "normalized": result.normalized,
                "original_diagram": result.original_diagram,
                "reduced_diagram": result.reduced_diagram,
                "original_diagram_image": result.original_diagram_image,
                "reduced_diagram_image": result.reduced_diagram_image,
            }
        )
    except ParseError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": f"Unexpected error: {exc}"}), 500


def run_cli() -> None:
    parser = SentenceGenerator()
    print("Enter sentences to parse (type 'quit' to stop).")
    print("Supports adverbs, prepositional phrases, and compound clauses with and/or.")
    print("Example: 'the smart student quickly reads a book in city and bob runs'.")

    while True:
        raw = input("\nSentence> ").strip()
        if not raw:
            continue
        if raw.lower() in {"quit", "exit", "q"}:
            print("Goodbye.")
            break

        try:
            tokens = parser.tokenize(raw)
            diagram = parser.parse_sentence(raw)
            result = parser.build_result(raw, tokens, diagram)

            print(f"\n--- {result.text} ---")
            print("Tokens:", result.tokens)
            print("Normalized:", result.normalized)
            print("Original:", result.original_diagram)
            print("Reduced:", result.reduced_diagram)

            parser.draw_result(diagram)
        except ParseError as exc:
            print(f"Parse error: {exc}")
        except Exception as exc:
            print(f"Unexpected error: {exc}")


def main() -> None:
    cli = argparse.ArgumentParser(description="Sentence parser CLI and web app.")
    cli.add_argument("--web", action="store_true", help="Run web server instead of CLI.")
    cli.add_argument("--host", default="127.0.0.1", help="Web host.")
    cli.add_argument("--port", type=int, default=5000, help="Web port.")
    cli.add_argument("--version", action="version", version=f"sentence-lab {VERSION}")
    args = cli.parse_args()

    if args.web:
        app.run(host=args.host, port=args.port, debug=False)
        return

    run_cli()


if __name__ == "__main__":
    main()
