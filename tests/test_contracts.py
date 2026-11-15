"""Tests for the shared contracts (tokens, errors, languages)."""

import pytest

from medu import languages
from medu.errors import MeduError
from medu.tokens import NAME, Token


def test_token_rejects_unknown_kind():
    with pytest.raises(ValueError):
        Token("BANANA", "x")


def test_token_repr():
    assert repr(Token(NAME, "lɛn", line=1, col=1)) == "[NAME 'lɛn' 1:1]"


def test_error_format_points_at_column():
    err = MeduError("E101", "unknown word 'zii'", line=1, col=4,
                    hint="did you mean 'zi' (sleep)?")
    text = err.format("story.mdt", "mə zii.")
    assert "error[E101]: unknown word 'zii'" in text
    assert " --> story.mdt:1:4" in text
    assert "1 | mə zii." in text
    assert "  |    ^" in text
    assert "help: did you mean 'zi' (sleep)?" in text


def test_load_medumba():
    lang = languages.load("medumba")
    assert len(lang.entries) > 2000
    assert lang.keyword_for("PRINT") == "dʉ"
    assert lang.concept_for("dʉ") == "PRINT"
    assert "medumba" in languages.available()


def test_extensions_pick_language_and_mode():
    assert languages.EXTENSIONS[".med"] == ("medumba", 1)
    assert languages.EXTENSIONS[".mdt"] == ("medumba", 2)
