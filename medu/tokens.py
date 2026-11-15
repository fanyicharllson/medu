"""
Tokens: the labelled pieces the word cutter (lexer) produces.

Owner: Charllson (shared contract - ask before changing).
Used by: lexer.py (creates them), both parsers (read them).

A token is one piece of the source text with a label:
    Token(kind="NAME", text="lɛn", value=None, line=1, col=1)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ---- Token kinds -----------------------------------------------------------
# Mode 1 (programs)
KEYWORD = "KEYWORD"    # value = concept, e.g. "PRINT" (never a Medumba word)
NAME = "NAME"          # a variable name chosen by the user
STRING = "STRING"      # text in quotes; value = the text without quotes
NUMBER = "NUMBER"      # value = int or float
OP = "OP"              # = + - * /
LPAREN = "LPAREN"      # (
RPAREN = "RPAREN"      # )
NEWLINE = "NEWLINE"    # end of a line

# Mode 2 (sentences)
WORD = "WORD"          # value = list of possible dictionary entries
PUNCT = "PUNCT"        # . ? ! ,

# Both
EOF = "EOF"            # end of the file

KINDS = {KEYWORD, NAME, STRING, NUMBER, OP, LPAREN, RPAREN, NEWLINE,
         WORD, PUNCT, EOF}


@dataclass
class Token:
    kind: str          # one of KINDS
    text: str          # exactly what the user wrote (after cleaning)
    value: Any = None  # see the comments on each kind above
    line: int = 1      # 1-based
    col: int = 1       # 1-based

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"unknown token kind: {self.kind}")

    def __repr__(self) -> str:
        extra = f" {self.value!r}" if self.value is not None else ""
        return f"[{self.kind} {self.text!r}{extra} {self.line}:{self.col}]"
