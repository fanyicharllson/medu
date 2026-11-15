"""
③ Grammar check (Mode 2)

Owner: Charllson
Takes: list[Token] from lexer.tokenize_text
Gives: list of sentence trees

What it must do:
    Sentence -> Subject [Tense] [Negation] Verb [Object], more patterns
    added with a speaker. Picks the right candidate for words with
    several meanings. Wrong order -> MeduError('E2xx').
"""

from __future__ import annotations

from medu.tokens import Token


def parse(tokens: list[Token]):
    raise NotImplementedError
