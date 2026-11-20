# Working on Medu

Full plan: [docs/Medu_Team_Plan.pdf](docs/Medu_Team_Plan.pdf)

## Who owns which file

Only edit your own files. If you need a change in someone else's file, open an issue or ask.

| Owner | Files |
|---|---|
| **Charllson** (lead architect) | `medu/tokens.py`, `errors.py`, `languages.py` (shared contracts), `cleaner.py`, `lexer.py`, `parser_text.py`, `checker_text.py`, `meaning.py`, `english.py`, `data/`, `tools/build_lexicon.py` |
| **Adrien** (second lead developer) | `medu/parser_code.py`, `checker_code.py`, `interpreter.py`, `cli.py`, `tests/test_mode1.py` |
| **Joy, Rydell** (testers) | `tests/examples/` |

Each file starts with a comment saying what it takes, what it gives and what it must do.

## Set up (once)

Python 3.10 or newer. From the `medu` folder:

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt
python -m pytest                  # should say: 5 passed
```

Activate the environment (`.venv\Scripts\activate`) every time you open a new terminal.

## Branches

```bash
git checkout -b adrien/mode1      # or charllson/front, tests/joy, tests/rydell
git push -u origin adrien/mode1
```

Nobody pushes to `main`. Open a pull request; Charllson reviews and merges it.

## Terminal output (banner, colours)

Everything the user sees goes through `medu/ui.py`, so Medu always looks the same.
Preview it with `python -m medu.ui`.

```python
from medu import ui
ui.setup()                           # first line of main(): UTF-8 + colours
print(ui.banner("medumba"))          # interactive prompt and `medu --version`
print(ui.header("medumba", "run"))   # one line at the top of `medu run` / `translate`
print(ui.section("Output"))          # ── Output ──────
print(ui.result("Emperor"))          # the answer, in green
print(ui.error(err, path, clean(source, code=True)))   # any MeduError
```

Colours switch off by themselves when output goes to a file or `NO_COLOR` is set.

## Before opening a pull request

```bash
python -m pytest                 # unit tests
python tools/run_examples.py     # example files
```

- No Medumba word written in Python code: use `languages.load("medumba")`
- Python 3.10+, standard library only (pytest for tests)
- Errors are raised as `MeduError`, never printed directly
