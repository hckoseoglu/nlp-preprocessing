"""Stopword listelerinin EKSTRİNSİK (downstream) değerlendirmesi.

Amaç: TF-IDF ile ürettiğimiz DİNAMİK stopword listesinin, downstream bir
5-tür (ins/bio/pop/ess/news) metin-sınıflandırma görevinde baseline'lara
(frekans, statik) karşı rekabetçi olup olmadığını ÖLÇMEK — yani yöntemi
değerlendirmek, salt "stopword var/yok" değil.

Her koşulda o koşulun stopword kümesi her cümlenin token listesinden çıkarılır,
kalan tokenlar boşlukla birleştirilip TfidfVectorizer + LogisticRegression ile
sınıflandırılır. Sayılar TEST split'inde raporlanır; her şey TRAIN'den fit edilir.

Kullanım (proje kökünden, venv python ile):
    <venv>/bin/python3 src/scripts/stopword_extrinsic.py
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import accuracy_score, f1_score  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from io_conllu import read_conllu  # noqa: E402
from stopword.core import (  # noqa: E402
    compute_stats,
    dynamic_stopwords,
    load_static_stopwords,
    remove_stopwords,
    tr_lower,
)

DATA = ROOT / "data" / "UD_Turkish-BOUN"
REPORTS = ROOT / "reports"
STATIC_PATH = ROOT / "resources" / "stopwords_tr.txt"
K = 75  # CLAUDE.md ile karşılaştırılabilirlik için sabit


def genre_of(sent_id: str) -> str:
    """sent_id'nin son alt-çizgiden önceki alfabetik ön-eki = tür etiketi."""
    return sent_id.rsplit("_", 1)[0]


def sentence_tokens(sentence) -> list[str]:
    """Gold tokenlar: Türkçe-küçük-harf, yalnızca alfabetik başlayanlar."""
    return [tr_lower(w.form) for w in sentence.words if w.form[:1].isalpha()]


def build_dataset(sentences):
    """(token_listeleri, etiketler) döndürür — cümle başına bir örnek."""
    toks = [sentence_tokens(s) for s in sentences]
    labels = [genre_of(s.sent_id) for s in sentences]
    return toks, labels


def to_strings(token_lists, stopset: set[str]) -> list[str]:
    """Her cümleden stopword'leri çıkar, kalanı boşlukla birleştir (boş cümle -> '')."""
    return [" ".join(remove_stopwords(toks, stopset)) for toks in token_lists]


def evaluate_condition(name, stopset, train_toks, y_train, test_toks, y_test,
                       total_train_tokens):
    """Tek bir koşulu değerlendir, metrik sözlüğü döndür."""
    X_train_str = to_strings(train_toks, stopset)
    X_test_str = to_strings(test_toks, stopset)

    vec = TfidfVectorizer(
        analyzer="word",
        token_pattern=r"(?u)\b\w+\b",
        lowercase=False,  # tokenlar zaten küçük harf
    )
    X_train = vec.fit_transform(X_train_str)
    X_test = vec.transform(X_test_str)

    clf = LogisticRegression(max_iter=2000)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    # token_reduction: TRAIN'de bu listeyle çıkarılan token oranı
    removed = sum(1 for toks in train_toks for t in toks if tr_lower(t) in stopset)
    token_reduction_pct = (
        100.0 * removed / total_train_tokens if total_train_tokens else 0.0
    )

    return {
        "condition": name,
        "accuracy": accuracy_score(y_test, y_pred),
        "macro_f1": f1_score(y_test, y_pred, average="macro"),
        "vocab_size": len(vec.vocabulary_),
        "token_reduction_pct": token_reduction_pct,
        "list_size": len(stopset),
    }


def main() -> None:
    train = read_conllu(f"{DATA}/tr_boun-ud-train.conllu")
    test = read_conllu(f"{DATA}/tr_boun-ud-test.conllu")

    train_toks, y_train = build_dataset(train)
    test_toks, y_test = build_dataset(test)

    total_train_tokens = sum(len(t) for t in train_toks)

    # --- Stopword kümeleri (hepsi yalnızca TRAIN'den) ---
    # 2) frekans baseline: TRAIN'deki en sık 75 alfabetik tip (Counter)
    freq_counter: Counter[str] = Counter(t for toks in train_toks for t in toks)
    freq_top75 = {w for w, _ in freq_counter.most_common(K)}

    # 3) bizim yöntem: dynamic TF-IDF, K=75
    stats = compute_stats(train)
    dynamic_75 = dynamic_stopwords(stats, K)

    # 4) statik dış liste
    static_467 = load_static_stopwords(STATIC_PATH)

    # 5) birleşim
    union = dynamic_75 | static_467

    conditions = [
        ("no-removal", set()),
        ("freq-top75", freq_top75),
        ("dynamic-75", dynamic_75),
        ("static-467", static_467),
        ("union", union),
    ]

    results = []
    for name, stopset in conditions:
        results.append(
            evaluate_condition(
                name, stopset, train_toks, y_train, test_toks, y_test,
                total_train_tokens,
            )
        )

    _print_table(results, total_train_tokens)
    _plot(results)


def _print_table(results, total_train_tokens) -> None:
    print(f"\nTRAIN cümle sayısı: toplam token (no-removal) = {total_train_tokens}")
    print("\n=== EKSTRİNSİK: 5-tür sınıflandırma (TEST) ===")
    header = (
        f"{'condition':12}{'accuracy':>10}{'macro_f1':>10}"
        f"{'vocab_size':>12}{'tok_red_%':>11}{'list_size':>11}"
    )
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r['condition']:12}{r['accuracy']:10.4f}{r['macro_f1']:10.4f}"
            f"{r['vocab_size']:12d}{r['token_reduction_pct']:11.2f}"
            f"{r['list_size']:11d}"
        )


def _plot(results) -> None:
    labels = [r["condition"] for r in results]
    acc = [r["accuracy"] for r in results]
    f1 = [r["macro_f1"] for r in results]

    x = np.arange(len(labels))
    w = 0.38
    plt.figure(figsize=(9, 5))
    bars_acc = plt.bar(x - w / 2, acc, w, label="accuracy", color="#2563eb")
    bars_f1 = plt.bar(x + w / 2, f1, w, label="macro_f1", color="#f59e0b")
    for bars, vals in ((bars_acc, acc), (bars_f1, f1)):
        for b, v in zip(bars, vals):
            plt.text(b.get_x() + b.get_width() / 2, v + 0.008, f"{v:.3f}",
                     ha="center", va="bottom", fontsize=8)
    plt.xticks(x, labels)
    plt.ylim(0, 1.0)
    plt.ylabel("score")
    plt.title("Effect of stopword lists on genre classification")
    plt.legend(loc="lower right")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / "stopword_extrinsic.png"
    plt.savefig(out, dpi=130)
    print(f"\nGörsel kaydedildi: {out}")


if __name__ == "__main__":
    main()
