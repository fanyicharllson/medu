"""
The medu command: reads what the user typed in the terminal and starts the right thing.

Owner: Charllson (Adrien plugs Mode 1 in through medu/mode1.py)

    medu                      interactive prompt (medu>)
    medu translate file.mdt   Mode 2: Medumba sentences -> English
    medu run file.med         Mode 1: run a Medu program        (Medu 2.0)
    medu check file           only look for errors
    medu file.mdt / file.med  same as translate / run, picked from the extension
    medu commands             every command and what it does
    medu help | -h | --help   help: commands, words, shortcuts, contact
    medu version | -v         version
    medu upgrade [version]    install the newest (or a given) version from GitHub
    medu downgrade <version>  go back to an older version
    -q / --quiet              hide the banner

Never shows a Python traceback: Medu errors are printed with ui.error(), and
anything unexpected becomes a short message with the link to report it
(set MEDU_DEBUG=1 to see the full traceback).
"""

from __future__ import annotations

import difflib
import os
import sys
import time
from pathlib import Path

from medu import languages, mode1, mode2, ui, updater, window
from medu.cleaner import clean
from medu.errors import MeduError

# name, how to type it, what it does  (also shown by `medu commands`)
COMMANDS = [
    ("", "medu", "open the interactive prompt (medu>) and type Medumba sentences"),
    ("translate", "medu translate story.mdt", "translate a file of Medumba sentences into English"),
    ("run", "medu run program.med", "run a Medu program written with Medumba keywords"),
    ("check", "medu check story.mdt", "only look for mistakes, translate nothing"),
    ("commands", "medu commands", "this list"),
    ("help", "medu help", "help: commands, words to start with, keyboard shortcuts, contact"),
    ("version", "medu version", "show the version (also: medu -v, medu --version)"),
    ("upgrade", "medu upgrade", "install the newest Medu from GitHub (needs internet)"),
    ("upgrade", "medu upgrade 1.2.0", "install a specific version"),
    ("downgrade", "medu downgrade 1.0.0", "go back to an older version"),
]
OPTIONS = [
    ("-q, --quiet", "hide the banner, e.g. medu -q translate story.mdt"),
    ("--no-color", "plain text, no colours"),
]
ALIASES = {"-v": "version", "--version": "version", "-h": "help", "--help": "help",
           "/?": "help", "--commands": "commands", "-c": "commands"}


def commands_text() -> str:
    width = max(len(usage) for _, usage, _ in COMMANDS) + 2
    lines = [ui.paint("Medu commands", ui.OCHRE, ui.BOLD)]
    lines += [f"  {ui.paint(usage.ljust(width), ui.INDIGO, ui.BOLD)}{what}"
              for _, usage, what in COMMANDS]
    lines += ["", ui.paint("Options", ui.OCHRE, ui.BOLD)]
    lines += [f"  {ui.paint(opt.ljust(width), ui.INDIGO, ui.BOLD)}{what}" for opt, what in OPTIONS]
    lines += ["", ui.paint("Files", ui.OCHRE, ui.BOLD),
              f"  {'.mdt'.ljust(width)}Medumba text (sentences)  -> medu translate",
              f"  {'.med'.ljust(width)}Medu program              -> medu run",
              "", ui.note("Inside medu> type: help, cls, version, exit")]
    return "\n".join(lines)


def _read(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        print(ui.paint(f"error: cannot open '{path}'", ui.RED, ui.BOLD))
        print(ui.note("check the file name and folder, e.g. samples/sentences.mdt"))
        return None


def _load():
    start = time.perf_counter()
    lang = languages.load("medumba")
    return lang, time.perf_counter() - start


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_translate(args: list[str], quiet: bool) -> int:
    if not args:
        print(ui.paint("usage: medu translate story.mdt", ui.OCHRE))
        return 1
    lang, load = _load()
    return mode2.translate_file(args[0], lang, load, quiet)


def cmd_run(args: list[str], quiet: bool) -> int:
    if not args:
        print(ui.paint("usage: medu run program.med", ui.OCHRE))
        return 1
    source = _read(args[0])
    if source is None:
        return 1
    lang, _ = _load()
    if not quiet:
        print(ui.banner(lang.name, hint=False))
    print(ui.header(lang.name, f"run {Path(args[0]).name}") + "\n")
    start = time.perf_counter()
    try:
        result = mode1.run(source, lang)
    except NotImplementedError:
        print(ui.paint("Medu programs (.med) arrive in Medu 2.0.", ui.OCHRE, ui.BOLD))
        print(ui.note("For now, translate sentences: medu translate story.mdt"))
        return 1
    except MeduError as err:
        print(ui.error(err, args[0], clean(source, code=True)))
        print("\n" + ui.timing(f"Stopped after {ui.ms(time.perf_counter() - start)}"))
        return 1
    print(ui.section("English version"))
    print(result.english + "\n")
    print(ui.section("Output"))
    for line in result.output:
        print(ui.result(line))
    print("\n" + ui.timing(f"Ran in {ui.ms(time.perf_counter() - start)}"))
    return 0


def cmd_check(args: list[str], quiet: bool) -> int:
    if not args:
        print(ui.paint("usage: medu check story.mdt", ui.OCHRE))
        return 1
    path = args[0]
    source = _read(path)
    if source is None:
        return 1
    lang, _ = _load()
    is_program = Path(path).suffix.lower() == ".med"
    start = time.perf_counter()
    try:
        if is_program:
            mode1.check(source, lang)
            what = "program"
        else:
            what = f"{len(mode2.translate(source, lang).lines)} sentence(s)"
    except NotImplementedError:
        print(ui.paint("Checking Medu programs (.med) arrives in Medu 2.0.", ui.OCHRE))
        return 1
    except MeduError as err:
        print(ui.error(err, path, clean(source, code=is_program)))
        return 1
    print(ui.timing(f"No mistakes in {Path(path).name} ({what}, {ui.ms(time.perf_counter() - start)})"))
    return 0


def cmd_by_extension(path: str, quiet: bool) -> int:
    ext = Path(path).suffix.lower()
    if ext not in languages.EXTENSIONS:
        return unknown(path)
    _, mode = languages.EXTENSIONS[ext]
    return cmd_run([path], quiet) if mode == 1 else cmd_translate([path], quiet)


def unknown(word: str) -> int:
    names = sorted({name for name, _, _ in COMMANDS if name} | {"help", "version"})
    close = difflib.get_close_matches(word.lower(), names, n=1, cutoff=0.5)
    print(ui.paint(f"error: '{word}' is not a Medu command", ui.RED, ui.BOLD))
    if close:
        print(ui.note(f"did you mean: medu {close[0]}"))
    print(ui.note("see every command with: medu commands"))
    return 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

MODE_SENTENCES = "Mode 2 · Sentences → English"
MODE_PROGRAMS = "Mode 1 · Programs"


def _activity(argv: list[str]) -> str:
    """What the title bar of the Medu window says for this command."""
    if not argv:
        return MODE_SENTENCES
    command = ALIASES.get(argv[0].lower(), argv[0].lower())
    target = Path(argv[1]).name if len(argv) > 1 else ""
    if command in ("translate", "check") and target:
        mode = MODE_PROGRAMS if target.lower().endswith(".med") else "Mode 2"
        return f"{mode.split(' · ')[0]} · {'checking' if command == 'check' else 'translating'} {target}"
    if command == "run":
        return f"Mode 1 · running {target}" if target else MODE_PROGRAMS
    if "." in argv[0]:
        name = Path(argv[0]).name
        return (f"Mode 1 · running {name}" if name.lower().endswith(".med")
                else f"Mode 2 · translating {name}")
    return {"help": "Help", "commands": "Commands", "version": "About",
            "upgrade": "Upgrading", "downgrade": "Changing version"}.get(command, "")


def _dispatch(argv: list[str]) -> int:
    quiet = any(a in ("-q", "--quiet") for a in argv)
    color = False if "--no-color" in argv else None
    argv = [a for a in argv if a not in ("-q", "--quiet", "--no-color")]
    ui.setup(color)
    window.brand(_activity(argv))          # only in Medu's own window
    if not argv:
        lang, load = _load()
        return mode2.interactive(lang, load, quiet)
    command, args = ALIASES.get(argv[0].lower(), argv[0].lower()), argv[1:]
    if command == "commands":
        print(commands_text())
        return 0
    if command == "help":
        print(ui.banner("medumba", hint=False))
        print(ui.help_text())
        return 0
    if command == "version":
        print(ui.version_text())
        return 0
    if command == "translate":
        return cmd_translate(args, quiet)
    if command == "run":
        return cmd_run(args, quiet)
    if command == "check":
        return cmd_check(args, quiet)
    if command == "upgrade":
        return updater.install(args[0] if args else None)
    if command == "downgrade":
        if not args:
            print(ui.paint("usage: medu downgrade <version>   e.g. medu downgrade 1.0.0", ui.OCHRE))
            versions = updater.list_versions()
            if versions:
                print(ui.note("Available versions: " + ", ".join(versions)))
            return 1
        return updater.install(args[0], allow_older=True)
    if "." in argv[0]:                     # medu story.mdt
        return cmd_by_extension(argv[0], quiet)
    return unknown(argv[0])


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        code = _dispatch(argv)
    except KeyboardInterrupt:
        print()
        return 130
    except Exception:                      # never show a traceback to users
        if os.environ.get("MEDU_DEBUG"):
            raise
        print(ui.paint("Medu hit an unexpected problem.", ui.RED, ui.BOLD))
        print(ui.note(f"Please report it: {ui.REPO}/issues  (details: set MEDU_DEBUG=1)"))
        code = 2
    if argv:                               # a double-clicked file: let them read it
        window.keep_open()
    return code


if __name__ == "__main__":
    sys.exit(main())
