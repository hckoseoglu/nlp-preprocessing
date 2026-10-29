"""Builds the special-entity test sets (test case 3): every dev / test sentence with one URL, e-mail,
hashtag or mention inserted (tokenization/special.py: TEST_VOCAB, seed 1 for dev, 2 for test).

Output: data/tokenization/special_dev.conllu and special_test.conllu (minimal CoNLL-U; the inserted
entity is marked with Entity=<kind> in the MISC column). Running it again gives the same files.

Usage:  python src/scripts/tok_build_special.py
"""
from __future__ import annotations

import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from tokenization.corpus import load_split  # noqa: E402
from tokenization.special import SEEDS, TEST_VOCAB, entity_kind, with_entity, write_conllu  # noqa: E402

OUT = ROOT / "data" / "tokenization"


def main() -> None:
    for split in ("dev", "test"):
        rng = random.Random(SEEDS[split])
        sentences = [with_entity(s, rng, TEST_VOCAB) for s in load_split(split)]
        path = OUT / f"special_{split}.conllu"
        write_conllu(sentences, path)
        kinds = Counter(entity_kind(t) for s in sentences for t in s.tokens if entity_kind(t))
        print(f"{path.relative_to(ROOT)}: {len(sentences)} sentences — " + ", ".join(f"{k} {n}" for k, n in kinds.items()))
    print(f"Example: {sentences[0].text}")


if __name__ == "__main__":
    main()
