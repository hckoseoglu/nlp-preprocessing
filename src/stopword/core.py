"""Stopword elimination — static + dynamic (Türkçe, genel domain). SAHİP: paylaşımlı.

- static: dış referans genel-domain liste (resources/, cite'lı).
- dynamic: korpustan (UD train, doküman = cümle) TF-IDF ile üretim.
  Yöntem: Achsan, Suhartanto, Wibowo, Dewi & Ismed (2023), "Automatic Extraction of
  Indonesian Stopwords", IJACSA 14(2). Düşük koleksiyon-TF-IDF'li kelimeler = stopword.
- değerlendirme: UPOS-proxy gold (kapalı-sınıf işlev sözcükleri) → token-level P/R/F1.
  Eşik (K) dev'de F1 ile seçilir. Bkz. CLAUDE.md.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from pathlib import Path

# UPOS kapalı-sınıf = stopword proxy gold
FUNCTION_POS = {"ADP", "AUX", "CCONJ", "SCONJ", "DET", "PRON", "PART"}


def tr_lower(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()


# --- Dynamic (TF-IDF, Achsan et al. 2023) ---------------------------------------

# UD-BOUN'da makale/doküman sınırı yok → ~CHUNK_SIZE cümleyi birleştirip pseudo-doküman
# yaparız (paper 6111 makale kullanmış; stopword "çoğu dokümanda" varsayımı ancak yeterince
# uzun dokümanlarda tutar — cümle granülerliğinde tf-idf bozuluyor).
CHUNK_SIZE = 20


class CorpusStats:
    """Her kelime için df, idf, koleksiyon-frekans ve koleksiyon-tf-idf tutar."""

    def __init__(self, N: int, df: dict[str, int], idf: dict[str, float],
                 freq: dict[str, int], tfidf: dict[str, float], chunk_size: int):
        self.N, self.df, self.idf, self.freq, self.tfidf = N, df, idf, freq, tfidf
        self.chunk_size = chunk_size


def _build_documents(sentences, chunk_size: int, shuffle: bool = True,
                     seed: int = 42) -> list[list[str]]:
    sent_toks = []
    for s in sentences:
        toks = [tr_lower(w.form) for w in s.words if w.form[:1].isalpha()]
        if toks:
            sent_toks.append(toks)
    if chunk_size <= 1:
        return sent_toks
    if shuffle:
        # BOUN'da ardışık cümleler aynı kaynaktan (bağımlı) → shuffle ile pseudo-dokümanları
        # bağımsız kıl; df/idf "kaç bağımsız dokümanda" anlamını korusun. Seed'li = reproducible.
        import random
        sent_toks = sent_toks[:]
        random.Random(seed).shuffle(sent_toks)
    docs = []
    for i in range(0, len(sent_toks), chunk_size):
        merged = [w for t in sent_toks[i:i + chunk_size] for w in t]
        if merged:
            docs.append(merged)
    return docs


def compute_stats(sentences, chunk_size: int = CHUNK_SIZE) -> CorpusStats:
    """Achsan et al. (2023) TF-IDF: doküman = ~chunk_size cümle.
    tf(w,d)=n/Σn ; df(w)=#doküman ; idf(w)=log(N/df) ; tfidf(w)=(Σ tf / df)*idf
    """
    docs = _build_documents(sentences, chunk_size)
    N = len(docs)
    df: Counter[str] = Counter()
    freq: Counter[str] = Counter()
    sum_tf: dict[str, float] = defaultdict(float)
    for toks in docs:
        counts = Counter(toks)
        total = len(toks)
        for w, c in counts.items():
            sum_tf[w] += c / total
            df[w] += 1
            freq[w] += c
    idf = {w: math.log(N / df[w]) for w in df}
    tfidf = {w: (sum_tf[w] / df[w]) * idf[w] for w in df}
    return CorpusStats(N, dict(df), idf, dict(freq), tfidf, chunk_size)


def dynamic_stopwords(stats: CorpusStats, k: int, by: str = "tfidf") -> set[str]:
    """En düşük skorlu K kelime = stopword (Achsan et al. 2023, tf-idf artan).
    by='idf' ablation için IDF-temelli varyant verir.
    """
    score = stats.tfidf if by == "tfidf" else stats.idf
    ranked = sorted(score, key=lambda w: score[w])  # artan: en düşük = stopword
    return set(ranked[:k])


# --- Static ----------------------------------------------------------------------

def load_static_stopwords(path: str | Path) -> set[str]:
    """resources/ altındaki dış genel-domain listeyi yükle (cite'lı)."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return {tr_lower(x.strip()) for x in lines if x.strip() and not x.startswith("#")}


# --- Eleme + değerlendirme -------------------------------------------------------

def remove_stopwords(tokens: list[str], stopwords: set[str]) -> list[str]:
    return [t for t in tokens if tr_lower(t) not in stopwords]


def evaluate_list(stopset: set[str], sentences) -> tuple[float, float, float]:
    """Token-level P/R/F1, gold = UPOS kapalı-sınıf (FUNCTION_POS)."""
    tp = fp = fn = 0
    for s in sentences:
        for w in s.words:
            if not w.form[:1].isalpha():
                continue
            pred = tr_lower(w.form) in stopset
            gold = w.upos in FUNCTION_POS
            if pred and gold:
                tp += 1
            elif pred and not gold:
                fp += 1
            elif not pred and gold:
                fn += 1
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1
