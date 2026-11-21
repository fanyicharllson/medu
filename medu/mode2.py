"""
Mode 2 pipeline: Medumba sentences -> English.

Owner: Charllson
Used by: cli.py (Adrien) for `medu translate` and the interactive prompt.

    from medu import mode2
    result = mode2.translate("mə nɛ̌n zi.", lang)   # runs ① to ⑥
    result.lines     -> ["I am sleeping."]
    result.read_as   -> "mə nɛ̌n zi" when the user typed plain letters
    result.notes     -> meanings not yet checked by a speaker
    result.warnings  -> W301 word-by-word parts

Test it now, before cli.py exists:
    python -m medu.mode2                  interactive prompt
    python -m medu.mode2 story.mdt        translate a file
"""

from __future__ import annotations

import sys
from pathlib import Path

from medu import checker_text, english, languages, meaning, parser_text, ui
from medu.cleaner import clean
from medu.errors import MeduError
from medu.languages import Language
from medu.lexer import tokenize_text
from medu.tokens import WORD


def translate(text: str, lang: Language) -> english.Result:
    """Run stations ① to ⑥. Raises MeduError on any error."""
    tokens = tokenize_text(text, lang)                     # ① ②
    sentences = parser_text.parse(tokens, lang)            # ③
    checker_text.check(sentences)                          # ④
    meanings = meaning.build(sentences, lang)              # ⑤
    result = english.write(meanings)                       # ⑥
    chosen = _chosen_spellings(sentences)
    standard = [chosen.get(id(t)) or min(t.value, key=parser_text._rank)["medumba"]
                for t in tokens if t.kind == WORD and t.value]
    typed = [t.text for t in tokens if t.kind == WORD]
    result.read_as = " ".join(standard) if standard != typed else ""
    return result


def _chosen_spellings(sentences) -> dict[int, str]:
    """token id -> spelling of the meaning the grammar check picked."""
    out: dict[int, str] = {}

    def np(n):
        out[id(n.token)] = n.entry.get("medumba", n.token.text)
        for tok, e in n.adjectives:
            out[id(tok)] = e["medumba"]

    for s in sentences:
        for c in s.clauses:
            if c.subject:
                np(c.subject)
            out[id(c.verb_token)] = c.verb["medumba"]
            for o in c.objects:
                np(o)
            for tok, e in c.adverbs:
                out[id(tok)] = e["medumba"]
        for tok, e in s.connectors:
            if e:
                out[id(tok)] = e["medumba"]
    return out


def show(result: english.Result) -> None:
    for line in result.lines:
        print(ui.result(line))
    if result.read_as:
        print(ui.note(f"(read as: {result.read_as})"))
    for w in result.warnings:
        print(ui.paint(w, ui.OCHRE))
    for n in result.notes:
        print(ui.note(n))


def translate_file(path: str, lang: Language) -> int:
    source = Path(path).read_text(encoding="utf-8")
    print(ui.header(lang.name, "translate") + "\n")
    try:
        show(translate(source, lang))
        return 0
    except MeduError as err:
        print(ui.error(err, path, clean(source)))
        return 1


def interactive(lang: Language) -> int:
    print(ui.banner(lang.name))
    while True:
        try:
            line = input(ui.prompt())
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if line.strip().lower() in ("exit", "quit"):
            return 0
        if not line.strip():
            continue
        try:
            show(translate(line, lang))
        except MeduError as err:
            print(ui.error(err, "<prompt>", clean(line)))
        print()


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ui.setup()
    lang = languages.load("medumba")
    if argv:
        return translate_file(argv[0], lang)
    return interactive(lang)


if __name__ == "__main__":
    sys.exit(main())
