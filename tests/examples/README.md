# Example tests (Joy and Rydell)

Each test is **two files with the same name**:

| File | What goes in it |
|---|---|
| `hello.med` (Mode 1) or `sleep.mdt` (Mode 2) | The Medumba the user types |
| `hello.expected` | What Medu must print. Every line here must appear in Medu's output |

- `mode1/`: programs (`.med`), run with `medu run`
- `mode2/`: sentences (`.mdt`), run with `medu translate`
- Name error tests with `e_` at the start, e.g. `e_paren.med`. Their `.expected` holds the error code, e.g. `error[E201]`.

## Run all tests

From the `medu` folder:

```bash
python tools/run_examples.py
```

Each test prints `PASS` or `FAIL`. For a `FAIL`, open a GitHub issue with:
the file name, what you expected, and what Medu printed.

Until Adrien and Charllson finish their parts, every test shows `FAIL`. That's normal.
