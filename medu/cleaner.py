"""
① Cleaner (normalizer)

Owner: Charllson
Takes: Raw text from the file
Gives: The same text in one standard spelling

What it must do:
    Greek α -> ɑ, every apostrophe -> ʼ, tones stored one way (NFC),
    shortcuts like e* -> ə, n* -> ŋ, extra spaces removed.
    Must match normalize() in tools/build_lexicon.py.
"""

from __future__ import annotations

def clean(text: str) -> str:
    """Return text in the standard Medumba spelling."""
    raise NotImplementedError
