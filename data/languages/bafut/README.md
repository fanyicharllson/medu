# Bafut (later)

Placeholder for the dual compiler. When we add Bafut, this folder gets the same files as
`../medumba/`:

- `lexicon.json`: the Bafut dictionary (source: SIL's Bafut Dictionary, 6,152 entries, once permission is granted)
- `keywords.json`: the Mode 1 keywords in Bafut

No code changes are needed to add a language. `medu/languages.py` finds every folder that has a `lexicon.json`.
