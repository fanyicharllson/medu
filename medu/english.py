"""
⑥ English writer

Owner: Charllson
Takes: list[SentenceMeaning] from meaning.build
Gives: English text, one line per sentence, plus notes

    Action(I, sleep, present, progressive)        -> "I am sleeping."
    Action(I, eat, past, negative)                -> "I did not eat."
    Action(I, see, past, question, things=[cat])  -> "Did I see the cat?"

Meanings that were suggested automatically (not checked by a speaker) get a
* and a note, so nobody mistakes a guess for a confirmed translation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from medu.meaning import Action, SentenceMeaning, Thing, Word

# Irregular verbs: base -> (past, past participle)
IRREGULAR = {
    "be": ("was", "been"), "begin": ("began", "begun"), "break": ("broke", "broken"),
    "bring": ("brought", "brought"), "buy": ("bought", "bought"), "come": ("came", "come"),
    "do": ("did", "done"), "drink": ("drank", "drunk"), "eat": ("ate", "eaten"),
    "fall": ("fell", "fallen"), "find": ("found", "found"), "fly": ("flew", "flown"),
    "get": ("got", "got"), "give": ("gave", "given"), "go": ("went", "gone"),
    "have": ("had", "had"), "hear": ("heard", "heard"), "hold": ("held", "held"),
    "know": ("knew", "known"), "leave": ("left", "left"), "make": ("made", "made"),
    "put": ("put", "put"), "run": ("ran", "run"), "say": ("said", "said"),
    "see": ("saw", "seen"), "sell": ("sold", "sold"), "send": ("sent", "sent"),
    "sit": ("sat", "sat"), "sleep": ("slept", "slept"), "speak": ("spoke", "spoken"),
    "stand": ("stood", "stood"), "swim": ("swam", "swum"), "take": ("took", "taken"),
    "teach": ("taught", "taught"), "tell": ("told", "told"), "think": ("thought", "thought"),
    "throw": ("threw", "thrown"), "understand": ("understood", "understood"),
    "wake": ("woke", "woken"), "wear": ("wore", "worn"), "win": ("won", "won"),
    "write": ("wrote", "written"), "cut": ("cut", "cut"), "hit": ("hit", "hit"),
    "lose": ("lost", "lost"), "meet": ("met", "met"), "pay": ("paid", "paid"),
    "read": ("read", "read"), "ride": ("rode", "ridden"), "sing": ("sang", "sung"),
    "spend": ("spent", "spent"), "steal": ("stole", "stolen"), "feel": ("felt", "felt"),
    "fight": ("fought", "fought"), "hide": ("hid", "hidden"), "keep": ("kept", "kept"),
    "lay": ("laid", "laid"), "lie": ("lay", "lain"), "become": ("became", "become"),
}
VOWELS = set("aeiou")


@dataclass
class Result:
    lines: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    read_as: str = ""

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


# ---------------------------------------------------------------------------
# Verb forms
# ---------------------------------------------------------------------------

def _split(verb: str) -> tuple[str, str]:
    """'dispose of' -> ('dispose', ' of'): only the first word changes form."""
    head, _, rest = verb.partition(" ")
    return head, (" " + rest if rest else "")


def past(verb: str) -> str:
    head, rest = _split(verb)
    if head in IRREGULAR:
        return IRREGULAR[head][0] + rest
    if head.endswith("e"):
        return head + "d" + rest
    if head.endswith("y") and len(head) > 1 and head[-2] not in VOWELS:
        return head[:-1] + "ied" + rest
    if _double_last(head):
        return head + head[-1] + "ed" + rest
    return head + "ed" + rest


def ing(verb: str) -> str:
    head, rest = _split(verb)
    if head == "be":
        return "being" + rest
    if head.endswith("ie"):
        return head[:-2] + "ying" + rest
    if head.endswith("e") and not head.endswith(("ee", "ye", "oe")):
        return head[:-1] + "ing" + rest
    if _double_last(head):
        return head + head[-1] + "ing" + rest
    return head + "ing" + rest


def third_person(verb: str) -> str:
    head, rest = _split(verb)
    if head == "be":
        return "is" + rest
    if head == "have":
        return "has" + rest
    if head.endswith(("s", "sh", "ch", "x", "z", "o")):
        return head + "es" + rest
    if head.endswith("y") and len(head) > 1 and head[-2] not in VOWELS:
        return head[:-1] + "ies" + rest
    return head + "s" + rest


def _double_last(w: str) -> bool:
    """stop -> stopp-ed, run -> runn-ing (short words ending consonant-vowel-consonant)."""
    return (len(w) >= 3 and len(w) <= 4 and w[-1] not in VOWELS | set("wxy")
            and w[-2] in VOWELS and w[-3] not in VOWELS)


def _be(who: Thing | None, time: str) -> str:
    third_sg = who is None or (who.person == 3 and not who.plural)
    if time == "past":
        return "was" if (who is None or (not who.plural and who.person in (1, 3))) else "were"
    if who is not None and who.person == 1 and not who.plural:
        return "am"
    return "is" if third_sg else "are"


def _do(who: Thing | None, time: str) -> str:
    if time == "past":
        return "did"
    third_sg = who is not None and who.person == 3 and not who.plural
    return "does" if third_sg else "do"


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------

class _Writer:
    def __init__(self) -> None:
        self.unsure: list[Word] = []

    def w(self, word: Word) -> str:
        if not word.sure:
            self.unsure.append(word)
            return word.en + "*"
        return word.en

    def thing(self, t: Thing, as_object: bool = False) -> str:
        if t.kind == "pronoun":
            return t.obj_form if as_object else t.word.en
        words = [self.w(d) for d in t.describers] + [self.w(t.word)]
        phrase = " ".join(words)
        return phrase if t.kind in ("name", "number") else "the " + phrase

    def verb_phrase(self, a: Action, question: bool) -> tuple[str, str]:
        """Returns (part before the subject, part after it).
        Questions move the helper verb in front: "Did" + "I see"."""
        v = self.w(a.verb)
        if not a.verb.sure:          # keep the * after the whole verb form
            v = a.verb.en
            mark = "*"
        else:
            mark = ""
        neg = " not" if a.negative else ""
        if a.aspect == "order":
            return ("do not" if a.negative else ""), v + mark
        if a.time == "future":
            front, back = "will", f"{neg} {v}{mark}"
        elif a.aspect == "progressive":
            front, back = _be(a.who, a.time), f"{neg} {ing(v)}{mark}"
        elif a.negative or question:
            front, back = _do(a.who, a.time), f"{neg} {v}{mark}"
        elif a.time == "past":
            return "", past(v) + mark
        elif a.who is not None and a.who.person == 3 and not a.who.plural:
            return "", third_person(v) + mark
        else:
            return "", v + mark
        if a.aspect == "habitual":
            back = " always" + back
        return front, back.strip()

    def action(self, a: Action, question: bool) -> str:
        front, back = self.verb_phrase(a, question)
        if a.aspect == "habitual" and not front:
            back = "always " + back
        rest = [self.thing(t, as_object=True) for t in a.things]
        if len(rest) == 2:                       # give the dog to the woman
            rest = [rest[0], "to " + rest[1]]
        rest += [self.w(x) for x in a.extras]
        tail = (" " + " ".join(rest)) if rest else ""
        if a.who is None:                        # no subject: an order ("Sleep.")
            return (front + " " + back if front else back) + tail
        subj = self.thing(a.who)
        if question and front:
            return f"{front} {subj} {back}{tail}"
        return f"{subj} {front + ' ' if front else ''}{back}{tail}"

    def sentence(self, m: SentenceMeaning) -> str:
        parts = [self.action(m.actions[0], m.question)]
        for link, a in zip(m.links, m.actions[1:]):
            joiner = "," if link.en == "," else f" {self.w(link)}"
            parts.append(f"{joiner} {self.action(a, m.question)}")
        text = "".join(parts)
        if m.rough:
            text += " … " + " ".join(self.w(r) for r in m.rough)
        text = text[0].upper() + text[1:]
        return text + ("?" if m.question else ".")


def write(meanings: list[SentenceMeaning]) -> Result:
    writer = _Writer()
    result = Result()
    for m in meanings:
        result.lines.append(writer.sentence(m))
        if m.rough:
            result.warnings.append(
                "warning[W301]: part of a sentence has no grammar rule yet; "
                "it is translated word by word after '…'")
    pairs = []
    for word in writer.unsure:
        pair = f"{word.source} = {word.en.strip('[]')}"
        if pair not in pairs:
            pairs.append(pair)
    if pairs:
        result.notes.append("* not yet checked by a speaker: " + ", ".join(pairs))
    return result
