"""
① Cleaner (normalizer)

Owner: Charllson
Takes: Raw text from the file
Gives: The same text in one standard spelling

Why: letters that look identical can be different characters inside the
computer (Greek α vs the Medumba letter ɑ, ' vs ʼ, ǐ stored as one or two
characters). Without cleaning, a correctly typed word is not found in the
dictionary. The dictionary (tools/build_lexicon.py) is cleaned with the same
rules, so both sides always match.

Rules:
    - Unicode NFC: a letter + tone mark is always stored the same way
    - Greek α / Α -> Medumba ɑ / Ɑ
    - ' ’ ‘ ʔ -> ʼ (the glottal-stop letter)
    - Shortcuts (Mode 2 and the prompt only): e* -> ə, e+ -> ɛ, u* -> ʉ,
      a* -> ɑ, o+ -> ɔ, n* -> ŋ (capitals too: E* -> Ə ...)
    - Windows line endings -> \\n, byte-order mark removed
    - Line structure is kept, so line numbers in errors stay correct

Mode 1 (programs): call clean(text, code=True). Shortcuts are switched off
there (a+b is arithmetic, not "ɑb") and text inside "double quotes" is only
NFC-normalised, never changed otherwise.

Helpers for the word cutter:
    plain(word)     same word without tone marks, lower case
    keyboard(word)  same word typed on a normal keyboard (ə->e, ɛ->e, ...)
"""

from __future__ import annotations

import re
import unicodedata

from medu.errors import MeduError

LOOKALIKES = {
    "α": "ɑ",  # Greek α -> Latin ɑ
    "Α": "Ɑ",  # Greek Α -> Latin Ɑ
    "'": "ʼ",       # ' -> ʼ
    "’": "ʼ",  # ’ -> ʼ
    "‘": "ʼ",  # ‘ -> ʼ
    "ʔ": "ʼ",  # ʔ -> ʼ
}

SHORTCUTS = {
    "e*": "ə", "E*": "Ə",
    "e+": "ɛ", "E+": "Ɛ",
    "u*": "ʉ", "U*": "Ʉ",
    "a*": "ɑ", "A*": "Ɑ",
    "o+": "ɔ", "O+": "Ɔ",
    "n*": "ŋ", "N*": "Ŋ",
}
_SHORTCUT_RE = re.compile("|".join(re.escape(k) for k in SHORTCUTS))

# Special letters -> what people type on a normal keyboard
KEYBOARD = {"ə": "e", "ɛ": "e", "ʉ": "u", "ɑ": "a", "ɔ": "o", "ŋ": "ng"}

_ALLOWED_CONTROL = {"\n", "\t"}


def _normalize(text: str) -> str:
    """NFD -> replace look-alikes -> NFC (same as tools/build_lexicon.py)."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(LOOKALIKES.get(ch, ch) for ch in text)
    return unicodedata.normalize("NFC", text)


def _check_characters(text: str) -> None:
    for line_no, line in enumerate(text.split("\n"), start=1):
        for col, ch in enumerate(line, start=1):
            if unicodedata.category(ch) == "Cc" and ch not in _ALLOWED_CONTROL:
                raise MeduError("E001", f"invisible control character U+{ord(ch):04X}",
                                line_no, col, hint="delete it and type the text again")


def _clean_outside_strings(text: str) -> str:
    """Mode 1: normalise everything, but leave "quoted text" as typed (NFC only)."""
    out = []
    for i, part in enumerate(re.split(r'("(?:[^"\\\n]|\\.)*")', text)):
        out.append(unicodedata.normalize("NFC", part) if i % 2 else _normalize(part))
    return "".join(out)


def clean(text: str, code: bool = False) -> str:
    """Return text in the standard Medumba spelling.

    code=False  sentences (Mode 2) and the interactive prompt: shortcuts on
    code=True   programs (Mode 1): no shortcuts, quoted text untouched
    """
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    _check_characters(text)
    if code:
        return _clean_outside_strings(text)
    text = _SHORTCUT_RE.sub(lambda m: SHORTCUTS[m.group(0)], text)
    return _normalize(text)


def plain(word: str) -> str:
    """Word without tone marks, lower case: 'nɛ̌n' -> 'nɛn'."""
    decomposed = unicodedata.normalize("NFD", word.lower())
    bare = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", bare)


def keyboard(word: str) -> str:
    """Word as typed on a normal keyboard: 'mə nɛ̌n' -> 'me nen'."""
    return "".join(KEYBOARD.get(ch, ch) for ch in plain(word))
