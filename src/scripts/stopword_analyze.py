"""Dynamic stopword analizi (Achsan et al. 2023 TF-IDF, pseudo-doküman = ~20 cümle).

- K-vs-F1 taraması (dev, UPOS-proxy gold) → K* seçimi
- tf-idf dağılımı görseli (asıl metrik; stopword'ler en düşük uçta)
- ablation: tf-idf vs idf (dürüst karşılaştırma)
Çıktı: reports/stopword_k_vs_f1.png, reports/stopword_tfidf_curve.png
Kullanım: python3 src/scripts/stopword_analyze.py   (proje kökünden)
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from io_conllu import read_conllu                                      # noqa: E402
from stopword import compute_stats, dynamic_stopwords, evaluate_list   # noqa: E402

DATA = ROOT / "data" / "UD_Turkish-BOUN"
REPORTS = ROOT / "reports"
KS = list(range(25, 1001, 25))


def sweep(stats, dev, by):
    P, R, F = [], [], []
    for k in KS:
        p, r, f = evaluate_list(dynamic_stopwords(stats, k, by=by), dev)
        P.append(p); R.append(r); F.append(f)
    i = max(range(len(KS)), key=lambda j: F[j])
    return P, R, F, KS[i], F[i]


def main() -> None:
    train = read_conllu(f"{DATA}/tr_boun-ud-train.conllu")
    dev = read_conllu(f"{DATA}/tr_boun-ud-dev.conllu")

    stats = compute_stats(train)
    print(f"train: {stats.N} pseudo-doküman ({stats.chunk_size} cümle/dok), "
          f"{len(stats.tfidf)} benzersiz kelime")

    ranked = sorted(stats.tfidf, key=lambda w: stats.tfidf[w])
    print("\nEn düşük TF-IDF (stopword adayları) ilk 25:")
    print("  " + ", ".join(ranked[:25]))

    # Ablation: tf-idf vs idf
    P, R, F, bestK, bestF = sweep(stats, dev, "tfidf")
    _, _, Fi, bestKi, bestFi = sweep(stats, dev, "idf")
    bi = KS.index(bestK)
    print(f"\n[tf-idf] en iyi K={bestK}  F1={bestF:.3f}  P={P[bi]:.3f}  R={R[bi]:.3f}")
    print(f"[idf   ] en iyi K={bestKi} F1={bestFi:.3f}  (ablation karşılaştırması)")

    REPORTS.mkdir(exist_ok=True)

    # Grafik 1: K vs P/R/F1 (tf-idf)
    plt.figure(figsize=(7, 4.5))
    plt.plot(KS, F, "-o", ms=3, label="F1", color="#2563eb")
    plt.plot(KS, P, "--", label="Precision", color="#16a34a")
    plt.plot(KS, R, "--", label="Recall", color="#dc2626")
    plt.axvline(bestK, color="gray", ls=":", lw=1)
    plt.scatter([bestK], [bestF], color="#2563eb", zorder=5)
    plt.annotate(f"K*={bestK}\nF1={bestF:.3f}", (bestK, bestF),
                 textcoords="offset points", xytext=(10, -5), fontsize=9)
    plt.xlabel("K (dynamic list size)"); plt.ylabel("score")
    plt.title("Dynamic stopwords (TF-IDF): K vs P/R/F1")
    plt.legend(); plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(REPORTS / "stopword_k_vs_f1.png", dpi=130)

    # Grafik 2: tf-idf dağılımı
    scores = [stats.tfidf[w] for w in ranked]
    plt.figure(figsize=(7, 4.5))
    plt.plot(range(1, len(scores) + 1), scores, color="#7c3aed", lw=1)
    plt.axvline(bestK, color="gray", ls=":", lw=1)
    plt.annotate(f"K*={bestK}", (bestK, scores[min(bestK, len(scores) - 1)]),
                 textcoords="offset points", xytext=(8, 14), fontsize=9)
    plt.xlabel("word rank (ascending TF-IDF)"); plt.ylabel("TF-IDF")
    plt.title("TF-IDF distribution")
    plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(REPORTS / "stopword_tfidf_curve.png", dpi=130)

    print(f"\nGörseller: {REPORTS}/stopword_k_vs_f1.png, {REPORTS}/stopword_tfidf_curve.png")


if __name__ == "__main__":
    main()
