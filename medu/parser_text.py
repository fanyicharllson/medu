"""
③ Grammar check (Mode 2)

Owner: Charllson
Takes: list[Token] from lexer.tokenize_text + the Language (grammar.json)
Gives: list[Sentence] (the tree of each sentence)

Grammar (from Medumba fieldwork, see data/languages/medumba/grammar.json):

    sentence  := clause { connector clause } [ question-word ] [ . ? ! ]
    clause    := [ subject ] { marker } verb { object } { adverb }
    subject   := noun-phrase
    object    := noun-phrase
    noun-phrase := { adjective } ( pronoun | noun | name | number ) { adjective }
    marker    := not | past | future | -ing | always   (grammar words, before the verb)
    connector := and / then / but ...  (conjunctions in the dictionary)

One function per rule (recursive descent). Words with several meanings keep
all of them in the token; each rule picks the meaning that fits its place
(ki at the end = question word, ki elsewhere = key).

Errors:
    E201  a grammar word with no verb after it  (mə kə̀.)
    E202  a sentence with no verb               (mbʉ.)
    W301  words left over that no rule explains: Medu keeps going and
          gives a word-by-word translation for them (a warning, not an error)
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

from medu.cleaner import keyboard
from medu.errors import MeduError
from medu.languages import Language
from medu.tokens import EOF, PUNCT, WORD, Token

NOUNISH = {"n", "np", "num", "prn"}
END_PUNCT = {".", "?", "!"}
CLAUSE_PUNCT = {",", ";", ":"}


# ---------------------------------------------------------------------------
# The tree
# ---------------------------------------------------------------------------

@dataclass
class NounPhrase:
    token: Token
    entry: dict                    # the chosen dictionary meaning
    kind: str                      # pronoun | noun | name | number
    pronoun: dict | None = None    # from grammar.json when kind == pronoun
    adjectives: list[tuple[Token, dict]] = field(default_factory=list)


@dataclass
class Clause:
    subject: NounPhrase | None
    markers: list[tuple[str, Token]]          # ("negative", token), ("past", token) ...
    verb_token: Token
    verb: dict
    objects: list[NounPhrase] = field(default_factory=list)
    adverbs: list[tuple[Token, dict]] = field(default_factory=list)


@dataclass
class Sentence:
    clauses: list[Clause]
    connectors: list[tuple[Token, dict | None]] = field(default_factory=list)
    question: bool = False
    end: str = "."
    leftover: list[Token] = field(default_factory=list)   # W301 words
    line: int = 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rank(entry: dict) -> int:
    for rank, key in enumerate(("gloss_en", "gloss_en_auto", "gloss_fr")):
        if entry.get(key):
            return rank
    return 3


def _pick(token: Token, pos: set[str]) -> dict | None:
    """Best meaning of this word for the given word classes, or None."""
    found = [e for e in (token.value or []) if e.get("pos") in pos]
    return min(found, key=_rank) if found else None


def _pick_tag(token: Token, tags: set[str]) -> tuple[str, dict] | None:
    for e in token.value or []:
        for t in e.get("tags", []):
            if t in tags:
                return t, e
    return None


class _Parser:
    def __init__(self, tokens: list[Token], lang: Language) -> None:
        self.toks = [t for t in tokens if t.kind != EOF]
        self.i = 0
        g = lang.grammar
        self.pronouns = {keyboard(w): v for w, v in g.get("pronouns", {}).items()}
        self.pronouns_exact = g.get("pronouns", {})
        self.aux = {keyboard(w): v for w, v in g.get("aux_verbs", {}).items()}
        self.marker_tags = g.get("marker_tags", {})
        self.question_tag = g.get("question_tag", "qst")

    # -- token stream -------------------------------------------------------
    def peek(self, k: int = 0) -> Token | None:
        j = self.i + k
        return self.toks[j] if j < len(self.toks) else None

    def at_end_of_sentence(self, k: int = 0) -> bool:
        t = self.peek(k)
        return t is None or (t.kind == PUNCT and t.text in END_PUNCT)

    def is_word(self, k: int = 0) -> bool:
        t = self.peek(k)
        return t is not None and t.kind == WORD

    # -- classification -----------------------------------------------------
    def pronoun_info(self, t: Token) -> dict | None:
        return self.pronouns_exact.get(t.text) or self.pronouns.get(keyboard(t.text))

    def can_noun(self, t: Token) -> bool:
        return self.pronoun_info(t) is not None or _pick(t, NOUNISH) is not None

    def can_verb(self, t: Token) -> bool:
        return _pick(t, {"v"}) is not None

    def marker(self, k: int = 0) -> str | None:
        """Role of a grammar word before the verb ("negative", "past" ...)."""
        t = self.peek(k)
        if t is None or t.kind != WORD:
            return None
        hit = _pick_tag(t, set(self.marker_tags))
        if hit:
            return self.marker_tags[hit[0]]
        role = self.aux.get(keyboard(t.text))
        nxt = self.peek(k + 1)
        if role and nxt is not None and nxt.kind == WORD and self.can_verb(nxt):
            return self.marker_tags.get(role, role)
        return None

    def is_question_word(self, k: int = 0) -> bool:
        t = self.peek(k)
        return (t is not None and t.kind == WORD
                and _pick_tag(t, {self.question_tag}) is not None
                and self.at_end_of_sentence(k + 1))

    def is_connector(self, k: int = 0) -> bool:
        t = self.peek(k)
        if t is None:
            return False
        if t.kind == PUNCT and t.text in CLAUSE_PUNCT:
            return True
        return t.kind == WORD and _pick(t, {"cnj"}) is not None and self.clause_follows(k + 1)

    def clause_follows(self, k: int) -> bool:
        """Is there a verb before the end of the sentence, from position k?"""
        while not self.at_end_of_sentence(k):
            t = self.peek(k)
            if t.kind == WORD and self.can_verb(t):
                return True
            k += 1
        return False

    # -- grammar rules ------------------------------------------------------
    def sentence(self) -> Sentence:
        start = self.peek()
        clauses, connectors = [self.clause()], []
        while self.is_connector():
            t = self.peek()
            self.i += 1
            connectors.append((t, _pick(t, {"cnj"}) if t.kind == WORD else None))
            clauses.append(self.clause())
        s = Sentence(clauses, connectors, line=start.line if start else 1)
        if self.is_question_word():
            s.question = True
            self.i += 1
        while not self.at_end_of_sentence():          # W301: no rule for these
            s.leftover.append(self.peek())
            self.i += 1
        t = self.peek()
        if t is not None:                              # . ? !
            s.end = t.text
            s.question = s.question or t.text == "?"
            self.i += 1
        return s

    def clause(self) -> Clause:
        subject = None
        t = self.peek()
        if (t is not None and t.kind == WORD and self.marker() is None
                and self.can_noun(t)
                and (self.clause_follows(1) or self.marker(1) is not None)):
            subject = self.noun_phrase()
        markers = []
        while (role := self.marker()) is not None:
            markers.append((role, self.peek()))
            self.i += 1
        t = self.peek()
        if t is None or t.kind != WORD or not self.can_verb(t) or self.is_question_word():
            self.missing_verb(subject, markers)
        verb = _pick(t, {"v"})
        self.i += 1
        c = Clause(subject, markers, t, verb)
        while self.is_word() and not self.is_question_word() and not self.is_connector():
            t = self.peek()
            if self.can_noun(t) or _pick(t, {"adj"}):
                c.objects.append(self.noun_phrase())
            elif _pick(t, {"adv"}):
                c.adverbs.append((t, _pick(t, {"adv"})))
                self.i += 1
            else:
                break
        return c

    def noun_phrase(self) -> NounPhrase:
        before = []
        while self.is_word() and _pick(self.peek(), {"adj"}) and self.is_word(1) \
                and self.can_noun(self.peek(1)):
            t = self.peek()
            before.append((t, _pick(t, {"adj"})))
            self.i += 1
        t = self.peek()
        info = self.pronoun_info(t)
        if info is not None:
            np = NounPhrase(t, _pick(t, {"prn"}) or {"medumba": t.text}, "pronoun", info)
        else:
            entry = _pick(t, NOUNISH) or _pick(t, {"adj"})
            kind = {"np": "name", "num": "number"}.get(entry.get("pos"), "noun")
            np = NounPhrase(t, entry, kind)
        self.i += 1
        np.adjectives = before
        while self.is_word() and _pick(self.peek(), {"adj"}) \
                and not self.can_verb(self.peek()) and not self.is_question_word():
            t = self.peek()
            np.adjectives.append((t, _pick(t, {"adj"})))
            self.i += 1
        return np

    # -- errors -------------------------------------------------------------
    def missing_verb(self, subject: NounPhrase | None, markers) -> None:
        t = self.peek()
        if markers:
            role, mt = markers[-1]
            where = t if t is not None and t.kind == WORD else mt
            visible = sum(1 for ch in mt.text if unicodedata.category(ch) != "Mn")
            raise MeduError("E201", f"expected a verb after '{mt.text}' ({role})",
                            where.line, where.col if where is t else mt.col + visible,
                            hint="put a verb after it, e.g. jʉ (eat), zi (sleep)")
        where = t if t is not None else (subject.token if subject else None)
        line, col = (where.line, where.col) if where else (1, 1)
        raise MeduError("E202", "the sentence needs a verb", line, col,
                        hint="a sentence needs an action word, e.g. mə zi (I slept)")


def parse(tokens: list[Token], lang: Language) -> list[Sentence]:
    """Turn the word cutter's tokens into sentence trees."""
    p = _Parser(tokens, lang)
    sentences = []
    while p.peek() is not None:
        if p.peek().kind == PUNCT:          # stray punctuation between sentences
            p.i += 1
            continue
        sentences.append(p.sentence())
    return sentences
