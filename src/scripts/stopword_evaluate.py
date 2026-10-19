"""Stopword değerlendirme: static / dynamic / static∪dynamic / static∩dynamic.
Gold = UPOS-proxy (kapalı-sınıf). K dev F1 ile seçilir. Ayrıca dynamic↔static set örtüşmesi.
Kullanım: python3 src/scripts/stopword_evaluate.py   (proje kökünden)
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from io_conllu import read_conllu                                               # noqa: E402
from stopword import (compute_stats, dynamic_stopwords, load_static_stopwords,  # noqa: E402
                      evaluate_list)

DATA = ROOT / "data" / "UD_Turkish-BOUN"
REPORTS = ROOT / "reports"


def main() -> None:
    train = read_conllu(f"{DATA}/tr_boun-ud-train.conllu")
    dev = read_conllu(f"{DATA}/tr_boun-ud-dev.conllu")
    test = read_conllu(f"{DATA}/tr_boun-ud-test.conllu")

    stats = compute_stats(train)
    static = load_static_stopwords(ROOT / "resources" / "stopwords_tr.txt")

    # K'yı dev F1 ile seç (dynamic, tf-idf)
    bestK, bestF = 0, -1.0
    for k in range(25, 1001, 25):
        _, _, f = evaluate_list(dynamic_stopwords(stats, k), dev)
        if f > bestF:
            bestK, bestF = k, f
    dyn = dynamic_stopwords(stats, bestK)
    union = dyn | static
    inter = dyn & static

    systems = [("static", static), (f"dynamic\n(K={bestK})", dyn),
               ("static ∪\ndynamic", union), ("static ∩\ndynamic", inter)]

    results = {}  # split -> list of (name, P, R, F1)
    for split, data in [("DEV", dev), ("TEST", test)]:
        rows = []
        print(f"\n=== {split} (gold = UPOS-proxy) ===")
        print(f"{'sistem':20}{'|liste|':>8}{'P':>8}{'R':>8}{'F1':>8}")
        print("-" * 52)
        for name, s in systems:
            p, r, f = evaluate_list(s, data)
            rows.append((name.replace("\n", " "), p, r, f))
            print(f"{name.replace(chr(10),' '):20}{len(s):8}{p:8.3f}{r:8.3f}{f:8.3f}")
        results[split] = rows

    # Reference-list karşılaştırması: dynamic ne kadar static'i buluyor
    prec = len(dyn & static) / len(dyn)
    rec = len(dyn & static) / len(static)
    print(f"\ndynamic↔static set örtüşmesi: dynamic'in %{prec*100:.1f}'i static'te; "
          f"static'in %{rec*100:.1f}'i dynamic'te (|∩|={len(inter)})")

    _plot(systems, results, bestK)


def _plot(systems, results, bestK, split: str = "TEST") -> None:
    """Sistemleri P/R/F1 (UPOS-proxy) üzerinden karşılaştıran gruplu bar grafiği."""
    labels = [n for n, _ in systems]
    rows = results[split]
    P = [r[1] for r in rows]; R = [r[2] for r in rows]; F = [r[3] for r in rows]
    import numpy as np
    x = np.arange(len(labels)); w = 0.26
    plt.figure(figsize=(8, 4.8))
    for i, (vals, name, col) in enumerate([(P, "Precision", "#16a34a"),
                                           (R, "Recall", "#dc2626"),
                                           (F, "F1", "#2563eb")]):
        bars = plt.bar(x + (i - 1) * w, vals, w, label=name, color=col)
        for b, v in zip(bars, vals):
            plt.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.2f}",
                     ha="center", va="bottom", fontsize=7)
    plt.xticks(x, labels); plt.ylim(0, 1.0); plt.ylabel("score")
    plt.title("Stopword lists: static vs dynamic")
    plt.legend(loc="lower right"); plt.grid(axis="y", alpha=0.3); plt.tight_layout()
    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / "stopword_system_comparison.png"
    plt.savefig(out, dpi=130)
    print(f"\nGörsel kaydedildi: {out}")


if __name__ == "__main__":
    main()
