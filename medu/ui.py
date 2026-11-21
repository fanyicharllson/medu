"""
Terminal look and feel: the Medu banner, colours and styled output.

Owner: Charllson (shared - every message the user sees goes through here).
Used by: cli.py (Adrien).

    from medu import ui
    ui.setup()                         # once, at start: UTF-8 + colours on Windows
    print(ui.banner("medumba"))        # big banner: interactive prompt, --version
    print(ui.header("medumba", "run")) # one line: medu run / translate
    print(ui.section("English version"))
    print(ui.result("Emperor"))
    print(ui.error(err, filename, clean_source))

Colours switch off automatically when output goes to a file, or when the
NO_COLOR environment variable is set. FORCE_COLOR=1 forces them on.
Preview everything with:  python -m medu.ui
"""

from __future__ import annotations

import os
import sys

from medu import __authors__, __company__, __version__
from medu.errors import MeduError

# 256-colour palette, inspired by Ndop cloth: indigo and ochre
INDIGO = "38;5;69"
OCHRE = "38;5;172"
GREEN = "38;5;71"
RED = "38;5;203"
DIM = "2"
BOLD = "1"

LOGO = r"""
 __  __ _____ ____  _   _
|  \/  | ____|  _ \| | | |
| |\/| |  _| | | | | | | |
| |  | | |___| |_| | |_| |
|_|  |_|_____|____/ \___/
"""

LANGUAGE_NAMES = {"medumba": "Mə̀dʉ̂mbɑ̀", "bafut": "Bɨfɨɨ̀"}

_color: bool | None = None


def _enable_windows_ansi() -> None:
    """Old Windows consoles need this switch before they show colours."""
    if os.name != "nt":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # stdout
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def _git_bash_terminal() -> bool:
    """Git Bash (mintty) talks to Python through a pipe, so isatty() says no
    even though the window shows colours. Not when writing to a file."""
    if not os.environ.get("TERM", "").startswith("xterm"):
        return False
    try:
        import stat
        return not stat.S_ISREG(os.fstat(sys.stdout.fileno()).st_mode)
    except (OSError, ValueError, AttributeError):
        return False


def setup(color: bool | None = None) -> None:
    """Call once at start-up. color=None decides automatically."""
    global _color
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8-sig" if stream is sys.stdin else "utf-8")
        except (AttributeError, ValueError):
            pass
    if color is None:
        if os.environ.get("NO_COLOR"):
            color = False
        elif os.environ.get("FORCE_COLOR"):
            color = True
        else:
            color = sys.stdout.isatty() or _git_bash_terminal()
    if color:
        _enable_windows_ansi()
    _color = color


def use_color() -> bool:
    return bool(_color)


def paint(text: str, *codes: str) -> str:
    if not use_color() or not codes:
        return text
    return f"\033[{';'.join(codes)}m{text}\033[0m"


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

def banner(language: str = "medumba", hint: bool = True) -> str:
    """Big Medu banner, shown at the start of every run (hide it with -q).
    hint=True adds the line for the interactive prompt."""
    name = LANGUAGE_NAMES.get(language, language.title())
    logo = "\n".join(paint(line, INDIGO, BOLD) for line in LOGO.strip("\n").split("\n"))
    tag = (paint(" :: Medu :: ", OCHRE, BOLD)
           + paint(f"  v{__version__}", BOLD)
           + paint(f"   {name} → English", DIM))
    credit = paint(f" {__company__} · {__authors__}", DIM)
    text = f"{logo}\n{tag}\n{credit}\n"
    if hint:
        text += paint("  Type a sentence. Commands: help, cls, version, exit", DIM) + "\n"
    return text


REPO = "https://github.com/fanyicharllson/medu"


def version_text() -> str:
    """medu -v / medu --version"""
    return (paint("Medu", INDIGO, BOLD) + f" {__version__}\n"
            + paint(f"{__company__} · {__authors__}\n{REPO}", DIM))


def help_text(prompt_mode: bool = False) -> str:
    """medu --help, and 'help' inside the medu> prompt."""
    h = lambda s: paint(s, OCHRE, BOLD)      # noqa: E731  section titles
    c = lambda s: paint(s, INDIGO, BOLD)     # noqa: E731  commands
    lines = []
    if prompt_mode:
        lines += [h("Inside medu>"),
                  f"  {c('<a sentence>')}   translate it, e.g.  mə kə̀ jʉ",
                  f"  {c('help')}           this help",
                  f"  {c('cls')} / {c('clear')}    clear the screen",
                  f"  {c('version')}        Medu version",
                  f"  {c('exit')}           leave Medu", ""]
    lines += [h("From a terminal")]
    for cmd, what in [("medu", "interactive prompt (medu>)"),
                      ("medu translate file.mdt", "translate Medumba sentences"),
                      ("medu run file.med", "run a Medu program"),
                      ("medu -v, --version", "version"),
                      ("medu -h, --help", "this help"),
                      ("-q", "hide the banner, e.g. medu -q translate file.mdt")]:
        lines.append(f"  {c(cmd.ljust(25))} {what}")
    lines += ["",
              h("Sentence pattern"),
              "  who + [kə̀ not | fə̀ past | àʼ will | nɛ̌n -ing | nùm always] + verb + [thing] + [ki ?]",
              "  mə zi = I slept · mə kə̀ jʉ = I did not eat · a yən mbʉ ki = Did he/she see the dog?", "",
              h("Words to start with"),
              "  mə I · a he/she · bo they · zi sleep · jʉ eat · nu drink · yən see · fɑ give",
              "  mbʉ dog · bùsi cat · ntsə water · mɛn child · mɛ̀nnzwi woman", "",
              h("No special letters on your keyboard?"),
              "  Type plain letters (me nen zi), or shortcuts: e* ə · e+ ɛ · u* ʉ · a* ɑ · o+ ɔ · n* ŋ", "",
              h("Help and contact"),
              f"  Guide and examples: {REPO}",
              f"  Report a problem:   {REPO}/issues",
              f"  {__company__} · {__authors__}"]
    return "\n".join(lines)


def clear_screen() -> None:
    """cls / clear inside the prompt."""
    if os.name == "nt" and not os.environ.get("TERM", "").startswith("xterm"):
        os.system("cls")
    else:
        print("\033[2J\033[3J\033[H", end="", flush=True)


def header(language: str, command: str) -> str:
    """One-line header for `medu run` / `medu translate`."""
    name = LANGUAGE_NAMES.get(language, language.title())
    return (paint("Medu", INDIGO, BOLD) + paint(f" v{__version__}", DIM)
            + paint(f" · {command} · {name}", DIM))


def section(title: str) -> str:
    """── English version ──────────"""
    return paint(f"── {title} " + "─" * max(4, 34 - len(title)), DIM)


def result(text: str) -> str:
    """The answer the user is waiting for: program output or English."""
    return paint(text, GREEN, BOLD)


def note(text: str) -> str:
    """Extra information, e.g. "(read as: mə nɛ̌n zi)"."""
    return paint(f"  {text}", DIM)


def ms(seconds: float) -> str:
    """0.0042 -> '4.2 ms', 1.5 -> '1.50 s'."""
    return f"{seconds * 1000:.1f} ms" if seconds < 1 else f"{seconds:.2f} s"


def timing(text: str) -> str:
    """Spring Boot-style timing line:  ✓ Translated 13 sentences in 4.2 ms"""
    return paint("✓ ", GREEN) + paint(text, DIM)


def prompt() -> str:
    return paint("medu", INDIGO, BOLD) + paint("> ", OCHRE, BOLD)


def error(err: MeduError, filename: str = "<input>", source: str = "") -> str:
    """A MeduError, coloured when the terminal allows it."""
    return err.format(filename, source, color=use_color())


# ---------------------------------------------------------------------------
# Preview:  python -m medu.ui
# ---------------------------------------------------------------------------

def _preview() -> None:
    setup()
    print(banner("medumba"))
    print(prompt() + "me nen zi")
    print(result("I am sleeping."))
    print(note("(read as: mə nɛ̌n zi)"))
    print()
    print(header("medumba", "run") + "\n")
    print(section("English version"))
    print('lɛn = "Emperor"\nprint(lɛn)\n')
    print(section("Output"))
    print(result("Emperor") + "\n")
    err = MeduError("E101", "unknown word 'zii'", 1, 8,
                    hint="did you mean 'zi' (sleep)?")
    print(error(err, "story.mdt", "mə nɛ̌n zii."))


if __name__ == "__main__":
    _preview()
