"""Gerçek gürültülü test setleri — normalization değerlendirmesi (yalnızca TEST; ayar yapılmaz).

SAHİP: Ecem
  - MultiLexNorm Türkçe **test** (tweet'ler, elle normalize): Çolakoğlu, Sulubacak & Tantuğ (2019),
    ACL SRW; van der Goot et al. (2021), W-NUT. Lexicon train bölümünden üretildi (norm_build_lexicon.py).
  - OSCAR-GEC **test** (web metni: haber parçası, forum, ürün yorumu...; elle düzeltilmiş):
    Ersoy & Yıldız (2024), arXiv:2405.15320;
    https://huggingface.co/datasets/asimokby/Turkish-GEC-Evaluation (MIT). Gramer düzeltme (GEC)
    verisi: M2 biçiminde cümle + düzeltme listesi.
Her iki set (gürültülü tokenlar, doğru biçimler) cümlelerine çevrilir; doğru biçim None olan token
puanlanmaz. Puanlama kuralları sonuçlara bakılmadan sabitlendi (CLAUDE.md, 2026-10-18):
  ortak       : harf içermeyen token, @mention, #hashtag, URL puanlanmaz (normalizer bunlara dokunmaz)
  MultiLexNorm: birleştirme (2+ token -> 1 kelime) parçaları puanlanmaz; bölme (yokmu -> yok mu)
                puanlanır
  OSCAR-GEC   : düzeltilmemiş tokenlar puanlanır. Bir kaynak tokene dokunan düzeltme, iki taraftaki
                ayrı noktalama tokenları atıldıktan sonra (a) yalnızca büyük/küçük harf, Türkçe
                karakter ya da kelime bölme farkıysa (etiketten bağımsız; "o -> . O" dahil) veya
                (b) tek kelime -> tek kelime olup etiketi SPELL/ORTH/OTHER ve ASCII-katlanmış
                Damerau-Levenshtein uzaklığı <= 2 ise puanlanır. Dilbilgisi (NOUN/VERB/...), kelime
                değişimi/ekleme, birleştirme ve silme düzeltmelerinin dokunduğu tokenlar puanlanmaz.
                Çoklu token düzeltmesi kelime sayısı eşitse kelime kelime değerlendirilir.
İndirilen veri data/external/ altında tutulur (git'e girmez).

Kullanım:  python src/real_data.py   (iki setin özeti: cümle, token, puanlanan, dışarıda kalan)
"""
from __future__ import annotations

import json
import time
import urllib.request
from collections import Counter
from pathlib import Path

from noise import is_word
from normalization import to_ascii, turkish_lower

_ROOT = Path(__file__).resolve().parent.parent
_EXTERNAL = _ROOT / "data" / "external"
_MLN_URL = ("https://datasets-server.huggingface.co/rows?dataset=robvanderg%2FMultiLexNorm"
            "&config=tur&split={split}&offset={offset}&length=100")
_OSCAR_URL = ("https://huggingface.co/datasets/asimokby/Turkish-GEC-Evaluation/resolve/main/"
              "oscar_gec_m2_W_MAPPED_LABELS.txt")
_OSCAR_FILE = _EXTERNAL / "oscar_gec" / "oscar_gec_m2.txt"
_SPELLING_LABELS = {"SPELL", "ORTH", "OTHER"}
_MAX_DIST = 2


def _fetch(url: str, retries: int = 4, timeout: float = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (CMPE561 course project)"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except OSError:
            if attempt == retries - 1:
                raise
            time.sleep(5 * 2 ** attempt)     # 5, 10, 20 sn bekle
    raise OSError(url)


def scorable(token: str) -> bool:
    """Puanlanabilir token: harf içerir ve @mention / #hashtag / URL değildir."""
    return is_word(token) and not token.startswith(("@", "#")) and "://" not in token


# --- MultiLexNorm (tweet) ------------------------------------------------------------

def load_multilexnorm(split: str = "test") -> list[list[tuple[str, str]]]:
    """MultiLexNorm Türkçe cümleleri: (ham, normalize) token çiftleri; önbellekten ya da indirerek."""
    cache = _EXTERNAL / f"multilexnorm_tur_{split}.json"
    if not cache.exists():
        rows, offset = [], 0
        while True:
            page = json.loads(_fetch(_MLN_URL.format(split=split, offset=offset)).decode("utf-8"))
            rows += [r["row"] for r in page["rows"]]
            offset += 100
            if offset >= page["num_rows_total"]:
                break
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    rows = json.loads(cache.read_text(encoding="utf-8"))
    return [list(zip(r["orig"], r["norm"])) for r in rows]


def multilexnorm_sentences(split: str = "test") -> list[tuple[list[str], list[str | None]]]:
    """(gürültülü tokenlar, doğru biçimler); birleştirme parçalarının doğrusu None (puanlanmaz)."""
    out = []
    for sent in load_multilexnorm(split):
        gold: list[str | None] = []
        for i, (_, norm) in enumerate(sent):
            merged = norm == "" or (i + 1 < len(sent) and sent[i + 1][1] == "")
            gold.append(None if merged else norm)
        out.append(([o for o, _ in sent], gold))
    return out


# --- OSCAR-GEC (web metni) -------------------------------------------------------------

def _fold(text: str) -> str:
    return to_ascii(turkish_lower(text))


def _osa_distance(a: str, b: str) -> int:
    """Damerau-Levenshtein uzaklığı (optimal string alignment: sil/ekle/değiştir/yer değiştir)."""
    prev2: list[int] = []
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        prev2, prev = prev, cur
    return prev[len(b)]


def _has_alnum(token: str) -> bool:
    return any(c.isalnum() for c in token)


def _is_normalization(src: str, corr: str, label: str) -> bool:
    """Tek tokenin düzeltmesi (corr birden çok kelime olabilir) normalization kapsamında mı?"""
    a, b = _fold(src), _fold(corr.replace(" ", ""))
    if a == b:      # yalnızca büyük/küçük harf, Türkçe karakter ya da kelime bölme farkı
        return True
    # typo: yalnız tek kelime -> tek kelime (bölmede uzaklığa izin verilirse eklenen kelimeler,
    # ör. "calisiyor -> çalışıyor ve", kapsama girerdi)
    return " " not in corr and label in _SPELLING_LABELS and _osa_distance(a, b) <= _MAX_DIST


def load_oscar_gec() -> list[tuple[list[str], list[tuple[int, int, str, str]]]]:
    """M2 dosyası: her cümle için (tokenlar, [(başlangıç, bitiş, tür, düzeltme)]); gerekirse indirir."""
    if not _OSCAR_FILE.exists():
        _OSCAR_FILE.parent.mkdir(parents=True, exist_ok=True)
        _OSCAR_FILE.write_bytes(_fetch(_OSCAR_URL))
    sents: list[tuple[list[str], list[tuple[int, int, str, str]]]] = []
    for line in _OSCAR_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("S "):
            sents.append((line[2:].split(), []))
        elif line.startswith("A ") and sents:
            span, kind, corr = line[2:].split("|||")[:3]
            start, end = map(int, span.split())
            if kind != "noop":
                sents[-1][1].append((start, end, kind, corr))
    return sents


def oscar_gec_sentences(stats: Counter | None = None) -> list[tuple[list[str], list[str | None]]]:
    """(gürültülü tokenlar, doğru biçimler); kapsam dışı düzeltmelerin dokunduğu tokenlar None.
    `stats` verilirse token sayıları neden bazında oraya eklenir."""
    out = []
    for toks, edits in load_oscar_gec():
        gold: list[str | None] = list(toks)
        status = ["düzeltilmemiş"] * len(toks)
        for start, end, kind, corr in edits:
            if start == end:            # ekleme (eksik virgül/kelime): kaynakta token yok
                continue
            # iki taraftaki ayrı noktalama tokenları atılır: "o -> . O" (nokta eklenmiş + büyük
            # harf) kelime açısından yalnızca büyük/küçük harf düzeltmesidir
            words = [] if corr == "-NONE-" else [w for w in corr.split() if _has_alnum(w)]
            idx = [k for k in range(start, end) if _has_alnum(toks[k])]
            label = kind[2:].split(":")[0].split("-")[0]
            if len(idx) == 1 and words and _is_normalization(toks[idx[0]], " ".join(words), label):
                pairs = [(idx[0], " ".join(words))]
            elif len(idx) > 1 and len(words) == len(idx) and \
                    all(_is_normalization(toks[k], w, label) for k, w in zip(idx, words)):
                pairs = list(zip(idx, words))
            else:
                pairs = []
            for k in range(start, end):         # önce hepsi kapsam dışı, sonra kapsamdakiler
                gold[k], status[k] = None, "kapsam dışı düzeltme"
            for k, w in pairs:
                gold[k], status[k] = w, "düzeltilmiş (kapsamda)"
        if stats is not None:
            for t, s in zip(toks, status):
                stats[s if scorable(t) else "harf yok / @ # URL"] += 1
        out.append((toks, gold))
    return out


if __name__ == "__main__":
    for name, sents in (("MultiLexNorm test", multilexnorm_sentences("test")),):
        n_tok = sum(len(t) for t, _ in sents)
        scored = sum(g is not None and scorable(t) for ts, gs in sents for t, g in zip(ts, gs))
        print(f"{name}: {len(sents)} cümle, {n_tok} token, puanlanan {scored}")
    stats: Counter[str] = Counter()
    sents = oscar_gec_sentences(stats)
    print(f"OSCAR-GEC test: {len(sents)} cümle, {sum(stats.values())} token")
    for k, v in stats.most_common():
        print(f"  {k:<26} {v}")
