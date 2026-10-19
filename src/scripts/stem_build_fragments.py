"""lexicon/copula_fragments.tsv: UD-BOUN'un ayrı sözcük olarak böldüğü ek-fiil parçacıkları (du, ydı, ken, dır,
ise ...) ve UD lemma sözleşmesi ('y' = -(y)DI/-(y)mIş/-(y)sA/-(y)ken parçaları, 'i' = -DIr ve i- biçimleri).

Biçimler kural-tabanlı üretilir (ek şablonları); train'de gerçek sözcükle çakışan biçimler (sen, din, dur ...)
yalnızca parçacık kullanımı daha sıksa tutulur. Kullanım: python3 src/scripts/stem_build_fragments.py
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "scripts"))
from stemmer.suffixes import Suffix, expand  # noqa: E402
from stem_gold import fold, load_split  # noqa: E402


def forms(template: str) -> set[str]:
    return {a.surface for a in expand(Suffix("X", template, "X", "-", "-"))}


def main() -> None:
    pers_a = {""} | forms("m") | forms("n") | forms("k") | forms("nIz") | forms("lAr")
    pers_b = {""} | forms("(y)Im") | forms("sIn") | forms("(y)Iz") | forms("sInIz") | forms("lAr")
    frag: dict[str, str] = {}
    for base in forms("(y)DI") | forms("(y)sA"):
        for p in pers_a:
            frag[base + p] = "y"
    for base in forms("(y)mIş"):
        for p in pers_b:
            frag[base + p] = "y"
    for base in forms("(y)ken"):
        frag[base] = "y"
    for base in forms("DIr"):
        for p in {""} | forms("lAr"):
            frag[base + p] = "i"
    for base in ["idi", "ise", "imiş", "iken"]:
        frag[base] = "i"
        for p in (pers_a if base in ("idi", "ise") else pers_b):
            frag[base + p] = "i"

    train = load_split("train")
    n_frag, n_other = Counter(), Counter()
    for t in train:
        f = fold(t.form)
        if f not in frag:
            continue
        if t.upos in ("AUX", "PART") and t.lemma_n in ("y", "i"):
            n_frag[f] += 1
        else:
            n_other[f] += 1
    roots = set()
    with (ROOT / "lexicon" / "roots.tsv").open(encoding="utf-8") as fh:
        fh.readline()
        for line in fh:
            roots.add(line.split("\t")[0])

    kept, dropped = [], []
    for f, lemma in sorted(frag.items()):
        if n_other[f] and n_other[f] >= n_frag[f]:
            dropped.append((f, n_frag[f], n_other[f]))
        elif n_frag[f] == 0 and f in roots:
            dropped.append((f, 0, 0))
        else:
            kept.append((f, lemma, n_frag[f], n_other[f]))
    out = ROOT / "lexicon" / "copula_fragments.tsv"
    with out.open("w", encoding="utf-8") as fh:
        fh.write("form\tlemma\tn_frag_train\tn_other_train\n")
        for f, lemma, a, b in kept:
            fh.write(f"{f}\t{lemma}\t{a}\t{b}\n")
    print(f"üretilen biçim: {len(frag)}; tutulan: {len(kept)}; elenen: {len(dropped)}")
    print("elenenler (biçim, parçacık, diğer):", dropped)


if __name__ == "__main__":
    main()
