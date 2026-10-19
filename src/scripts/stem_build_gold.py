"""lexicon/derived.tsv + results/gold_stats.md üretir.

Kullanım: python3 src/scripts/stem_build_gold.py [--min-count 2] [--no-chain]
Gold tanımı için bkz. src/scripts/stem_gold.py docstring.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stem_gold import (ROOT, SPLITS, build_derived, fold, gold_root,  # noqa: E402
                       load_split, write_derived)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-count", type=int, default=2)
    ap.add_argument("--min-ratio", type=float, default=0.5)
    ap.add_argument("--no-chain", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "lexicon" / "derived.tsv"))
    ap.add_argument("--stats", default=str(ROOT / "results" / "gold_stats.md"))
    args = ap.parse_args()

    toks = {s: load_split(s) for s in SPLITS}
    all_toks = [t for s in SPLITS for t in toks[s]]
    derived, stats = build_derived(all_toks, min_count=args.min_count, min_ratio=args.min_ratio,
                                   chain=not args.no_chain)
    write_derived(Path(args.out), derived)

    lines = ["# Gold istatistikleri (stem_build_gold.py)", "",
             f"min_count={args.min_count}, min_ratio={args.min_ratio}, chain={not args.no_chain}", "",
             "## derived.tsv", ""]
    for k, v in sorted(stats.items()):
        lines.append(f"- {k}: {v}")
    depth = Counter(e.depth for e in derived.values())
    lines.append(f"- zincir derinliği dağılımı: {dict(sorted(depth.items()))}")
    lines.append(f"- yalnız train'de görülen tip: {sum('train' in e.splits for e in derived.values())}")
    lines += ["", "## Split başına token sayıları", "",
              "| split | içerik token | form==gold (çıplak) | gold≠lemma (türetim eşlemesi) | DerivedFrom taşıyan |",
              "|---|---|---|---|---|"]
    for s in SPLITS:
        n = len(toks[s])
        bare = sum(gold_root(t, derived) == fold(t.form) for t in toks[s])
        der = sum(gold_root(t, derived) != t.lemma_n for t in toks[s])
        df = sum(1 for t in toks[s] if t.derived_from)
        lines.append(f"| {s} | {n} | {bare} | {der} | {df} |")
    lines += ["", "## Örnek eşlemeler (en sık 25)", "", "| lemma | upos | kök | derinlik | n_agree/n_df/n_lemma |", "|---|---|---|---|---|"]
    for e in sorted(derived.values(), key=lambda x: -x.n_lemma)[:25]:
        lines.append(f"| {e.lemma} | {e.upos} | {e.root} | {e.depth} | {e.n_agree}/{e.n_df}/{e.n_lemma} |")
    Path(args.stats).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
