"""42bin_haber (büyük Türkçe haber korpusu) → dinamik TF-IDF stopword üretimi + değerlendirme.

Mevcut dinamik (TF-IDF) stopword yöntemimizi (Achsan et al. 2023; bkz. stopword/core.py)
~42.000 makalelik 42bin_haber korpusuna uygularız. BOUN'un aksine her makale ZATEN bağımsız
bir dokümandır → pseudo-doküman (chunk) ve shuffle GEREKMEZ (native-TF-IDF avantajı).

Üretilen listeyi üç yolla değerlendiririz:
  1) UPOS-proxy (BOUN test, kapalı-sınıf gold) → token-level P/R/F1  [core.evaluate_list]
  2) Bağımsız gold (ahmetax/trstop, 278 kelime) → type-level P/R/F1 ve BOUN-test token-P
  3) boun-dynamic-75 ↔ 42bin-dynamic-75 set örtüşmesi

Reprodüksiyon (proje kökünden, venv python ile):
    <venv>/bin/python3 src/scripts/stopword_build_42bin.py

VERİ İNDİRME (script otomatik dener; manuel gerekirse):
    curl -L -o /tmp/42bin.rar "http://www.kemik.yildiz.edu.tr/data/File/42bin_haber.rar"
    unar -o <SCRATCH>/42bin /tmp/42bin.rar       # 'brew install unar' gerekebilir
Beklenen ağaç: <EXTRACT_DIR>/42bin_haber/news/<kategori>/<id>.txt  (13 kategori, ~42k txt)

Yalnızca ekler: resources/stopwords_dynamic_42bin.txt, reports/stopword_42bin_comparison.png
"""
from __future__ import annotations

import math
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np               # noqa: E402

# --- proje kodunu yeniden kullan (TF-IDF formülünü yeniden tanımlamayız) --------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from io_conllu import read_conllu                                       # noqa: E402
from stopword.core import (compute_stats, dynamic_stopwords,            # noqa: E402
                           load_static_stopwords, evaluate_list, tr_lower)

# --- yollar ---------------------------------------------------------------------
RAR_URL = "http://www.kemik.yildiz.edu.tr/data/File/42bin_haber.rar"
RAR_PATH = Path("/tmp/42bin.rar")
# Ham veriyi repoya SOKMA → scratchpad altında tut.
SCRATCH = Path(os.environ.get(
    "SCRATCHPAD",
    "/private/tmp/claude-501/-Users-hikmetcankoseoglu-dev-nlp-preprocessing/"
    "181afc4d-32ac-4af1-8673-c43c09c39cd7/scratchpad"))
EXTRACT_DIR = SCRATCH / "42bin"
NEWS_DIR = EXTRACT_DIR / "42bin_haber" / "news"

DATA = PROJECT_ROOT / "data" / "UD_Turkish-BOUN"
RESOURCES = PROJECT_ROOT / "resources"
REPORTS = PROJECT_ROOT / "reports"
OUT_LIST = RESOURCES / "stopwords_dynamic_42bin.txt"
# Tam sıralama (284k tip, ~10MB) repoyu şişirmesin → scratchpad'e yaz (K burada tunable).
OUT_RANKING = EXTRACT_DIR / "stopwords_dynamic_42bin_full_ranking.tsv"
OUT_PNG = REPORTS / "stopword_42bin_comparison.png"
GOLD_PATH = RESOURCES / "stopwords_gold_ahmetax.txt"
STATIC_PATH = RESOURCES / "stopwords_tr.txt"

K = 75  # BOUN listesiyle adil karşılaştırma için
TOKEN_RE = re.compile(r"[^\W\d_]+", re.UNICODE)  # harf-dizileri (rakam/alt-çizgi/ünlem hariç)


# --- 1) veri indirme / açma -----------------------------------------------------

def ensure_data() -> Path:
    """42bin_haber/news ağacını garanti eder; yoksa indirir+açar. news dizinini döndürür."""
    if NEWS_DIR.is_dir() and any(NEWS_DIR.iterdir()):
        return NEWS_DIR
    if not RAR_PATH.exists():
        print(f"[indir] {RAR_URL} -> {RAR_PATH}")
        subprocess.run(["curl", "-L", "--connect-timeout", "30", "--max-time", "600",
                        "-o", str(RAR_PATH), RAR_URL], check=True)
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    unar = "unar" if subprocess.run(["which", "unar"], capture_output=True).returncode == 0 else None
    if unar is None:
        raise RuntimeError(
            "RAR açıcı yok. 'brew install unar' kurun ya da manuel açın:\n"
            f"  unar -o {EXTRACT_DIR} {RAR_PATH}")
    print(f"[aç] {RAR_PATH} -> {EXTRACT_DIR}")
    subprocess.run([unar, "-quiet", "-force-overwrite", "-output-directory",
                    str(EXTRACT_DIR), str(RAR_PATH)], check=True)
    if not (NEWS_DIR.is_dir() and any(NEWS_DIR.iterdir())):
        raise RuntimeError(f"Açma sonrası beklenen ağaç yok: {NEWS_DIR}")
    return NEWS_DIR


def read_article(path: Path) -> str:
    """Türkçe haber dosyasını dayanıklı oku (utf-8; bozuksa cp1254; son çare errors=replace)."""
    raw = path.read_bytes()
    for enc in ("utf-8", "cp1254"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def iter_documents(news_dir: Path):
    """Her .txt = BİR doküman. (kategori, token_listesi) üretir. Chunk/shuffle YOK."""
    for cat in sorted(p for p in news_dir.iterdir() if p.is_dir()):
        for fp in sorted(cat.iterdir()):
            if fp.suffix != ".txt":
                continue
            text = read_article(fp)
            toks = [tr_lower(m.group()) for m in TOKEN_RE.finditer(text)]
            if toks:
                yield cat.name, toks


# --- 2) native TF-IDF (bizim formülümüz; core.compute_stats'ı aynala) -----------

def compute_stats_articles(docs: list[list[str]]):
    """core.compute_stats ile AYNI formül, ama girdi ham makale-token listeleri
    (CoNLL-U Sentence değil). tf=count/doc_len ; df=#doküman ; idf=log(N/df) ;
    tfidf(w)=(Σ_j tf(w,d_j)/df(w))*idf(w). Artan tfidf = stopword.
    """
    N = len(docs)
    df: Counter[str] = Counter()
    freq: Counter[str] = Counter()
    sum_tf: dict[str, float] = defaultdict(float)
    total_tokens = 0
    for toks in docs:
        counts = Counter(toks)
        total = len(toks)
        total_tokens += total
        for w, c in counts.items():
            sum_tf[w] += c / total
            df[w] += 1
            freq[w] += c
    idf = {w: math.log(N / df[w]) for w in df}
    tfidf = {w: (sum_tf[w] / df[w]) * idf[w] for w in df}
    return N, dict(df), dict(freq), tfidf, total_tokens


def ranked_by_tfidf(tfidf: dict[str, float]) -> list[str]:
    return sorted(tfidf, key=lambda w: tfidf[w])  # artan: en düşük = stopword


# --- 3) değerlendirme yardımcıları ---------------------------------------------

def load_gold(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return {tr_lower(x.strip()) for x in lines if x.strip() and not x.startswith("#")}


def type_prf(pred: set[str], gold: set[str]) -> tuple[float, float, float]:
    inter = len(pred & gold)
    p = inter / len(pred) if pred else 0.0
    r = inter / len(gold) if gold else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def token_precision_vs_gold(stopset: set[str], gold: set[str], sentences) -> tuple[float, int, int]:
    """BOUN-test token-level precision: kaldırılan tokenlardan kaçı gold ∈ ?"""
    removed = good = 0
    for s in sentences:
        for w in s.words:
            if not w.form[:1].isalpha():
                continue
            if tr_lower(w.form) in stopset:
                removed += 1
                if tr_lower(w.form) in gold:
                    good += 1
    return (good / removed if removed else 0.0), good, removed


# --- 4) çıktılar ----------------------------------------------------------------

def save_list(path: Path, words: list[str], N: int, total_tokens: int, vocab: int) -> None:
    header = (
        "# Dinamik (TF-IDF) stopword listesi — 42bin_haber korpusu\n"
        f"# Korpus: 42bin_haber (Kemik/Yıldız Teknik Üniv.), {N} makale, "
        f"{total_tokens} token, {vocab} tip.\n"
        "# Yöntem: Achsan et al. (2023) koleksiyon-TF-IDF; her makale = bir doküman "
        "(native, chunk/shuffle yok).\n"
        f"# En düşük TF-IDF'li ilk {len(words)} kelime (artan sırada = en çok stopword).\n"
        "# UYARI (dürüst bulgu): büyük N (41992) + çok değişken makale uzunluğunda\n"
        "#   'en düşük TF-IDF = stopword' sezgisi BOZULUYOR. Gerçek stopword'lerin idf'i\n"
        "#   çökerken (ve: idf=0.17), uzun makalelerde 1 kez geçen nadir kelimeler en alta\n"
        "#   düşüyor → bu liste gerçek stopword değil, nadir uzun-kuyruk kelimelerdir.\n"
        "#   Ayrıntı/karşılaştırma: reports/stopword_42bin_comparison.png ve src/scripts/stopword_build_42bin.py.\n")
    path.write_text(header + "\n".join(words) + "\n", encoding="utf-8")


def save_ranking(path: Path, ranking: list[str], tfidf: dict[str, float],
                 df: dict[str, int], freq: dict[str, int]) -> None:
    lines = ["# rank\tword\ttfidf\tdf\tcollection_freq"]
    for i, w in enumerate(ranking):
        lines.append(f"{i}\t{w}\t{tfidf[w]:.8e}\t{df[w]}\t{freq[w]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot_comparison(rows: dict[str, dict], out: Path) -> None:
    """boun-dynamic-75 vs 42bin-dynamic-75 (+static-467): 3 metrik gruplu bar."""
    metrics = [("UPOS-proxy F1\n(BOUN test)", "upos_f1"),
               ("ahmetax token-P\n(BOUN test)", "ahmetax_token_p"),
               ("ahmetax type-F1", "ahmetax_type_f1")]
    systems = [("boun-dynamic-75", "#2563eb"),
               ("42bin-dynamic-75", "#16a34a"),
               ("static-467", "#9ca3af")]
    x = np.arange(len(metrics))
    w = 0.26
    plt.figure(figsize=(9, 5.2))
    for i, (name, col) in enumerate(systems):
        vals = [rows[name][key] for _, key in metrics]
        bars = plt.bar(x + (i - 1) * w, vals, w, label=name, color=col)
        for b, v in zip(bars, vals):
            plt.text(b.get_x() + b.get_width() / 2, v + 0.012, f"{v:.3f}",
                     ha="center", va="bottom", fontsize=7.5)
    plt.xticks(x, [m for m, _ in metrics])
    plt.ylim(0, 1.0)
    plt.ylabel("skor")
    plt.title("BOUN vs 42bin_haber dynamic stopword — karşılaştırma")
    plt.legend(loc="upper right")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout(rect=(0, 0.06, 1, 1))
    plt.figtext(0.5, 0.01,
                "42bin-dynamic-75 (en düşük TF-IDF) tüm metriklerde 0.000: büyük N + değişken "
                "makale uzunluğu 'düşük TF-IDF = stopword' sezgisini bozar;\nliste nadir uzun-kuyruk "
                "kelimelere dejenere olur. Korpus sağlam — frekans/IDF ile sıralama gerçek "
                "stopword'leri geri getirir (bkz. rapor).",
                ha="center", va="bottom", fontsize=7, color="#b91c1c")
    REPORTS.mkdir(exist_ok=True)
    plt.savefig(out, dpi=130)
    print(f"[görsel] kaydedildi: {out}")


# --- main -----------------------------------------------------------------------

def main() -> None:
    news_dir = ensure_data()

    print("[korpus] makaleler okunuyor (her .txt = bir doküman)...")
    docs: list[list[str]] = []
    cat_counts: Counter[str] = Counter()
    for cat, toks in iter_documents(news_dir):
        docs.append(toks)
        cat_counts[cat] += 1

    N, df, freq, tfidf, total_tokens = compute_stats_articles(docs)
    vocab = len(tfidf)
    ranking = ranked_by_tfidf(tfidf)
    dyn42 = set(ranking[:K])

    print("\n===== 42bin_haber korpus istatistikleri =====")
    print(f"makale (doküman) sayısı : {N}")
    print(f"toplam token            : {total_tokens}")
    print(f"vocabulary (tip) sayısı : {vocab}")
    print("kategori dağılımı       : " +
          ", ".join(f"{c}={n}" for c, n in sorted(cat_counts.items())))

    print("\n===== en düşük TF-IDF'li ilk 40 kelime (42bin dynamic) =====")
    for i, w in enumerate(ranking[:40]):
        print(f"{i+1:>2}. {w:<16} tfidf={tfidf[w]:.3e}  df={df[w]:>6}  freq={freq[w]:>7}")

    save_list(OUT_LIST, ranking[:K], N, total_tokens, vocab)
    save_ranking(OUT_RANKING, ranking, tfidf, df, freq)
    print(f"\n[liste] kaydedildi: {OUT_LIST}  (K={K})")
    print(f"[tam sıralama] kaydedildi: {OUT_RANKING}")

    # --- karşılaştırma setleri ---
    train = read_conllu(DATA / "tr_boun-ud-train.conllu")
    test = read_conllu(DATA / "tr_boun-ud-test.conllu")
    boun_stats = compute_stats(train)
    boun75 = dynamic_stopwords(boun_stats, K)
    static467 = load_static_stopwords(STATIC_PATH)
    gold = load_gold(GOLD_PATH)
    print(f"\n[gold] ahmetax referans: {len(gold)} kelime | static: {len(static467)}")

    lists = {"boun-dynamic-75": boun75,
             "42bin-dynamic-75": dyn42,
             "static-467": static467}

    rows: dict[str, dict] = {}
    for name, L in lists.items():
        up, ur, uf = evaluate_list(L, test)
        tp, tr, tf = type_prf(L, gold)
        tok_p, good, removed = token_precision_vs_gold(L, gold, test)
        rows[name] = dict(size=len(L), upos_p=up, upos_r=ur, upos_f1=uf,
                          ahmetax_type_p=tp, ahmetax_type_r=tr, ahmetax_type_f1=tf,
                          ahmetax_token_p=tok_p, token_good=good, token_removed=removed)

    overlap = len(boun75 & dyn42)
    overlap_pct = overlap / K * 100

    # --- tablo ---
    print("\n===== SONUÇ TABLOSU =====")
    hdr = (f"{'liste':<18}{'|L|':>5}{'UPOS-P':>8}{'UPOS-R':>8}{'UPOS-F1':>8}"
           f"{'axType-P':>10}{'axType-R':>10}{'axType-F1':>11}{'axTok-P':>9}")
    print(hdr)
    print("-" * len(hdr))
    for name in lists:
        r = rows[name]
        print(f"{name:<18}{r['size']:>5}{r['upos_p']:>8.3f}{r['upos_r']:>8.3f}"
              f"{r['upos_f1']:>8.3f}{r['ahmetax_type_p']:>10.3f}{r['ahmetax_type_r']:>10.3f}"
              f"{r['ahmetax_type_f1']:>11.3f}{r['ahmetax_token_p']:>9.3f}")
    print(f"\nboun-dynamic-75 ∩ 42bin-dynamic-75 = {overlap}/{K} = %{overlap_pct:.1f} örtüşme")
    print("ortak kelimeler:", ", ".join(sorted(boun75 & dyn42)))

    plot_comparison(rows, OUT_PNG)
    assert OUT_PNG.exists(), f"PNG oluşmadı: {OUT_PNG}"
    print(f"[doğrulama] {OUT_PNG} mevcut ({OUT_PNG.stat().st_size} byte)")


if __name__ == "__main__":
    main()
