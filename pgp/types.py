"""Shared types for the pregroup grammar parser."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from discopy.grammar.pregroup import Ty

N: Ty = Ty("N")
S: Ty = Ty("S")

POS_LABELS: dict[str, str] = {
    "det":   "Determiner",
    "adj":   "Adjective",
    "noun":  "Noun",
    "vintr": "Intransitive Verb",
    "vtr":   "Transitive Verb",
    "adv":   "Adverb",
    "prep":  "Preposition",
    "conj":  "Conjunction",
}

ALLOWED_POS: frozenset[str] = frozenset(POS_LABELS)


class ParseError(ValueError):
    """Raised when the current grammar cannot parse a sentence."""


@dataclass(frozen=True)
class TokenTag:
    word: str
    pos: str
    guessed: bool = False

    @property
    def label(self) -> str:
        return POS_LABELS.get(self.pos, self.pos)

    def to_dict(self) -> dict:
        return {
            "word":    self.word,
            "pos":     self.pos,
            "label":   self.label,
            "guessed": self.guessed,
        }


@dataclass(frozen=True)
class ParseResult:
    text: str
    tokens: List[str]
    token_tags: List[TokenTag]
    normalized: str
    original_diagram: str
    reduced_diagram: str
    original_diagram_image: Optional[str]
    reduced_diagram_image: Optional[str]
