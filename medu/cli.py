"""
The medu command

Owner: Adrien
Takes: Command-line arguments
Gives: Printed results or formatted errors

What it must do:
    medu run file.med | medu translate file.mdt | medu check file | medu
    Picks language and mode from languages.EXTENSIONS. Catches MeduError
    and prints error.format(filename, source). Never shows a Python traceback.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    print("medu: not implemented yet")
    return 1
