"""Counts of the tokenization candidate point corpus (train / dev / test) + one example sentence.

The progress report's "22,713 candidate points from train, 16,701 of them split" are produced with
this definition (see src/tokenization/corpus.py).

Usage:  python src/scripts/tok_corpus_stats.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from tokenization.corpus import CONVENTIONS, corpus_stats, load_split, show  # noqa: E402


def main() -> None:
    print(f"{'split':<12} {'cümle':>6} {'token':>7} {'parça':>7} {'bölünecek':>9} "
          f"{'aday':>7} {'bölünür':>8} {'aday dışı':>9}")
    for split in ("train", "dev", "test"):
        sentences = load_split(split)
        for convention in CONVENTIONS:          # "tdk" = our gold, "ud" = plain UD-BOUN (progress report)
            s = corpus_stats(sentences, convention)
            print(f"{split + ' (' + convention + ')':<12} {s['sentences']:>6,} {s['tokens']:>7,} {s['chunks']:>7,} "
                  f"{s['chunks_to_split']:>9,} {s['candidates']:>7,} {s['splits']:>8,} {s['missed']:>9,}")

    example = next(s for s in load_split("dev") if "'" in s.text and "," in s.text)
    print(f"\nÖrnek (dev): {example.text}")
    print(f"             {show(example)}")
    print("             | bölünür   · aday ama bölünmez")


if __name__ == "__main__":
    main()
