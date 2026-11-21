"""
② Word cutter (lexer)

Owner: Charllson
Takes: Text (raw or clean) + the Language (lexicon, keywords)
Gives: list[Token], ending with an EOF token

Both functions run the cleaner first, so callers can pass raw file text.
Line and column numbers refer to the cleaned text: when showing an error,
pass clean(source) (or clean(source, code=True)) to MeduError.format().

tokenize_code  (Mode 1, programs)
    NAME, STRING, NUMBER, OP (= + - * /), LPAREN, RPAREN, NEWLINE, EOF.
    A word that is a keyword in this language becomes KEYWORD with the
    concept as value ("PRINT"); plain keyboard letters work too (du -> dʉ).
    # starts a comment. Text inside "double quotes" is never changed.
    A name directly followed by "(" must be a keyword, else E101.

tokenize_text  (Mode 2, sentences)
    WORD tokens: value = list of possible dictionary entries.
    Lookup order: exact spelling, then without tones, then keyboard letters.
    Longest match first, so multi-word expressions become one token.
    A capitalised unknown word is kept as a name (pos "np").
    An unknown word raises E101 with "did you mean ...?".
    PUNCT tokens for . ? ! , ;  and an EOF token at the end.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass, field

from medu.cleaner import clean, keyboard, plain
from medu.errors import MeduError
from medu.languages import Language
from medu.tokens import (EOF, KEYWORD, LPAREN, NAME, NEWLINE, NUMBER, OP, PUNCT,
                         RPAREN, STRING, WORD, Token)

GLOTTAL = "ʼ"  # ʼ counts as a letter
OPERATORS = set("=+-*/")
SENTENCE_PUNCT = set(".?!,;:")


def _is_letter(ch: str) -> bool:
    cat = unicodedata.category(ch)
    return cat.startswith("L") or cat == "Mn" or ch == GLOTTAL


def _vcol(line: str, i: int) -> int:
    """Column as the user sees it: tone marks (combining) take no space."""
    return 1 + sum(1 for ch in line[:i] if unicodedata.category(ch) != "Mn")


def _english(entry: dict) -> str:
    """Short meaning for messages: checked English, then auto English, then French."""
    for key in ("gloss_en", "gloss_en_auto", "gloss_fr"):
        if entry.get(key):
            return re.sub(r"\s*\(.*?\)", "", entry[key][0]).strip() or entry[key][0]
    return "?"


def _meaning_rank(entry: dict) -> int:
    """0 = checked English, 1 = auto English, 2 = French only, 3 = nothing."""
    for rank, key in enumerate(("gloss_en", "gloss_en_auto", "gloss_fr")):
        if entry.get(key):
            return rank
    return 3


# ---------------------------------------------------------------------------
# Dictionary index (built once per language)
# ---------------------------------------------------------------------------

@dataclass
class _Index:
    exact: dict[str, list[dict]] = field(default_factory=dict)
    plain: dict[str, list[dict]] = field(default_factory=dict)
    keyboard: dict[str, list[dict]] = field(default_factory=dict)
    max_words: int = 1


_INDEXES: dict[int, _Index] = {}


def _index(lang: Language) -> _Index:
    idx = _INDEXES.get(id(lang))
    if idx is None:
        idx = _Index()
        for e in lang.entries:
            word = e["medumba"]
            idx.exact.setdefault(word.lower(), []).append(e)
            idx.plain.setdefault(plain(word), []).append(e)
            idx.keyboard.setdefault(keyboard(word), []).append(e)
            idx.max_words = max(idx.max_words, len(word.split()))
        _INDEXES[id(lang)] = idx
    return idx


def _lookup(idx: _Index, phrase: str) -> list[dict]:
    """Strictest match first: exact, then without tones, then keyboard.

    Expressions of several words never match through keyboard letters:
    'mə jʉ' (I eat) must not become the expression 'mə ju'."""
    found = idx.exact.get(phrase.lower())
    if found:
        return found
    if " " in phrase:
        return idx.plain.get(plain(phrase)) or []
    # one word, not spelled exactly: every word with the same keyboard letters
    # (this includes the tone-free matches); the parser picks the best meaning
    return idx.keyboard.get(keyboard(phrase)) or []


def _suggest(idx: _Index, word: str) -> str | None:
    close = difflib.get_close_matches(keyboard(word), list(idx.keyboard), n=8,
                                      cutoff=0.6)
    if not close:
        return None
    # closest spelling first; among equally close words, the best-known meaning
    candidates = [(pos, _meaning_rank(e), e) for pos, key in enumerate(close)
                  for e in idx.keyboard[key]]
    known = [c for c in candidates if c[1] < 3]
    if not known:
        return f"did you mean '{candidates[0][2]['medumba']}'?"
    best = min(known, key=lambda c: (c[1] > 0, c[0], c[1]))[2]
    return f"did you mean '{best['medumba']}' ({_english(best)})?"


# ---------------------------------------------------------------------------
# Mode 2: sentences
# ---------------------------------------------------------------------------

def _split_words(line: str):
    """Yield (kind, text, index) for words and punctuation in one line."""
    i = 0
    while i < len(line):
        ch = line[i]
        if ch.isspace():
            i += 1
        elif _is_letter(ch) or ch.isdigit():
            start = i
            while i < len(line) and (_is_letter(line[i]) or line[i].isdigit()
                                     or line[i] == "-"):
                i += 1
            yield "word", line[start:i], start
        elif ch in SENTENCE_PUNCT:
            yield "punct", ch, i
            i += 1
        else:
            yield "other", ch, i
            i += 1


def tokenize_text(text: str, lang: Language) -> list[Token]:
    """Mode 2: cut sentences into WORD / PUNCT tokens."""
    idx = _index(lang)
    tokens: list[Token] = []
    for line_no, line in enumerate(clean(text).split("\n"), start=1):
        pieces = list(_split_words(line))
        i = 0
        while i < len(pieces):
            kind, piece, pos = pieces[i]
            col = _vcol(line, pos)
            if kind == "punct":
                tokens.append(Token(PUNCT, piece, None, line_no, col))
                i += 1
                continue
            if kind == "other":
                raise MeduError("E102", f"unexpected character '{piece}'",
                                line_no, col)
            if piece.isdigit():
                tokens.append(Token(WORD, piece, [{"medumba": piece, "pos": "num",
                                                   "gloss_en": [piece]}], line_no, col))
                i += 1
                continue
            # longest run of following words that is one dictionary entry
            match_len, entries = 0, []
            for n in range(min(idx.max_words, len(pieces) - i), 0, -1):
                run = pieces[i:i + n]
                if any(k != "word" for k, _, _ in run):
                    continue
                found = _lookup(idx, " ".join(p for _, p, _ in run))
                if found:
                    match_len, entries = n, found
                    break
            if entries:
                end_piece = pieces[i + match_len - 1]
                text_span = line[pos:end_piece[2] + len(end_piece[1])]
                tokens.append(Token(WORD, text_span, entries, line_no, col))
                i += match_len
            elif piece[0].isupper():
                tokens.append(Token(WORD, piece, [{"medumba": piece, "pos": "np",
                                                   "gloss_en": [piece]}], line_no, col))
                i += 1
            else:
                raise MeduError("E101", f"unknown word '{piece}'", line_no, col,
                                hint=_suggest(idx, piece))
    tokens.append(Token(EOF, "", None, len(text.split("\n")), 1))
    return tokens


# ---------------------------------------------------------------------------
# Mode 1: programs
# ---------------------------------------------------------------------------

def _keyword_concept(lang: Language, word: str) -> str | None:
    concept = lang.concept_for(word)
    if concept:
        return concept
    typed = keyboard(word)
    for concept, kw in lang.keywords.items():
        if keyboard(kw) == typed:
            return concept
    return None


def _keyword_hint(lang: Language, word: str) -> str | None:
    by_key = {keyboard(kw): (kw, concept) for concept, kw in lang.keywords.items()}
    close = difflib.get_close_matches(keyboard(word), list(by_key), n=1, cutoff=0.4)
    if not close:
        return None
    kw, concept = by_key[close[0]]
    return f"did you mean '{kw}' ({concept.lower()})?"


def _read_string(line: str, start: int, line_no: int) -> tuple[str, int]:
    """Read "..." starting at line[start] == '"'. Returns (value, next index)."""
    out, i = [], start + 1
    escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
    while i < len(line):
        ch = line[i]
        if ch == '"':
            return "".join(out), i + 1
        if ch == "\\" and i + 1 < len(line):
            out.append(escapes.get(line[i + 1], line[i + 1]))
            i += 2
            continue
        out.append(ch)
        i += 1
    raise MeduError("E103", 'text is not closed: missing "', line_no, _vcol(line, start),
                    hint='end the text with " on the same line')


def tokenize_code(text: str, lang: Language) -> list[Token]:
    """Mode 1: cut a program into tokens."""
    tokens: list[Token] = []
    lines = clean(text, code=True).split("\n")
    for line_no, line in enumerate(lines, start=1):
        i = 0
        line_tokens: list[Token] = []
        while i < len(line):
            ch, col = line[i], _vcol(line, i)
            if ch.isspace():
                i += 1
            elif ch == "#":
                break
            elif ch == '"':
                start = i
                value, i = _read_string(line, i, line_no)
                line_tokens.append(Token(STRING, line[start:i], value, line_no, col))
            elif ch.isdigit():
                start = i
                while i < len(line) and (line[i].isdigit() or line[i] == "."):
                    i += 1
                raw = line[start:i]
                try:
                    value = int(raw) if "." not in raw else float(raw)
                except ValueError:
                    raise MeduError("E104", f"'{raw}' is not a number", line_no, col)
                line_tokens.append(Token(NUMBER, raw, value, line_no, col))
            elif _is_letter(ch) or ch == "_":
                start = i
                while i < len(line) and (_is_letter(line[i]) or line[i].isdigit()
                                         or line[i] == "_"):
                    i += 1
                word = line[start:i]
                concept = _keyword_concept(lang, word)
                if concept:
                    line_tokens.append(Token(KEYWORD, word, concept, line_no, col))
                else:
                    rest = line[i:].lstrip()
                    if rest.startswith("("):
                        raise MeduError("E101", f"unknown word '{word}'", line_no, col,
                                        hint=_keyword_hint(lang, word))
                    line_tokens.append(Token(NAME, word, None, line_no, col))
            elif ch in OPERATORS:
                line_tokens.append(Token(OP, ch, None, line_no, col))
                i += 1
            elif ch == "(":
                line_tokens.append(Token(LPAREN, ch, None, line_no, col))
                i += 1
            elif ch == ")":
                line_tokens.append(Token(RPAREN, ch, None, line_no, col))
                i += 1
            else:
                raise MeduError("E102", f"unexpected character '{ch}'", line_no, col)
        if line_tokens:
            tokens += line_tokens
            tokens.append(Token(NEWLINE, "", None, line_no, _vcol(line, len(line))))
    tokens.append(Token(EOF, "", None, len(lines), 1))
    return tokens
