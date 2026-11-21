"""
Languages: loads everything that belongs to one language.

Owner: Charllson (shared contract - ask before changing).

This is what makes Medu a dual compiler. Each language has a folder:

    data/languages/medumba/lexicon.json    dictionary
    data/languages/medumba/keywords.json   Mode 1 keywords, e.g. {"PRINT": "dʉ"}
    data/languages/medumba/grammar.json    Mode 2 rules: pronouns, markers, tense
    data/languages/medumba/corrections.json  checked meanings (replace automatic ones)
    data/languages/bafut/...               same files, added later

Code never writes a Medumba word directly. It asks the Language object:
    lang = load("medumba")
    lang.keyword_for("PRINT")   -> "dʉ"
    lang.concept_for("dʉ")      -> "PRINT"
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Inside a PyInstaller .exe, data files are unpacked to sys._MEIPASS.
# The build must include them: --add-data "data/languages;data/languages"
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
LANG_DIR = ROOT / "data" / "languages"

# File extensions -> (language, mode). Bafut gets its own later.
EXTENSIONS = {
    ".med": ("medumba", 1),   # Mode 1: programs
    ".mdt": ("medumba", 2),   # Mode 2: sentences
}


@dataclass
class Language:
    name: str
    entries: list[dict] = field(default_factory=list)   # lexicon entries
    keywords: dict[str, str] = field(default_factory=dict)  # concept -> word
    grammar: dict = field(default_factory=dict)              # Mode 2 rules

    def keyword_for(self, concept: str) -> str:
        return self.keywords[concept]

    def concept_for(self, word: str) -> str | None:
        for concept, kw in self.keywords.items():
            if kw == word:
                return concept
        return None


def available() -> list[str]:
    return sorted(p.name for p in LANG_DIR.iterdir()
                  if (p / "lexicon.json").exists())


def load(name: str) -> Language:
    folder = LANG_DIR / name
    lexicon = folder / "lexicon.json"
    if not lexicon.exists():
        raise FileNotFoundError(f"no lexicon for language '{name}' in {folder}")
    entries = json.loads(lexicon.read_text(encoding="utf-8"))["entries"]
    kw_file = folder / "keywords.json"
    keywords = {}
    if kw_file.exists():
        keywords = {k: v for k, v in
                    json.loads(kw_file.read_text(encoding="utf-8")).items()
                    if not k.startswith("_")}
    grammar = _read_json(folder / "grammar.json")
    _apply_corrections(entries, _read_json(folder / "corrections.json"))
    return Language(name=name, entries=entries, keywords=keywords, grammar=grammar)


def _apply_corrections(entries: list[dict], corrections: dict) -> None:
    """Checked meanings (corrections.json) replace automatic ones."""
    for e in entries:
        fix = corrections.get(e["medumba"])
        if fix and fix.get("pos", e["pos"]) == e["pos"]:
            e["gloss_en"] = [fix["en"]]
            e["gloss_en_auto"] = []
            e.setdefault("sources", []).append("corrections.json")


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return {k: v for k, v in json.loads(path.read_text(encoding="utf-8")).items()
            if not k.startswith("_")}
