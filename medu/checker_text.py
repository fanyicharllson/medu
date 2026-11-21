"""
④ Sense check (Mode 2)

Owner: Charllson
Takes: Sentence trees from parser_text.parse
Gives: Nothing; raises MeduError when a sentence is well formed but makes no sense

Rules (one function each):
    E311  the same grammar word twice in one clause   (mə kə̀ kə̀ jʉ)
    E312  past and future in the same clause          (mə àʼ fə̀ jʉ)
"""

from __future__ import annotations

from medu.errors import MeduError
from medu.parser_text import Clause, Sentence


def _no_repeated_marker(clause: Clause) -> None:
    seen: dict[str, str] = {}
    for role, tok in clause.markers:
        if role in seen:
            raise MeduError("E311", f"'{tok.text}' ({role}) appears twice in one sentence",
                            tok.line, tok.col, hint=f"remove one '{tok.text}'")
        seen[role] = tok.text


def _one_time(clause: Clause) -> None:
    roles = {role: tok for role, tok in clause.markers}
    if "past" in roles and "future" in roles:
        tok = roles["future"]
        raise MeduError("E312", "a sentence cannot be in the past and the future at once",
                        tok.line, tok.col,
                        hint=f"keep either '{roles['past'].text}' (past) or "
                             f"'{tok.text}' (future)")


def check(sentences: list[Sentence]) -> None:
    for sentence in sentences:
        for clause in sentence.clauses:
            _no_repeated_marker(clause)
            _one_time(clause)
