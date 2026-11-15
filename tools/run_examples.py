"""
Runs every example in tests/examples/ and prints PASS or FAIL.

    python tools/run_examples.py            all examples
    python tools/run_examples.py mode1      only one folder

A test passes when every line of its .expected file appears in Medu's output.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "tests" / "examples"
COMMANDS = {".med": "run", ".mdt": "translate"}


def run_one(src: Path) -> tuple[bool, str]:
    expected_file = src.with_suffix(".expected")
    if not expected_file.exists():
        return False, "missing .expected file"
    proc = subprocess.run(
        [sys.executable, "-m", "medu", COMMANDS[src.suffix], str(src)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    output = proc.stdout + proc.stderr
    missing = [line for line in expected_file.read_text(encoding="utf-8").splitlines()
               if line.strip() and line.strip() not in output]
    if missing:
        return False, f"expected: {missing[0]!r}\n         got: {output.strip()[:200]!r}"
    return True, ""


def main() -> int:
    folders = sys.argv[1:] or ["mode1", "mode2"]
    passed = total = 0
    for folder in folders:
        for src in sorted((EXAMPLES / folder).glob("*")):
            if src.suffix not in COMMANDS:
                continue
            total += 1
            ok, why = run_one(src)
            passed += ok
            print(f"{'PASS' if ok else 'FAIL'}  {folder}/{src.name}")
            if why:
                print(f"         {why}")
    print(f"\n{passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
