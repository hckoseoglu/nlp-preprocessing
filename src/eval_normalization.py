"""Normalization değerlendirmesi — sentetik gürültü test case'leri.

SAHİP: Ecem
UD cümlelerini noise.py ile bozar, normalizer'a düzelttirir, orijinalle karşılaştırır.
Gold = UD formunun Türkçe küçük harfi (+ biçim birliği, bkz. normalization.canonical).
Metrik harf içeren tokenlarda; "biçim" satırında tüm tokenlarda (noktalama ve sayılar dahil).
Her satırda:
  baz       : düzeltmesiz (sadece Türkçe küçük harf) skoru — "hiçbir şey yapmasak" ne alırdık
  sistem    : normalizer'ın token accuracy'si
  düzeltme  : bozulmuş tokenların kaçı doğru düzeltildi
  koruma    : bozulmamış tokenların kaçı bozulmadan kaldı

Kullanım:  python src/eval_normalization.py [dev|test] [--errors N]
"""
from __future__ import annotations

import argparse
import random
import zlib
from pathlib import Path

from evaluate import accuracy
from io_conllu import read_conllu
from noise import corrupt, is_word
from normalization import Normalizer, canonical, turkish_lower

_DATA = Path(__file__).resolve().parent.parent / "data" / "UD_Turkish-BOUN"
_REAL = Path(__file__).resolve().parent.parent / "data" / "normalization" / "real_noisy.tsv"

# (rapordaki ad, gürültü tipi, oran, ölçülen tokenlar: "word" = harf içeren / "all" = hepsi)
CASES = [
    ("temiz (bozulmamış)", "clean", 0.0, "word"),
    ("diakritik silme (tümü)", "diacritics", 1.0, "word"),
    ("diakritik silme (%30)", "diacritics", 0.3, "word"),
    ("büyük harf (tümü)", "upper", 1.0, "word"),
    ("harf tekrarı (%20)", "repeat", 0.2, "word"),
    ("typo (%10)", "typo", 0.1, "word"),
    ("biçim (%50, tüm token)", "format", 0.5, "all"),
    ("karışık", "mixed", 0.0, "word"),
]


def case_seed(name: str) -> int:
    """Test case'in sabit seed'i (adından türetilir; tabloya case eklenince diğerleri değişmez)."""
    return zlib.crc32(name.encode("utf-8"))


def run_case(sentences, normalizer: Normalizer, kind: str, rate: float, seed: int,
             scope: str = "word"):
    """Bir test case'i çalıştırır; (gold, baz, sistem, gürültülü) token listelerini döndürür."""
    rng = random.Random(seed)
    gold, base, pred, noisy_all = [], [], [], []
    for s in sentences:
        clean = [t.form for t in s.tokens]
        noisy = corrupt(clean, kind, rate, rng)
        out = normalizer.normalize_tokens(noisy)
        for c, n, o in zip(clean, noisy, out):
            if scope == "all" or is_word(c):
                gold.append(canonical(c))
                base.append(turkish_lower(n))
                pred.append(o)
                noisy_all.append(n)
    return gold, base, pred, noisy_all


def load_real(path: Path) -> list[tuple[list[str], list[str]]]:
    """Elle hazırlanmış gerçek gürültülü set: (gürültülü tokenlar, doğru tokenlar) cümleleri."""
    sents, noisy, gold = [], [], []
    for line in path.read_text(encoding="utf-8").splitlines() + [""]:
        if line.startswith("#"):
            continue
        if not line.strip():
            if noisy:
                sents.append((noisy, gold))
            noisy, gold = [], []
            continue
        n, g = line.split("\t")[:2]
        noisy.append(n.strip())
        gold.append(g.strip())
    return sents


def run_real(sents, normalizer: Normalizer):
    gold, base, pred, noisy_all = [], [], [], []
    for noisy, clean in sents:
        out = normalizer.normalize_tokens(noisy)
        for c, n, o in zip(clean, noisy, out):
            if is_word(c):
                gold.append(canonical(c))
                base.append(turkish_lower(n))
                pred.append(o)
                noisy_all.append(n)
    return gold, base, pred, noisy_all


def scores(gold, base, pred):
    changed = [i for i, (g, b) in enumerate(zip(gold, base)) if g != b]
    kept = [i for i, (g, b) in enumerate(zip(gold, base)) if g == b]
    sub = lambda idx, xs: [xs[i] for i in idx]
    return {
        "baz": accuracy(base, gold),
        "sistem": accuracy(pred, gold),
        "düzeltme": accuracy(sub(changed, pred), sub(changed, gold)) if changed else float("nan"),
        "koruma": accuracy(sub(kept, pred), sub(kept, gold)) if kept else float("nan"),
        "n": len(gold),
        "bozulan": len(changed),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("split", nargs="?", default="dev", choices=["dev", "test"])
    ap.add_argument("--errors", type=int, default=0, help="her case için örnek hata sayısı")
    args = ap.parse_args()

    sentences = read_conllu(_DATA / f"tr_boun-ud-{args.split}.conllu")
    normalizer = Normalizer()

    print(f"Normalization — UD-BOUN {args.split} ({len(sentences)} cümle)\n")
    header = f"{'test case':<24} | {'baz':>6} | {'sistem':>6} | {'düzeltme':>8} | {'koruma':>6} | bozulan"
    print(header)
    print("-" * len(header))
    runs = [(name, lambda n=name, k=kind, r=rate, sc=scope:
             run_case(sentences, normalizer, k, r, seed=case_seed(n), scope=sc))
            for name, kind, rate, scope in CASES]
    real = load_real(_REAL) if _REAL.exists() else []
    if real:
        runs.append(("gerçek gürültülü (elle)", lambda: run_real(real, normalizer)))
    for name, run in runs:
        gold, base, pred, noisy = run()
        sc = scores(gold, base, pred)
        pct = lambda x, w: f"{'-':>{w}}" if x != x else f"{x:{w}.2%}"   # x != x: NaN
        print(f"{name:<24} | {pct(sc['baz'], 6)} | {pct(sc['sistem'], 6)} | "
              f"{pct(sc['düzeltme'], 8)} | {pct(sc['koruma'], 6)} | {sc['bozulan']}/{sc['n']}")
        if args.errors:
            errs = [(n, p, g) for n, p, g in zip(noisy, pred, gold) if p != g]
            for n, p, g in errs[:args.errors]:
                print(f"      {n!r:<22} -> {p!r:<22} (doğrusu {g!r})")


if __name__ == "__main__":
    main()
