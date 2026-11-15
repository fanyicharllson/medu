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

## Before opening a pull request

```bash
python -m pytest                 # unit tests
python tools/run_examples.py     # example files
```

- No Medumba word written in Python code: use `languages.load("medumba")`
- Python 3.10+, standard library only (pytest for tests)
- Errors are raised as `MeduError`, never printed directly
