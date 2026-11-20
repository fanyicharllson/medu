"""Tests for ② the word cutter (lexer)."""

import pytest

from medu import languages
from medu.errors import MeduError
from medu.lexer import tokenize_code, tokenize_text
from medu.tokens import (EOF, KEYWORD, LPAREN, NAME, NEWLINE, NUMBER, OP, PUNCT,
                         RPAREN, STRING, WORD)

LANG = languages.load("medumba")


def kinds(tokens):
    return [t.kind for t in tokens]


# ---------------- Mode 1: programs ----------------

def test_hello_program():
    toks = tokenize_code('lɛn = "Emperor"\ndʉ(lɛn)\n', LANG)
    assert kinds(toks) == [NAME, OP, STRING, NEWLINE,
                           KEYWORD, LPAREN, NAME, RPAREN, NEWLINE, EOF]
    assert toks[2].value == "Emperor"
    assert toks[4].value == "PRINT"
    assert (toks[4].line, toks[4].col) == (2, 1)


def test_keyword_typed_with_plain_letters():
    toks = tokenize_code("du(x)", LANG)
    assert toks[0].kind == KEYWORD and toks[0].value == "PRINT"


def test_numbers_and_operators():
    toks = tokenize_code("dʉ((2 + 3.5) * 4)", LANG)
    assert [t.value for t in toks if t.kind == NUMBER] == [2, 3.5, 4]
    assert [t.text for t in toks if t.kind == OP] == ["+", "*"]


def test_comments_and_blank_lines_dropped():
    toks = tokenize_code("# a comment\n\nx = 1  # value\n", LANG)
    assert kinds(toks) == [NAME, OP, NUMBER, NEWLINE, EOF]


def test_quoted_text_kept_exactly():
    toks = tokenize_code('x = "a+b e* don\'t"', LANG)
    assert toks[2].value == "a+b e* don't"


def test_unknown_function_word():
    with pytest.raises(MeduError) as err:
        tokenize_code("dd(lɛn)", LANG)
    assert err.value.code == "E101"
    assert "dʉ" in err.value.hint


def test_unclosed_text():
    with pytest.raises(MeduError) as err:
        tokenize_code('x = "Joy', LANG)
    assert err.value.code == "E103"
    assert (err.value.line, err.value.col) == (1, 5)


def test_unexpected_character():
    with pytest.raises(MeduError) as err:
        tokenize_code("x = 5 % 2", LANG)
    assert err.value.code == "E102"


# ---------------- Mode 2: sentences ----------------

def test_sleep_sentence():
    toks = tokenize_text("mə nɛ̌n zi.", LANG)
    assert kinds(toks) == [WORD, WORD, WORD, PUNCT, EOF]
    assert any(e["pos"] == "prn" for e in toks[0].value)   # mə = I
    assert any(e["pos"] == "v" for e in toks[2].value)     # zi = sleep
    assert toks[2].col == 8


def test_plain_keyboard_letters():
    toks = tokenize_text("me nen zi", LANG)
    assert [t.value[0]["medumba"] for t in toks[:3]] == ["mə", "nɛ̌n", "zi"]


def test_exact_spelling_wins_over_tone_free_match():
    toks = tokenize_text("zǐ", LANG)
    assert {e["medumba"] for e in toks[0].value} == {"zǐ"}


def test_word_with_several_meanings_keeps_all():
    toks = tokenize_text("mbwə", LANG)
    assert {e["pos"] for e in toks[0].value} >= {"n", "v"}


def test_multi_word_expression_is_one_token():
    toks = tokenize_text("tsin ndô num nka", LANG)
    assert kinds(toks) == [WORD, EOF]


def test_capitalised_unknown_word_is_a_name():
    toks = tokenize_text("Ariane", LANG)
    assert toks[0].value[0]["pos"] == "np"


def test_unknown_word_suggests_close_word():
    with pytest.raises(MeduError) as err:
        tokenize_text("mə zii.", LANG)
    assert err.value.code == "E101"
    assert (err.value.line, err.value.col) == (1, 4)
    assert err.value.hint.startswith("did you mean 'zi' (sleep")
