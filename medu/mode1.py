"""
Mode 1 pipeline: a Medu program (.med) -> run it, plus its English version.

Owner: Adrien
Used by: cli.py (`medu run file.med`, `medu check file.med`) - already wired.

Fill in run() and check() using your stations:
    lexer.tokenize_code(source, lang)    ①②  (Charllson, done)
    parser_code.parse(tokens)            ③   (Adrien)
    checker_code.check(program)          ④   (Adrien)
    interpreter: run it, collect what it prints, build the English version

Until they work, both raise NotImplementedError and cli.py tells the user
"Medu programs (.med) arrive in Medu 2.0".
"""

from __future__ import annotations

from dataclasses import dataclass, field

from medu.languages import Language


@dataclass
class ProgramResult:
    english: str                                  # the program with English keywords
    output: list[str] = field(default_factory=list)   # every line the program printed


def run(source: str, lang: Language) -> ProgramResult:
    """Check and run a program. Raise MeduError for any mistake (E1xx-E4xx)."""
    raise NotImplementedError


def check(source: str, lang: Language) -> None:
    """Only look for mistakes (stations ①-④). Raise MeduError for the first one."""
    raise NotImplementedError
