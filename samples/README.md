# Samples to try

Open a terminal in VS Code (in the `medu` folder, virtual environment active):

```bash
python -m medu.mode2 samples/sentences.mdt        # many sentences at once
python -m medu.mode2 samples/plain_letters.mdt    # typed without special letters
python -m medu.mode2 samples/errors/no_verb.mdt   # each file in errors/ shows one error
python -m medu.mode2                              # interactive prompt: type a sentence
```

When `cli.py` is ready, the same works with `medu translate file.mdt` and `medu`.

## Words to build your own sentences

| Medumba | English | Kind |
|---|---|---|
| mə, a, bo, bin, bag | I, he/she, they, you (all), we | pronoun |
| zi, jʉ, nu, yən, fɑ, swɛn, zwi | sleep, eat, drink, see, give, sell, kill | verb |
| mbʉ, bùsi, ntsə, mɛn, mɛ̀nnzwi, caŋ | dog, cat, water, child, woman, food | noun |
| kə̀ | not | before the verb |
| fə̀ | past | before the verb |
| àʼ | future (will) | before the verb |
| nɛ̌n | -ing (am …ing) | before the verb |
| nùm | always | before the verb |
| ki | question | at the end |
| mbɑ̀ | and | between two sentences |

Pattern: **who + [kə̀ / fə̀ / àʼ / nɛ̌n / nùm] + verb + [thing] + [ki]**

A `*` after a word means its meaning was suggested automatically and still needs a speaker to confirm it.
