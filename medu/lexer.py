"""
② Word cutter (lexer)

Owner: Charllson
Takes: Clean text + the Language (lexicon, keywords)
Gives: list[Token], ending with an EOF token

What it must do:
    tokenize_code: names, strings, numbers, = + - * / ( ), keywords via
    lang.concept_for(). Comments (#) dropped. Text in quotes untouched.
    tokenize_text: dictionary lookup (exact, then without tones, then
    plain keyboard letters); WORD tokens keep every candidate entry.
    Unknown word -> raise MeduError('E101', ..., hint='did you mean ...').
"""

from __future__ import annotations

from medu.languages import Language
from medu.tokens import Token


def tokenize_code(text: str, lang: Language) -> list[Token]:
    """Mode 1: cut a program into tokens."""
    raise NotImplementedError


def tokenize_text(text: str, lang: Language) -> list[Token]:
    """Mode 2: cut sentences into WORD / PUNCT tokens."""
    raise NotImplementedError
