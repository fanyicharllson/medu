"""
⑤ Meaning (IR)

Owner: Charllson
Takes: Checked sentence trees + the Language (for default tense)
Gives: list[SentenceMeaning], with no Medumba left in it

This is the language-free middle of Medu. A Bafut front end will build the
same objects, and ⑥ (English) never needs to know which language came in.

    "mə nɛ̌n zi"  ->  Action(who=Thing("I", person=1), verb="sleep",
                            time="present", aspect="progressive")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from medu.languages import Language
from medu.parser_text import Clause, NounPhrase, Sentence


@dataclass
class Word:
    en: str                 # English meaning
    sure: bool = True       # False = suggested automatically, not checked
    source: str = ""        # the Medumba word, for notes


@dataclass
class Thing:
    word: Word
    kind: str = "noun"      # pronoun | noun | name | number
    person: int = 3
    plural: bool = False
    obj_form: str = ""      # pronouns: "me", "him/her" ...
    describers: list[Word] = field(default_factory=list)   # adjectives


@dataclass
class Action:
    who: Thing | None
    verb: Word
    time: str = "past"          # past | present | future
    aspect: str = "simple"      # simple | progressive | habitual
    negative: bool = False
    things: list[Thing] = field(default_factory=list)      # objects
    extras: list[Word] = field(default_factory=list)       # adverbs


@dataclass
class SentenceMeaning:
    actions: list[Action]
    links: list[Word] = field(default_factory=list)        # and / then / but
    question: bool = False
    rough: list[Word] = field(default_factory=list)        # W301 word-by-word part


def word_of(entry: dict, medumba: str = "") -> Word:
    """English meaning of a dictionary entry, shortened for writing sentences."""
    for key, sure in (("gloss_en", True), ("gloss_en_auto", False)):
        if entry.get(key):
            text = entry[key][0]
            text = re.sub(r"\(.*?\)", "", text)
            text = re.split(r"[,;/]", text)[0].strip() or entry[key][0]
            if len(text) > 1 and text[0].isupper() and not text[1].isupper():
                text = text[0].lower() + text[1:]
            return Word(text, sure, medumba)
    if entry.get("gloss_fr"):
        return Word(f"[French: {entry['gloss_fr'][0]}]", False, medumba)
    return Word(f"[{medumba}]", False, medumba)


def _thing(np: NounPhrase) -> Thing:
    if np.kind == "pronoun":
        p = np.pronoun
        return Thing(Word(p["en"], True, np.token.text), "pronoun", p["person"],
                     p["number"] == "pl", p["obj"])
    w = word_of(np.entry, np.token.text)
    if np.kind == "name":
        w = Word(np.token.text, True, np.token.text)
    t = Thing(w, np.kind)
    t.describers = [word_of(e, tok.text) for tok, e in np.adjectives]
    return t


def _action(clause: Clause, default_tense: str) -> Action:
    roles = [role for role, _ in clause.markers]
    verb = word_of(clause.verb, clause.verb_token.text)
    verb.en = re.sub(r"^to\s+", "", verb.en)
    a = Action(_thing(clause.subject) if clause.subject else None, verb)
    a.negative = "negative" in roles
    if "future" in roles:
        a.time = "future"
    elif "past" in roles:
        a.time = "past"
    elif "progressive" in roles or "habitual" in roles:
        a.time = "present"
    elif clause.subject is None:
        a.time, a.aspect = "present", "order"      # zi. -> "Sleep."
    else:
        a.time = default_tense
    if "progressive" in roles:
        a.aspect = "progressive"
    elif "habitual" in roles:
        a.aspect = "habitual"
    a.things = [_thing(np) for np in clause.objects]
    a.extras = [word_of(e, tok.text) for tok, e in clause.adverbs]
    return a


def build(sentences: list[Sentence], lang: Language) -> list[SentenceMeaning]:
    default = lang.grammar.get("default_tense", "past")
    out = []
    for s in sentences:
        m = SentenceMeaning([_action(c, default) for c in s.clauses], question=s.question)
        for tok, entry in s.connectors:
            m.links.append(word_of(entry, tok.text) if entry else Word(",", True, tok.text))
        m.rough = [word_of(t.value[0], t.text) if t.value else Word(t.text, False, t.text)
                   for t in s.leftover]
        out.append(m)
    return out
