"""CoNLL-U reader for UD Turkish-BOUN.

Zemin modülü — hem stemming hem normalization hem stopword bunun üstüne kurulur.
Bir CoNLL-U dosyasını cümlelere ayırır; her cümle için:
  - sent_id, text (`# text =` satırı)
  - surface tokens (tokenization gold): çoklu-sözcük aralıklarının (ör. `2-3 yılındayız`)
    yüzey formu + aralığa girmeyen tekil tokenlar
  - syntactic words (stemming/stopword için): tekil satırlar, form + lemma + UPOS + feats

CoNLL-U kolonları: ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC
Çoklu-sözcük token satırı: ID aralıktır (ör. "2-3"), yalnızca FORM dolu, altındaki tekil
satırlar (2, 3) gerçek sözcüklerdir ve lemma taşır.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass
class Word:
    """Tek bir sözdizimsel sözcük (CoNLL-U tekil satırı)."""
    idx: int
    form: str
    lemma: str
    upos: str
    feats: str = "_"
    space_after: bool = True  # MISC'te SpaceAfter=No yoksa True


@dataclass
class Token:
    """Yüzey tokeni (tokenization gold). Çoklu-sözcük ise birden çok Word'e karşılık gelir."""
    form: str
    space_after: bool = True
    words: list[Word] = field(default_factory=list)  # bu yüzey tokenini oluşturan sözcükler


@dataclass
class Sentence:
    sent_id: str
    text: str
    tokens: list[Token] = field(default_factory=list)   # tokenization gold
    words: list[Word] = field(default_factory=list)      # stemming/stopword için düz liste


def _misc_space_after(misc: str) -> bool:
    return "SpaceAfter=No" not in misc


def read_conllu(path: str | Path) -> list[Sentence]:
    """CoNLL-U dosyasını cümle listesine çevirir."""
    return list(iter_conllu(path))


def iter_conllu(path: str | Path) -> Iterator[Sentence]:
    """CoNLL-U dosyasını cümle cümle üretir (büyük dosyalar için bellek dostu)."""
    path = Path(path)
    sent_id = ""
    text = ""
    tokens: list[Token] = []
    words: list[Word] = []
    mwt_remaining = 0          # çoklu-sözcük aralığında kalan tekil satır sayısı
    mwt_token: Token | None = None

    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                if sent_id or tokens or words:
                    yield Sentence(sent_id=sent_id, text=text, tokens=tokens, words=words)
                sent_id, text = "", ""
                tokens, words = [], []
                mwt_remaining, mwt_token = 0, None
                continue
            if line.startswith("#"):
                if line.startswith("# sent_id"):
                    sent_id = line.split("=", 1)[1].strip()
                elif line.startswith("# text"):
                    text = line.split("=", 1)[1].strip()
                continue

            cols = line.split("\t")
            if len(cols) < 10:
                continue
            tid, form, lemma, upos, _xpos, feats, _head, _deprel, _deps, misc = cols[:10]
            space_after = _misc_space_after(misc)

            if "-" in tid:  # çoklu-sözcük token satırı
                start, end = tid.split("-")
                mwt_remaining = int(end) - int(start) + 1
                mwt_token = Token(form=form, space_after=space_after)
                tokens.append(mwt_token)
                continue
            if "." in tid:  # boş düğüm (enhanced deps) — atla
                continue

            word = Word(idx=int(tid), form=form, lemma=lemma, upos=upos,
                        feats=feats, space_after=space_after)
            words.append(word)

            if mwt_remaining > 0 and mwt_token is not None:
                mwt_token.words.append(word)
                mwt_remaining -= 1
            else:
                tokens.append(Token(form=form, space_after=space_after, words=[word]))

        if sent_id or tokens or words:
            yield Sentence(sent_id=sent_id, text=text, tokens=tokens, words=words)


# --- Task'lar için kolay erişim yardımcıları ------------------------------------

def gold_tokens(sentences: list[Sentence]) -> list[list[str]]:
    """Her cümle için yüzey token listesi (tokenization gold)."""
    return [[t.form for t in s.tokens] for s in sentences]


def lemma_pairs(sentences: list[Sentence]) -> list[tuple[str, str]]:
    """(sözcük_formu, gold_lemma) çiftleri — STEMMING değerlendirmesi için.

    Not: UD lemma'sı stem değildir; iyi bir proxy'dir (bkz. CLAUDE.md stemming notu).
    'null' lemmalar (zero-copula AUX vb.) atlanır.
    """
    pairs: list[tuple[str, str]] = []
    for s in sentences:
        for w in s.words:
            if w.lemma and w.lemma != "_" and w.lemma != "null":
                pairs.append((w.form, w.lemma))
    return pairs


def word_frequencies(sentences: list[Sentence]) -> dict[str, int]:
    """Yüzey-form frekansları (dynamic STOPWORD üretimi için)."""
    freq: dict[str, int] = {}
    for s in sentences:
        for w in s.words:
            key = w.form.casefold()
            freq[key] = freq.get(key, 0) + 1
    return freq


if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else "data/UD_Turkish-BOUN/tr_boun-ud-dev.conllu"
    sents = read_conllu(p)
    print(f"{len(sents)} sentences")
    s = sents[0]
    print("sent_id:", s.sent_id)
    print("text   :", s.text)
    print("tokens :", [t.form for t in s.tokens])
    print("lemmas :", [(w.form, w.lemma) for w in s.words])
