"""Tests for Mode 2: Medumba sentences -> English (stations ③ to ⑥)."""

import pytest

from medu import languages, mode2
from medu.english import ing, past, third_person
from medu.errors import MeduError

LANG = languages.load("medumba")


def en(text):
    return mode2.translate(text, LANG).text


# ---------------- sentences that must translate ----------------

@pytest.mark.parametrize("medumba, english", [
    ("mə nɛ̌n zi.", "I am sleeping."),            # fieldwork sentence
    ("me nen zi", "I am sleeping."),              # typed with plain letters
    ("mə zi.", "I slept."),                       # no marker = recent past
    ("mə fə̀ zi.", "I slept."),                   # past marker
    ("mə àʼ jʉ.", "I will eat."),                 # future
    ("mə kə̀ jʉ.", "I did not eat."),             # negation
    ("a kə̀ nɛ̌n zi.", "He/she is not sleeping."),
    ("a yən mbʉ.", "He/she saw the dog."),       # subject verb object
    ("a yən mbʉ ki?", "Did he/she see the dog?"),  # question word at the end
    ("mə yən bùsi ki", "Did I see the cat?"),
    ("bo àʼ kə̀ nu ntsə ki?", "Will they not drink the water?"),
    ("mɛ̀nnzwi swɛn mbʉ.", "The woman sold the dog."),
    ("mə fɑ mbʉ mɛ̀nnzwi.", "I gave the dog to the woman."),   # two objects
    ("mɛn nɛ̌n zi.", "The child is sleeping."),
    ("Ariane yən mə.", "Ariane saw me."),         # name + object pronoun
    ("zi.", "Sleep."),                            # no subject = an order
    ("kə̀ zi.", "Do not sleep."),
])
def test_translation(medumba, english):
    assert en(medumba) == english


def test_two_sentences_in_one_text():
    assert mode2.translate("mə zi. a jʉ.", LANG).lines == ["I slept.", "He/she ate."]


def test_two_clauses_with_and():
    assert en("mə zi mbɑ̀ a jʉ.").startswith("I slept and")


def test_read_as_note_for_plain_letters():
    assert mode2.translate("me nen zi", LANG).read_as == "mə nɛ̌n zi"
    assert mode2.translate("mə nɛ̌n zi", LANG).read_as == ""


def test_unchecked_meaning_is_marked():
    r = mode2.translate("mə jʉ caŋ.", LANG)
    assert "food*" in r.text
    assert r.notes and "caŋ" in r.notes[0]


# ---------------- errors ----------------

@pytest.mark.parametrize("medumba, code", [
    ("mə zii.", "E101"),          # unknown word
    ("mə kə̀.", "E201"),          # grammar word with no verb after it
    ("mbʉ.", "E202"),             # no verb at all
    ("mə kə̀ kə̀ jʉ.", "E311"),   # negation twice
    ("mə àʼ fə̀ jʉ.", "E312"),    # past and future together
])
def test_errors(medumba, code):
    with pytest.raises(MeduError) as err:
        mode2.translate(medumba, LANG)
    assert err.value.code == code


def test_error_position():
    with pytest.raises(MeduError) as err:
        mode2.translate("mə nɛ̌n zii.", LANG)
    assert (err.value.line, err.value.col) == (1, 8)


# ---------------- English verb forms ----------------

@pytest.mark.parametrize("verb, p, g, s", [
    ("eat", "ate", "eating", "eats"),
    ("sleep", "slept", "sleeping", "sleeps"),
    ("stop", "stopped", "stopping", "stops"),
    ("carry", "carried", "carrying", "carries"),
    ("dance", "danced", "dancing", "dances"),
    ("lie", "lay", "lying", "lies"),
    ("wash", "washed", "washing", "washes"),
    ("dispose of", "disposed of", "disposing of", "disposes of"),
])
def test_verb_forms(verb, p, g, s):
    assert (past(verb), ing(verb), third_person(verb)) == (p, g, s)
