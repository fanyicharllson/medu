"""Tests for ① the cleaner."""

import unicodedata

import pytest

from medu import languages
from medu.cleaner import clean, keyboard, plain
from medu.errors import MeduError


def test_greek_alpha_becomes_medumba_letter():
    assert clean("fα") == "fɑ"


def test_apostrophes_become_glottal_letter():
    for typed in ("zi'", "zi’", "zi‘", "ziʔ"):
        assert clean(typed) == "ziʼ"


def test_tone_mark_stored_one_way():
    two_chars = "zǐ"          # i + separate caron
    assert clean(two_chars) == unicodedata.normalize("NFC", "zǐ")
    assert clean(two_chars) == clean("zǐ")


def test_shortcuts_in_sentences():
    assert clean("me* ne+n zi") == "mə nɛn zi"
    assert clean("n*ko+") == "ŋkɔ"


def test_no_shortcuts_in_code():
    assert clean("a+b", code=True) == "a+b"
    assert clean("e*2", code=True) == "e*2"


def test_quoted_text_untouched_in_code():
    src = 'lɛn = "don\'t α"\ndʉ(lɛn)'
    out = clean(src, code=True)
    assert '"don\'t α"' in out          # inside quotes: unchanged


def test_line_structure_kept():
    assert clean("mə\r\nzi\r\n").split("\n") == ["mə", "zi", ""]


def test_bom_removed():
    assert clean("﻿zi") == "zi"


def test_control_character_rejected():
    with pytest.raises(MeduError) as err:
        clean("zi\x07")
    assert err.value.code == "E001"
    assert (err.value.line, err.value.col) == (1, 3)


def test_plain_and_keyboard_forms():
    assert plain("nɛ̌n") == "nɛn"
    assert keyboard("mə nɛ̌n zi") == "me nen zi"
    assert keyboard("ŋkɔ") == "ngko"


def test_dictionary_already_clean():
    """Every dictionary word must come out of the cleaner unchanged,
    otherwise user text and dictionary would not match."""
    for entry in languages.load("medumba").entries:
        assert clean(entry["medumba"]) == entry["medumba"], entry["medumba"]
