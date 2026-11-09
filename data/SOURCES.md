# Where the Medumba words come from

`tools/build_lexicon.py` builds `medumba_lexicon.json` / `.csv` from these open sources.
All of them allow reuse; because two are GPL-3.0, the Medu compiler is released under GPL-3.0 too.

| Source | What we take | Licence |
|---|---|---|
| [apertium/apertium-byv](https://github.com/apertium/apertium-byv) (Ngadou Sylvestre, Francis M. Tyers, 2016) | Medumba words, word class, noun classes, grammar particles (negation, tense, questions), some French glosses | GPL-3.0 |
| [apertium/apertium-byv-fra](https://github.com/apertium/apertium-byv-fra) | Medumba ↔ French bilingual dictionary | GPL-3.0 |
| apertium-byv `dev/` word lists | Words with English glosses (official CEPOM spelling only) | GPL-3.0 |
| [FreeDict fra-eng 0.4.1](https://freedict.org) | French → English, used to *suggest* English meanings | GPL |

## Spelling

Every word goes through `normalize()`:
- Unicode NFC, so the same letter with the same tone mark is always stored the same way
- Greek `α` is changed to the Medumba letter `ɑ` (they look identical but are different characters)
- `'`, `’`, `‘` and `ʔ` are changed to `ʼ` (the glottal-stop letter)

`plain` is the same word without tone marks, so users can type without accents.

## Accuracy notes

- `english_auto` meanings are machine-suggested from the French. **A speaker must review them.**
- Webonary's *Mambəlemα* dictionary is a different variety of Medumba from the one spoken in Bangangté.
  For example, "eat" is `jʉ` in Apertium and `di` in Mambəlemα, and "sleep" is `zi` versus `le`.
  Apertium's `zi` is confirmed by field recordings ("mə nɛn zi", "I am sleeping"). Check words
  with a Bangangté speaker, not against Mambəlemα.
- Copyrighted Bible excerpts in the Apertium repos are **not** used.
