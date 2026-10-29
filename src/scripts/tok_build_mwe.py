"""Builds the MWE lexicon resources/mwe_tr.txt from the UD-BOUN training split (see tokenization/mwe.py).

Usage:  python src/scripts/tok_build_mwe.py [--min-share 0.2]
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from tokenization.corpus import load_split  # noqa: E402
from tokenization.mwe import LEXICON_FILE, build_lexicon, gold_mwes, save_lexicon  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-share", type=float, default=0.2,
                    help="keep an expression if it is an MWE in at least this share of its occurrences")
    args = ap.parse_args()

    train = load_split("train")
    gold = Counter(kind for s in train for _, _, kind in gold_mwes(s))
    lexicon = build_lexicon(train, args.min_share)
    save_lexicon(lexicon)
    kept = Counter(entry.kind for entry, _, _ in lexicon)
    print(f"{LEXICON_FILE.relative_to(ROOT)}: {len(lexicon)} entries")
    for kind in gold:
        examples = ", ".join([" ".join(e.words) for e, _, _ in lexicon if e.kind == kind][:5])
        print(f"  {kind:<6} {gold[kind]:>4} MWEs in train → {kept[kind]:>4} entries   e.g. {examples}")


if __name__ == "__main__":
    main()
