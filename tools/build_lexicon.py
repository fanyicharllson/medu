"""
Build the Medumba lexicon for the Medu compiler.

Downloads open-licensed Medumba data, cleans the spelling, merges everything
into one dictionary and writes:

    data/medumba_lexicon.json   - full entries (used by the compiler)
    data/medumba_lexicon.csv    - same data, for opening in Excel / Sheets
    data/stats.txt              - counts per source and word class

Sources (all openly licensed, see data/SOURCES.md):
  1. apertium-byv      Medumba morphological lexicon (GPL-3.0)
                       -> words, word class, noun classes, some French glosses
  2. apertium-byv-fra  Medumba <-> French bilingual dictionary (GPL-3.0)
                       -> French meanings
  3. apertium-byv dev  word lists with English glosses (GPL-3.0)
  4. FreeDict fra-eng  French -> English dictionary (GPL)
                       -> used to suggest English meanings from French ones
                          (marked "auto", to be reviewed by a speaker)

Usage (Python 3.10+, no extra packages needed):
    python tools/build_lexicon.py            # uses cached downloads
    python tools/build_lexicon.py --refresh  # re-download everything
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import tarfile
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"

APERTIUM_BYV = "https://raw.githubusercontent.com/apertium/apertium-byv/master"
APERTIUM_BYV_FRA = "https://raw.githubusercontent.com/apertium/apertium-byv-fra/master"

SOURCES = {
    "byv.lexc": f"{APERTIUM_BYV}/apertium-byv.byv.lexc",
    "byv-fra.dix": f"{APERTIUM_BYV_FRA}/apertium-byv-fra.byv-fra.dix",
    "byv-words-en.tsv": f"{APERTIUM_BYV}/dev/AnnaBelewWords.tsv",
    "fra-byv-eng.txt": f"{APERTIUM_BYV}/dev/random.fra-byv-eng.txt",
    "corpus-byv.txt": f"{APERTIUM_BYV}/texts/corpus-byv.txt",
    "freedict-fra-eng.tar.xz": (
        "https://download.freedict.org/dictionaries/fra-eng/0.4.1/"
        "freedict-fra-eng-0.4.1.src.tar.xz"
    ),
}

USER_AGENT = "medu-lexicon-builder/0.1 (student compiler project)"


# --------------------------------------------------------------------------
# Spelling normalisation
# --------------------------------------------------------------------------

# Characters that look the same as Medumba letters but are different code
# points. Sources mix them, so we map everything onto the standard letters.
_LOOKALIKES = {
    "α": "ɑ",  # Greek alpha  α -> Latin alpha ɑ
    "Α": "Ɑ",  # Greek Alpha  Α -> Latin Alpha Ɑ
    "'": "ʼ",       # ASCII apostrophe -> modifier letter apostrophe ʼ
    "’": "ʼ",  # right single quote ’ -> ʼ
    "‘": "ʼ",  # left single quote ‘ -> ʼ
    "ʔ": "ʼ",  # glottal stop ʔ -> ʼ (orthography writes ʼ)
}


def normalize(text: str) -> str:
    """Canonical Medumba spelling: NFC, standard letters, single spaces."""
    text = unicodedata.normalize("NFD", text.strip())
    text = "".join(_LOOKALIKES.get(ch, ch) for ch in text)
    text = unicodedata.normalize("NFC", text)
    return re.sub(r"\s+", " ", text)


def strip_tones(text: str) -> str:
    """Same word without tone marks - lets users type without accents."""
    decomposed = unicodedata.normalize("NFD", text)
    bare = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", bare).lower()


# --------------------------------------------------------------------------
# Downloads
# --------------------------------------------------------------------------

def fetch(name: str, refresh: bool) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    target = RAW / name
    if target.exists() and not refresh:
        return target
    url = SOURCES[name]
    print(f"  downloading {name} ...", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        target.write_bytes(resp.read())
    return target


# --------------------------------------------------------------------------
# Entry store
# --------------------------------------------------------------------------

class Lexicon:
    def __init__(self) -> None:
        self.entries: dict[tuple[str, str], dict] = {}

    def add(self, word: str, pos: str, source: str, *, gloss_fr=(),
            gloss_en=(), noun_class: str | None = None,
            en_auto: bool = False, tags=()) -> None:
        word = normalize(word.replace(">", " "))
        # drop a stray tone mark left at the very start by the source markup
        while word and unicodedata.category(word[0]) == "Mn":
            word = word[1:]
        if not word or word.startswith(("%", "+")):
            return
        key = (word, pos)
        e = self.entries.setdefault(key, {
            "medumba": word,
            "plain": strip_tones(word),
            "pos": pos,
            "noun_class": None,
            "gloss_fr": [],
            "gloss_en": [],
            "gloss_en_auto": [],
            "tags": [],
            "sources": [],
        })
        if noun_class and not e["noun_class"]:
            e["noun_class"] = noun_class
        for t in tags:
            if t not in e["tags"]:
                e["tags"].append(t)
        for g in gloss_fr:
            g = g.strip()
            if g and g not in e["gloss_fr"]:
                e["gloss_fr"].append(g)
        bucket = "gloss_en_auto" if en_auto else "gloss_en"
        for g in gloss_en:
            g = g.strip()
            if g and g not in e[bucket]:
                e[bucket].append(g)
        if source not in e["sources"]:
            e["sources"].append(source)


# --------------------------------------------------------------------------
# Parsers
# --------------------------------------------------------------------------

# lexc section name -> word class
LEXC_SECTIONS = {
    "Noms": "n", "ProperNouns": "np", "Adjectifs": "adj", "Adverbes": "adv",
    "Verbes": "v", "Pronoms": "prn", "Conjonctions": "cnj",
    "Prepositions": "pr", "Determiners": "det", "Nombres": "num",
    "Interjections": "ij", "Miscellaneous": "misc",
}

# Tags that mark grammatical particles (tense, negation, focus, questions...)
GRAMMAR_TAGS = {"neg", "past", "fut", "prog", "foc", "qst", "cop", "hab",
                "dur", "consec", "impf", "pres", "itg", "rel"}

LEXC_LINE = re.compile(
    r"""^\s*(?P<upper>[^!\s:][^:]*?)       # surface form (what people write)
        :(?P<lower>\S+)\s+                  # underlying form (ignored)
        (?P<cont>[^\s;]+)\s*;               # continuation class, e.g. N-1-6
        \s*(?:!\s*"?(?P<gloss>[^"]*)"?)?    # optional French gloss comment
    """,
    re.VERBOSE,
)


def parse_lexc(path: Path, lex: Lexicon) -> int:
    section = None
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("LEXICON "):
            section = LEXC_SECTIONS.get(line.split()[1])
            continue
        if not section:
            continue
        m = LEXC_LINE.match(line)
        if not m:
            continue
        upper = m["upper"].replace("%", "").strip()
        # Grammar markers carry tags like <neg>, <past>, <qst>: keep the tags,
        # they tell the parser what the particle does.
        tags = re.findall(r"<([^>]+)>", upper)
        upper = re.sub(r"<[^>]+>", "", upper).replace(">", " ").strip()
        if not upper or upper == "0":
            continue
        pos = section
        if "prn" in tags:
            pos = "prn"
        elif "det" in tags:
            pos = "det"
        elif any(t in GRAMMAR_TAGS for t in tags):
            pos = "part"
        noun_class = None
        nc = re.match(r"N-(\d|X)(?:-(\d|X))?$", m["cont"])
        if nc:
            noun_class = "/".join(c for c in nc.groups() if c)
        gloss = [g.strip() for g in (m["gloss"] or "").split(",") if g.strip()]
        lex.add(upper, pos, "apertium-byv", gloss_fr=gloss,
                noun_class=noun_class, tags=tags)
        count += 1
    return count


DIX_POS = {
    "v": "v", "vblex": "v", "n": "n", "np": "np", "adj": "adj", "adv": "adv",
    "pr": "pr", "prn": "prn", "det": "det", "num": "num", "ij": "ij",
    "cnjcoo": "cnj", "cnjsub": "cnj", "cnjadv": "cnj",
}


def _side_text(el: ET.Element) -> str:
    """Text of an <l>/<r> side: <b/> is a space, <s> tags are dropped."""
    parts = [el.text or ""]
    for child in el:
        if child.tag == "b":
            parts.append(" ")
        elif child.tag == "g":
            parts.append(_side_text(child))
        parts.append(child.tail or "")
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def parse_dix(path: Path, lex: Lexicon) -> int:
    root = ET.parse(path).getroot()
    count = 0
    for e in root.iter("e"):
        p = e.find("p")
        if p is None:
            continue
        left, right = p.find("l"), p.find("r")
        if left is None or right is None:
            continue
        tags = [s.get("n") for s in left.iter("s")]
        pos = next((DIX_POS[t] for t in tags if t in DIX_POS), "misc")
        word, fr = _side_text(left), _side_text(right)
        if word and fr:
            lex.add(word, pos, "apertium-byv-fra", gloss_fr=[fr])
            count += 1
    return count


def parse_words_en(path: Path, lex: Lexicon) -> int:
    """Field-linguistics word list. Only rows with a CEPOM (official)
    spelling are used; IPA-only rows would not match how people write."""
    count = 0
    rows = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8")),
                          delimiter="\t")
    pos_map = {"noun": "n", "verb": "v", "adjective": "adj", "adverb": "adv",
               "pronoun": "prn", "preposition": "pr"}
    for row in rows:
        word = (row.get("CEPOM Orthography") or "").strip()
        gloss = (row.get("Gloss") or "").strip()
        if not word or not gloss:
            continue
        cat = (row.get("Grammatical Cat") or "").strip().lower()
        pos = pos_map.get(cat, "misc")
        lex.add(word, pos, "apertium-byv/dev", gloss_en=[gloss])
        count += 1
    return count


def parse_trilingual(path: Path, lex: Lexicon) -> int:
    """Lines of the form: french | medumba | english"""
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3 or not all(parts):
            continue
        fr, word, en = parts
        en = re.sub(r"^(a|an|the)\s+", "", en)
        lex.add(word, "n", "apertium-byv/dev", gloss_fr=[fr], gloss_en=[en])
        count += 1
    return count


# --------------------------------------------------------------------------
# French -> English (FreeDict)
# --------------------------------------------------------------------------

TEI = "{http://www.tei-c.org/ns/1.0}"


def load_freedict(path: Path) -> dict[str, list[str]]:
    with tarfile.open(path, "r:xz") as tar:
        member = next(m for m in tar.getmembers() if m.name.endswith(".tei"))
        xml_bytes = tar.extractfile(member).read()
    root = ET.fromstring(xml_bytes)
    fr_en: dict[str, list[str]] = defaultdict(list)
    for entry in root.iter(f"{TEI}entry"):
        orth = entry.find(f"{TEI}form/{TEI}orth")
        if orth is None or not orth.text:
            continue
        head = orth.text.strip().lower()
        for q in entry.iter(f"{TEI}quote"):
            if q.text and q.text.strip() not in fr_en[head]:
                fr_en[head].append(q.text.strip())
    return fr_en


def _fr_keys(gloss: str) -> list[str]:
    g = re.sub(r"\(.*?\)", "", gloss).strip().lower()
    keys = [g]
    for prefix in ("se ", "s'", "s’"):
        if g.startswith(prefix):
            keys.append(g[len(prefix):].strip())
    keys.append(g.replace("é", "e").replace("è", "e"))
    return keys


def add_auto_english(lex: Lexicon, fr_en: dict[str, list[str]]) -> int:
    filled = 0
    for e in lex.entries.values():
        if e["gloss_en"] or not e["gloss_fr"]:
            continue
        found: list[str] = []
        for fr in e["gloss_fr"]:
            for key in _fr_keys(fr):
                if key in fr_en:
                    found.extend(fr_en[key][:2])
                    break
        if found:
            if e["pos"] == "v":
                found = [f if f.startswith("to ") else f"to {f}" for f in found]
            e["gloss_en_auto"] = list(dict.fromkeys(found))[:3]
            filled += 1
    return filled


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def write_outputs(lex: Lexicon, per_source: dict[str, int], auto: int) -> None:
    entries = sorted(lex.entries.values(), key=lambda e: (e["plain"], e["pos"]))
    payload = {
        "language": "Medumba (byv)",
        "generated": date.today().isoformat(),
        "licence": "GPL-3.0 (derived from Apertium and FreeDict data)",
        "entries": entries,
    }
    (DATA / "medumba_lexicon.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    with (DATA / "medumba_lexicon.csv").open("w", encoding="utf-8-sig",
                                             newline="") as f:
        w = csv.writer(f)
        w.writerow(["medumba", "plain", "pos", "noun_class", "grammar_tags",
                    "french", "english", "english_auto (review!)", "sources"])
        for e in entries:
            w.writerow([e["medumba"], e["plain"], e["pos"], e["noun_class"] or "",
                        " ".join(e["tags"]),
                        "; ".join(e["gloss_fr"]), "; ".join(e["gloss_en"]),
                        "; ".join(e["gloss_en_auto"]), ", ".join(e["sources"])])

    pos_counts = Counter(e["pos"] for e in entries)
    with_fr = sum(1 for e in entries if e["gloss_fr"])
    with_en = sum(1 for e in entries if e["gloss_en"])
    with_any_en = sum(1 for e in entries if e["gloss_en"] or e["gloss_en_auto"])
    no_meaning = sum(1 for e in entries
                     if not (e["gloss_fr"] or e["gloss_en"] or e["gloss_en_auto"]))
    lines = [
        f"Medumba lexicon - built {date.today().isoformat()}",
        "",
        f"Unique entries (word + word class): {len(entries)}",
        f"  with a French meaning:              {with_fr}",
        f"  with a checked English meaning:     {with_en}",
        f"  with an auto English meaning:       {auto}",
        f"  with any English meaning:           {with_any_en}",
        f"  with no meaning yet:                {no_meaning}",
        "",
        "Rows read per source:",
        *[f"  {k:<28}{v}" for k, v in per_source.items()],
        "",
        "Entries per word class:",
        *[f"  {k:<6}{v}" for k, v in pos_counts.most_common()],
    ]
    (DATA / "stats.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--refresh", action="store_true",
                    help="download sources again even if cached")
    args = ap.parse_args()

    print("Fetching sources ...")
    paths = {name: fetch(name, args.refresh) for name in SOURCES}

    lex = Lexicon()
    per_source = {
        "apertium-byv (lexc)": parse_lexc(paths["byv.lexc"], lex),
        "apertium-byv-fra (dix)": parse_dix(paths["byv-fra.dix"], lex),
        "word list (English)": parse_words_en(paths["byv-words-en.tsv"], lex),
        "fra-byv-eng list": parse_trilingual(paths["fra-byv-eng.txt"], lex),
    }
    print("Suggesting English meanings from French (FreeDict) ...")
    auto = add_auto_english(lex, load_freedict(paths["freedict-fra-eng.tar.xz"]))
    print()
    write_outputs(lex, per_source, auto)
    print(f"\nWrote {DATA / 'medumba_lexicon.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
