"""
③ Code parser (Mode 1)

Owner: Adrien
Takes: list[Token] from lexer.tokenize_code
Gives: Program (AST of @dataclass nodes)

What it must do:
    Hand-written recursive descent, one function per grammar rule
    (grammar: docs/Medu_Team_Plan.pdf page 3).
    Wrong order -> raise MeduError('E201', 'expected X, found Y', line, col).
"""

from __future__ import annotations

from medu.tokens import Token


def parse(tokens: list[Token]):
    """Return the Program AST."""
    raise NotImplementedError
