"""Stemming değerlendirme: exact-match vs UD lemma, POS kırılımı + baseline karşılaştırması.

Kullanım: python3 src/eval_stemming.py [dev|test|train]
Baseline olarak Snowball (varsa), fixed-prefix-5 ve no-op raporlanır.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_conllu import read_conllu          # noqa: E402
from stemming import stem, tr_lower         # noqa: E402

try:
    import snowballstemmer
    _SNOW = snowballstemmer.stemmer("turkish")
    snow = lambda w: _SNOW.stemWord(w)       # noqa: E731
except Exception:
    snow = None


def evaluate(split: str = "dev") -> None:
    path = f"data/UD_Turkish-BOUN/tr_boun-ud-{split}.conllu"
    sents = read_conllu(path)

    # (form, lemma, upos) — sadece alfabetik kelimeler
    data = []
    for s in sents:
        for w in s.words:
            if w.lemma in ("_", "null", "") or not w.form[:1].isalpha():
                continue
            data.append((w.form, w.lemma, w.upos))

    methods = {"bizim (v0)": lambda w: stem(w),
               "no-op": lambda w: tr_lower(w),
               "fixed-prefix-5": lambda w: tr_lower(w)[:5]}
    if snow is not None:
        methods["snowball"] = lambda w: snow(tr_lower(w))

    print(f"=== {split}: n={len(data)} kelime ===\n")
    # genel
    print(f"{'yöntem':16} | {'genel acc':>9}")
    print("-" * 30)
    for name, fn in methods.items():
        acc = sum(fn(f) == tr_lower(l) for f, l, _ in data) / len(data)
        print(f"{name:16} | {acc:9.3f}")

    # POS kırılımı (sadece bizim stemmer)
    print(f"\n=== POS kırılımı (bizim v0 vs snowball) ===")
    tot = Counter(); ok_us = Counter(); ok_sn = Counter()
    for f, l, pos in data:
        tot[pos] += 1
        if stem(f) == tr_lower(l): ok_us[pos] += 1
        if snow is not None and snow(tr_lower(f)) == tr_lower(l): ok_sn[pos] += 1
    print(f"{'POS':8} {'n':>5} {'bizim':>7} {'snowball':>9}")
    for pos, n in tot.most_common(10):
        sn = f"{ok_sn[pos]/n:7.3f}" if snow else "   -   "
        print(f"{pos:8} {n:5} {ok_us[pos]/n:7.3f} {sn:>9}")


if __name__ == "__main__":
    evaluate(sys.argv[1] if len(sys.argv) > 1 else "dev")
