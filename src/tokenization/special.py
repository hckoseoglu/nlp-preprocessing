"""Synthetic special entities (URL, e-mail, hashtag, mention) inserted into UD sentences.

UD-BOUN contains no URLs, e-mails or hashtags, so the Logistic Regression tokenizer could never learn
from UD alone to keep them in one piece. We generate such entities and insert them into sentences:

    training (step 3):  copies of 20% of the train sentences, seed 0, TRAIN_VOCAB
                        → extra training examples for the LR tokenizer
    testing  (step 4):  every dev / test sentence once, seed 1 / 2, TEST_VOCAB
                        → test case 3, saved by src/scripts/tok_build_special.py

The test entities are built from other words and hashtags than the training ones (TEST_VOCAB), so the
LR tokenizer cannot simply remember the strings it saw in training. The top-level domains are the
same, because in real text they are a small closed list.

Each inserted entity is one gold token, marked with `Entity=<kind>` in the MISC column of the saved
file. Sometimes a comma or the sentence-final period follows it directly ("boun.edu.tr," /
"boun.edu.tr."); that punctuation stays a separate token.
"""
from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from io_conllu import Sentence, Token, Word

from .corpus import gold_tokens
from .metrics import token_spans


@dataclass(frozen=True)
class Vocabulary:
    """Small, made-up building blocks for entities (ASCII, as in real domain names and user names)."""
    words: tuple[str, ...]        # domain names, URL paths, user names
    users: tuple[str, ...]        # common e-mail user names
    hashtags: tuple[str, ...]


TRAIN_VOCAB = Vocabulary(
    words=("haber", "spor", "ekonomi", "kitap", "okul", "sinema", "muzik", "hava", "yemek", "tarih",
           "bilim", "saglik", "egitim", "gundem", "kultur", "teknoloji", "dunya", "ankara", "istanbul", "izmir"),
    users=("info", "iletisim", "destek"),
    hashtags=("#nlp", "#Türkiye", "#İstanbul", "#BoğaziçiÜniversitesi", "#seçim2026", "#haber", "#GünaydınTürkiye",
              "#kitapokuyorum", "#spor", "#ekonomi", "#deprem", "#İyiBayramlar"),
)
TEST_VOCAB = Vocabulary(
    words=("gazete", "radyo", "muze", "oyun", "film", "doga", "seyahat", "araba", "moda", "sanat",
           "felsefe", "matematik", "fizik", "kimya", "bursa", "antalya", "trabzon", "konya", "eskisehir", "edirne"),
    users=("bilgi", "yardim", "basin"),
    hashtags=("#yapayzeka", "#Ankara", "#ÇanakkaleGeçilmez", "#bilim", "#maç", "#YeniYıl", "#oy2026", "#müzik",
              "#sanat", "#TeknolojiHaberleri", "#ÖğretmenlerGünü", "#doğa"),
)
TLDS = ("com", "com.tr", "org", "org.tr", "net", "edu.tr", "gov.tr")
SEEDS = {"train": 0, "dev": 1, "test": 2}


def make_url(rng: random.Random, vocab: Vocabulary = TRAIN_VOCAB) -> str:
    """e.g. https://www.haber.com.tr/spor/2026/10/28/mac-sonucu  ·  www.kitap.org  ·  http://okul.edu.tr/?id=12"""
    domain = rng.choice(["", "www."]) + rng.choice(vocab.words) + "." + rng.choice(TLDS)
    if domain.startswith("www.") and rng.random() < 0.5:
        return domain                                          # www.kitap.org
    path = "/".join(rng.choice([*vocab.words, str(rng.randint(1, 2026))]) for _ in range(rng.randint(0, 3)))
    if path and rng.random() < 0.3:
        path += "-" + rng.choice(vocab.words)
    if rng.random() < 0.2:
        path += f"?id={rng.randint(1, 999)}"
    return rng.choice(["https://", "http://"]) + domain + ("/" + path if path else "")


def make_email(rng: random.Random, vocab: Vocabulary = TRAIN_VOCAB) -> str:
    """e.g. ecem.yildirim@boun.edu.tr  ·  info@haber.com"""
    if rng.random() < 0.5:
        user = rng.choice(vocab.users)
    else:
        user = (rng.choice(vocab.words) + rng.choice([".", "_", ""]) + rng.choice(vocab.words)
                + rng.choice(["", str(rng.randint(1, 99))]))
    return f"{user}@{rng.choice(vocab.words)}.{rng.choice(TLDS)}"


def make_hashtag(rng: random.Random, vocab: Vocabulary = TRAIN_VOCAB) -> str:
    return rng.choice(vocab.hashtags)


def make_mention(rng: random.Random, vocab: Vocabulary = TRAIN_VOCAB) -> str:
    """e.g. @haber_spor  ·  @kitap42"""
    return "@" + rng.choice(vocab.words) + rng.choice(["", "_" + rng.choice(vocab.words), str(rng.randint(1, 99))])


MAKERS: dict[str, Callable[[random.Random, Vocabulary], str]] = {
    "url": make_url, "email": make_email, "hashtag": make_hashtag, "mention": make_mention}


def insert_entity(tokens: list[tuple[str, bool]], entity: str, rng: random.Random) -> tuple[list[tuple[str, bool]], int]:
    """Inserts `entity` as one token into a (form, space after) token list, at a word boundary.

    30% of the time it goes right before the sentence-final mark ("... adresi boun.edu.tr."), and
    30% of the other times a comma follows it directly ("boun.edu.tr, ..."). Returns the new token
    list and the position of the entity in it.
    """
    tokens = list(tokens)
    if len(tokens) > 1 and tokens[-1][0] in (".", "!", "?") and rng.random() < 0.3:
        tokens[-2] = (tokens[-2][0], True)                      # a space before the entity
        i = len(tokens) - 1
        tokens.insert(i, (entity, False))                       # entity directly followed by "."
        return tokens, i
    positions = [i for i in range(len(tokens)) if i == 0 or tokens[i - 1][1]]   # after a space
    i = rng.choice(positions)
    tokens[i:i] = [(entity, True)] if rng.random() > 0.3 else [(entity, False), (",", True)]
    return tokens, i


def with_entity(sentence: Sentence, rng: random.Random, vocab: Vocabulary = TRAIN_VOCAB) -> Sentence:
    """A copy of the sentence with one random special entity inserted (gold tokens included)."""
    kind = rng.choice(list(MAKERS))
    entity = MAKERS[kind](rng, vocab)
    tokens, position = insert_entity(gold_tokens(sentence, "tdk"), entity, rng)
    text = "".join(form + (" " if space else "") for form, space in tokens).rstrip()
    new_tokens = [Token(form=form, space_after=space) for form, space in tokens]
    new_tokens[position].words = [Word(idx=0, form=entity, lemma="_", upos="_", misc=f"Entity={kind}")]
    return Sentence(sent_id=f"{sentence.sent_id}+{kind}", text=text, tokens=new_tokens)


def augment(sentences: list[Sentence], rate: float = 0.2, seed: int = 0,
            vocab: Vocabulary = TRAIN_VOCAB) -> list[Sentence]:
    """Copies of `rate` of the sentences, each with one special entity (fixed seed → reproducible)."""
    rng = random.Random(seed)
    return [with_entity(s, rng, vocab) for s in sentences if rng.random() < rate]


# --- the saved test set ---------------------------------------------------------------------------

def entity_kind(token: Token) -> str | None:
    """"url" / "email" / "hashtag" / "mention" for an inserted entity, None for an ordinary token."""
    for word in token.words:
        for item in word.misc.split("|"):
            if item.startswith("Entity="):
                return item.removeprefix("Entity=")
    return None


def write_conllu(sentences: list[Sentence], path: Path) -> None:
    """Saves sentences as a minimal CoNLL-U file (only ID, FORM and MISC are filled in).

    It can be read back with io_conllu.read_conllu; gold_tokens(..., "tdk") gives the same tokens.
    """
    lines = []
    for s in sentences:
        lines += [f"# sent_id = {s.sent_id}", f"# text = {s.text}"]
        for i, token in enumerate(s.tokens, 1):
            kind = entity_kind(token)
            misc = [f"Entity={kind}"] if kind else []
            if not token.space_after:
                misc.append("SpaceAfter=No")
            lines.append("\t".join([str(i), token.form] + ["_"] * 7 + ["|".join(misc) or "_"]))
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def evaluate_entities(tokenize: Callable[[str], list[str]], sentences: list[Sentence]) -> dict[str, tuple[int, int]]:
    """For each entity kind: (entities kept as exactly one token, all entities)."""
    kept: Counter = Counter()
    total: Counter = Counter()
    for s in sentences:
        gold = token_spans(s.text, [t.form for t in s.tokens])
        pred = set(token_spans(s.text, tokenize(s.text)) or [])
        for token, span in zip(s.tokens, gold or []):
            kind = entity_kind(token)
            if kind:
                total[kind] += 1
                kept[kind] += span in pred
    return {kind: (kept[kind], total[kind]) for kind in MAKERS}
