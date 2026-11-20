"""
Errors: one shared way to report a problem, for every station.

Owner: Charllson (shared contract - ask before changing).

Every station raises MeduError instead of printing or exiting.
cli.py catches it and prints error.format(...).

Error codes:
    E0xx  cleaner        characters Medumba doesn't use
    E1xx  word cutter    E101 unknown word
    E2xx  parsers        E201 syntax error (expected X, found Y)
    E3xx  checkers       E301 variable has no value, E302 text mixed with number
    E4xx  run time       E401 division by zero
    Wxxx  warnings       W301 sentence pattern not recognised
"""

from __future__ import annotations


class MeduError(Exception):
    def __init__(self, code: str, message: str, line: int = 0, col: int = 0,
                 hint: str | None = None) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.line = line
        self.col = col
        self.hint = hint

    def format(self, filename: str = "<input>", source: str = "",
               color: bool = False) -> str:
        """Readable message with the line and a ^ under the problem:

        error[E101]: unknown word 'zii'
         --> story.mdt:1:4
          |
        1 | mə zii.
          |    ^
          = help: did you mean 'zi' (sleep)?

        color=True adds terminal colours (used by medu.ui.error).
        """
        def paint(text: str, code: str) -> str:
            return f"\033[{code}m{text}\033[0m" if color else text

        warning = self.code.startswith("W")
        kind_color = "1;38;5;172" if warning else "1;38;5;203"
        kind = "warning" if warning else "error"
        out = [paint(f"{kind}[{self.code}]", kind_color) + paint(f": {self.message}", "1")]
        if self.line:
            out.append(paint(" --> ", "38;5;69") + f"{filename}:{self.line}:{self.col}")
            lines = source.splitlines()
            if 0 < self.line <= len(lines):
                num = str(self.line)
                pad = " " * len(num)
                bar = paint(" |", "38;5;69")
                out += [f"{pad}{bar}",
                        paint(num, "38;5;69") + f"{bar} {lines[self.line - 1]}",
                        f"{pad}{bar} {' ' * max(self.col - 1, 0)}" + paint("^", kind_color)]
        if self.hint:
            out.append(paint("  = help: ", "1;38;5;71") + self.hint)
        return "\n".join(out)
