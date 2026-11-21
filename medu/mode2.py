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
import time
from pathlib import Path

from medu import checker_text, english, languages, meaning, parser_text, ui, updater  # noqa: F401
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

    def spell(t):
        if t.kind != WORD or not t.value:
            return t.text
        return chosen.get(id(t)) or min(t.value, key=parser_text._rank)["medumba"]

    result.sources, result.typed = [], []
    for s in sentences:
        words = [t for t in s.tokens if t.kind == WORD]
        punct = "".join(t.text for t in s.tokens if t.kind != WORD and t.text in ".?!")
        result.sources.append(" ".join(spell(t) for t in words) + punct)
        result.typed.append(" ".join(t.text for t in words) + punct)
    standard = [spell(t) for t in tokens if t.kind == WORD and t.value]
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
    """Each sentence as a pair:

        Medumba   mə nɛ̌n zi        (you typed: me nen zi)
        English   I am sleeping.
    """
    many = len(result.lines) > 1
    for i, english_line in enumerate(result.lines):
        source = result.sources[i] if i < len(result.sources) else ""
        typed = result.typed[i] if i < len(result.typed) else source
        num = ui.paint(f"{i + 1:>2}  ", ui.DIM) if many else ""
        pad = "    " if many else ""
        extra = ui.note(f"(you typed: {typed})") if typed != source else ""
        print(f"{num}{ui.label('Medumba')} {source}{extra}")
        print(f"{pad}{ui.label('English')} {ui.result(english_line)}")
        if many:
            print()
    for w in result.warnings:
        print(ui.paint(w, ui.OCHRE))
    for n in result.notes:
        print(ui.note(n))


def translate_file(path: str, lang: Language, load_ms: float = 0.0,
                   quiet: bool = False) -> int:
    try:
        source = Path(path).read_text(encoding="utf-8")
    except OSError:
        print(ui.paint(f"error: cannot open '{path}'", ui.RED, ui.BOLD))
        print(ui.note("check the file name and folder, e.g. samples/sentences.mdt"))
        return 1
    if not quiet:
        print(ui.banner(lang.name, hint=False))
    print(ui.header(lang.name, f"translate {Path(path).name}") + "\n")
    start = time.perf_counter()
    try:
        result = translate(source, lang)
    except MeduError as err:
        print(ui.error(err, path, clean(source)))
        print("\n" + ui.timing(f"Stopped after {ui.ms(time.perf_counter() - start)}"))
        return 1
    show(result)
    n = len(result.lines)
    print("\n" + ui.timing(f"Translated {n} sentence{'s' * (n != 1)} in "
                           f"{ui.ms(time.perf_counter() - start)}"
                           f" (dictionary loaded in {ui.ms(load_ms)})"))
    return 0


PROMPT_COMMANDS = {"exit", "quit", "help", "cls", "clear", "version"}


def interactive(lang: Language, load_ms: float = 0.0, quiet: bool = False) -> int:
    if quiet:
        print(ui.timing(f"Started in {ui.ms(load_ms)} · {len(lang.entries):,} words loaded") + "\n")
    else:
        print(ui.welcome(lang.name, len(lang.entries), load_ms))
    notice = updater.UpdateNotice()          # quiet, background, offline-safe
    while True:
        if (msg := notice.message()):
            print(msg + "\n")
        try:
            line = input(ui.prompt())
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        command = line.strip().lower()
        if command in ("exit", "quit"):
            print(ui.note("Bye!"))
            return 0
        if command == "help":
            print(ui.help_text(prompt_mode=True) + "\n")
            continue
        if command in ("cls", "clear"):
            ui.clear_screen()
            print(ui.welcome(lang.name, len(lang.entries), load_ms))
            continue
        if command == "version":
            print(ui.version_text() + "\n")
            continue
        if not command:
            continue
        start = time.perf_counter()
        try:
            show(translate(line, lang))
            print(ui.timing(ui.ms(time.perf_counter() - start)))
        except MeduError as err:
            print(ui.error(err, "<prompt>", clean(line)))
        print()


def main(argv: list[str] | None = None) -> int:
    """`python -m medu.mode2 ...` behaves exactly like the medu command."""
    from medu import cli
    return cli.main(argv)


if __name__ == "__main__":
    sys.exit(main())
