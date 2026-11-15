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

    def format(self, filename: str = "<input>", source: str = "") -> str:
        """Readable message with the line and a ^ under the problem:

        error[E101]: unknown word 'zii'
         --> story.mdt:1:4
          |
        1 | mə zii.
          |    ^
          = help: did you mean 'zi' (sleep)?
        """
        kind = "warning" if self.code.startswith("W") else "error"
        out = [f"{kind}[{self.code}]: {self.message}"]
        if self.line:
            out.append(f" --> {filename}:{self.line}:{self.col}")
            lines = source.splitlines()
            if 0 < self.line <= len(lines):
                num = str(self.line)
                pad = " " * len(num)
                out += [f"{pad} |",
                        f"{num} | {lines[self.line - 1]}",
                        f"{pad} | {' ' * max(self.col - 1, 0)}^"]
        if self.hint:
            out.append(f"  = help: {self.hint}")
        return "\n".join(out)
