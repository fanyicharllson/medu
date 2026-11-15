"""
Interpreter (Mode 1)

Owner: Adrien
Takes: Checked Program AST + Language
Gives: Program output, and the English version of the code

What it must do:
    run(): executes statements, prints with print().
    to_english(): same program with English keywords, names unchanged.
    E401 division by zero at run time.
"""

from __future__ import annotations

def run(program) -> None:
    raise NotImplementedError


def to_english(program, lang) -> str:
    raise NotImplementedError
