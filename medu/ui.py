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
    name = user_name()
    if name and hint:
        text += paint(f"\n  Welcome, {name}!", GREEN, BOLD) + "\n"
    if hint:
        text += paint("  Type a sentence. Commands: help, cls, version, exit", DIM) + "\n"
    return text


REPO = "https://github.com/fanyicharllson/medu"

# Logo gradient, top to bottom: light indigo -> deep indigo
LOGO_SHADES = ["38;5;117", "38;5;111", "38;5;105", "38;5;99", "38;5;63"]
FRAME = "38;5;60"


def visible_len(text: str) -> int:
    """Width on screen: no colour codes, tone marks take no space."""
    import re
    import unicodedata
    plain = re.sub(r"\033\[[0-9;]*m", "", text)
    return sum(1 for ch in plain if unicodedata.category(ch) != "Mn")


def welcome(language: str = "medumba", words: int = 0, load_seconds: float = 0.0) -> str:
    """The premium start screen of the interactive prompt: a framed card with
    the logo, version, authors, examples to try and the main commands."""
    width = 66
    name = LANGUAGE_NAMES.get(language, language.title())

    def row(content: str = "", align: str = "left") -> str:
        gap = width - visible_len(content)
        if align == "center":
            left = gap // 2
            content = " " * left + content + " " * (gap - left)
        else:
            content = content + " " * max(gap, 0)
        return paint("│", FRAME) + content + paint("│", FRAME)

    def rule(label: str = "") -> str:
        if not label:
            return paint("├" + "─" * width + "┤", FRAME)
        text = f" {label} "
        return (paint("├──", FRAME) + paint(text, OCHRE, BOLD)
                + paint("─" * (width - 2 - len(text)) + "┤", FRAME))

    lines = [paint("╭" + "─" * width + "╮", FRAME), row()]
    for shade, art in zip(LOGO_SHADES, LOGO.strip("\n").split("\n")):
        lines.append(row(paint(art, shade, BOLD), "center"))
    lines += [row(),
              row(paint("Medu ", BOLD) + paint(f"v{__version__}", OCHRE, BOLD)
                  + paint("  ·  ", DIM) + f"{name} → English", "center"),
              row(paint("the first compiler for the Medumba language", DIM), "center"),
              row()]
    user = user_name()
    if user:
        lines += [row(paint(f"Welcome back, {user}!", GREEN, BOLD), "center"), row()]
    lines.append(rule("Try"))
    for medumba, english in (("mə nɛ̌n zi", "I am sleeping."),
                             ("mə kə̀ jʉ", "I did not eat."),
                             ("a yən mbʉ ki", "Did he/she see the dog?")):
        lines.append(row("   " + paint(medumba.ljust(14 + len(medumba) - visible_len(medumba)),
                                       OCHRE, BOLD)
                         + paint("→  ", DIM) + paint(english, GREEN)))
    lines.append(rule("Commands"))
    cmds = [("help", "guide"), ("cls", "clear"), ("version", "about"), ("exit", "quit")]
    lines.append(row("   " + "   ".join(paint(c, INDIGO, BOLD) + paint(f" {d}", DIM)
                                         for c, d in cmds)))
    lines.append(rule("Made by"))
    lines.append(row("   " + paint(__company__, OCHRE, BOLD) + paint("  ·  ", DIM) + __authors__))
    lines.append(row("   " + paint(REPO.replace("https://", ""), DIM)))
    lines.append(paint("╰" + "─" * width + "╯", FRAME))
    status = (paint("  ● ", GREEN) + paint("offline ready", DIM)
              + paint("   ● ", INDIGO) + paint(f"{words:,} words", DIM)
              + paint("   ● ", OCHRE) + paint(f"started in {ms(load_seconds)}", DIM))
    return "\n".join(lines) + "\n" + status + "\n"


def config_path():
    """%APPDATA%\\Medu\\config.json, written by the installer's 'About you' page."""
    from pathlib import Path
    base = os.environ.get("MEDU_CONFIG_DIR") or os.path.join(
        os.environ.get("APPDATA", os.path.expanduser("~")), "Medu")
    return Path(base) / "config.json"


def user_name() -> str:
    """The name given in the installer, or '' (works offline, nothing is sent)."""
    import json
    try:
        data = json.loads(config_path().read_text(encoding="utf-8-sig"))
        return str(data.get("name", "")).strip()[:40]
    except (OSError, ValueError, AttributeError):
        return ""


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
                      ("medu run file.med", "run a Medu program (Medu 2.0)"),
                      ("medu check file", "only look for mistakes"),
                      ("medu upgrade", "install the newest version from GitHub"),
                      ("medu downgrade 1.0.0", "go back to an older version"),
                      ("medu -v, --version", "version"),
                      ("medu -h, --help", "this help"),
                      ("medu commands", "every command and what it does"),
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


def label(name: str) -> str:
    """Fixed-width tag in front of a line: 'Medumba ', 'English '."""
    return paint(f"{name:<8}", OCHRE, BOLD)


def note(text: str) -> str:
    """Extra information, e.g. "(read as: mə nɛ̌n zi)"."""
    return paint(f"  {text}", DIM)


def ms(seconds: float) -> str:
    """0.0042 -> '4.2 ms', 1.5 -> '1.50 s'."""
    return f"{seconds * 1000:.1f} ms" if seconds < 1 else f"{seconds:.2f} s"


def timing(text: str) -> str:
    """Spring Boot-style timing line:  ▸ Translated 13 sentences in 4.2 ms"""
    return paint("▸ ", GREEN) + paint(text, DIM)


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
