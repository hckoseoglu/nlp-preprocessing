"""Normalization lexicon'unu akademik bir kaynaktan üretir.

SAHİP: Ecem
Kaynak: MultiLexNorm Türkçe **train** bölümü (gerçek tweet'ler + elle yapılmış normalizasyon):
  - Çolakoğlu, Sulubacak, Tantuğ (2019). Normalizing Non-canonical Turkish Texts Using Machine
    Translation Approaches. ACL 2019 Student Research Workshop. (veri)
  - van der Goot et al. (2021). MultiLexNorm: A Shared Task on Multilingual Lexical
    Normalization. W-NUT 2021. (veri setinin ortak biçimi; https://huggingface.co/datasets/robvanderg/MultiLexNorm)
Test bölümüne dokunulmaz (ileride gerçek gürültülü test seti olarak kullanılabilsin).

Seçim kuralları (her biri normalizer'ın başka bir adımı zaten çözüyorsa ya da belirsizse eler):
  1. Yalnızca "sözcüksel" düzeltmeler: sadece büyük/küçük harf, sadece Türkçe karakter, sadece harf
     tekrarı olan düzeltmeler ve birleştirmeler alınmaz (normalizer bunları kendisi yapıyor).
  2. Ham form en az 2 harf ve yalnızca harflerden oluşur (h -> hayır/hafta gibi belirsizlik yok).
  3. Kaynakta belirsiz değil: ham form hep aynı biçime düzeltilmiş, hiç olduğu gibi bırakılmamış.
  4. Ham form doğru bir kelimeyle karışmaz: (a) kendisi ya da Türkçe karaktersiz hâli UD train'de
     (editörlü temiz metin) sık geçen bir kelime değil (< 3 kez; olum -> ölüm), (b) kelime bölme
     girişinde UD'de hiç geçmez (bende -> ben de / bende), (c) geçerli bir kelimeye benziyorsa
     (UD'de var ya da kök + ek olarak açıklanabiliyor: kader, halayda) kaynakta en az 2 kez görülmüş.
  5. Birleştirme (merge) başı olan tokenlar alınmaz (gire + bilir -> "girebilir miyim").
  6. Yaygın olmalı (plan: "yaygın yazım-hata lexicon'u"): en az 2 FARKLI tweet'te görülmüş; tek
     kişinin tek seferlik hatası (bipgi -> bilgi) ya da tek tweet'e özgü kelime alınmaz.
  7. Ham form yalnızca Türk alfabesindeki harflerden oluşur (αcı, чαşαmış gibi süs yazımlar yok).
  8. Küfür/hakaret içeren girişler alınmaz (genel alan / haber dili için gereksiz).
  9. Kelime ortasında büyük harf olan ham formlar alınmaz: '#' işareti düşmüş hashtag'lerdir
     (MaliyeAtama, SırasıTarımda -> tek bir kampanyaya özgü, genel Türkçe değil).
Doğrulama: düzeltilmiş biçimin her kelimesi UD-BOUN train'de ya da TDK Güncel Türkçe Sözlük'te
(https://sozluk.gov.tr) bulunmalı. Bulunamayanlar "#?" ile yorum satırı olarak yazılır (elle kontrol).

Kullanım:  python src/scripts/norm_build_lexicon.py [--no-tdk]
İndirilen veri ve TDK sorgu önbelleği data/external/ altında tutulur (git'e girmez).
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # src/ (kütüphane modülleri)
from io_conllu import iter_conllu  # noqa: E402
from normalization import _RUN3, _WORD, Normalizer, canonical, to_ascii, turkish_lower

_ROOT = Path(__file__).resolve().parents[2]   # proje kökü (src/scripts/ → ../..)
_TRAIN = _ROOT / "data" / "UD_Turkish-BOUN" / "tr_boun-ud-train.conllu"
_CACHE = _ROOT / "data" / "external"
_OUT = _ROOT / "resources" / "normalization_lexicon.tsv"
_MLN_URL = ("https://datasets-server.huggingface.co/rows?dataset=robvanderg%2FMultiLexNorm"
            "&config=tur&split=train&offset={offset}&length=100")
_TDK_URL = "https://sozluk.gov.tr/gts?ara={word}"
_MIN_TWEETS = 2                                            # kural 6
_TR_ALPHABET = set("abcçdefgğhıijklmnoöprsştuüvyzâîû'")    # kural 7
_PROFANITY = {"orospu", "amına", "sik", "siktir", "piç", "göt", "ananı"}   # kural 8
_CAMEL = re.compile(r"[a-zçğıöşü][A-ZÇĞİÖŞÜ]")                              # kural 9


def _get_json(url: str, retries: int = 4, timeout: float = 15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (CMPE561 course project)"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (OSError, ValueError):
            if attempt == retries - 1:
                raise
            time.sleep(5 * 2 ** attempt)     # 5, 10, 20 sn bekle (sunucuyu yormamak için)


def load_multilexnorm_train() -> list[list[tuple[str, str]]]:
    """MultiLexNorm Türkçe train cümleleri: (ham, normalize) token çiftleri; önbellekten ya da
    indirerek."""
    cache = _CACHE / "multilexnorm_tur_train.json"
    if not cache.exists():
        rows, offset = [], 0
        while True:
            page = _get_json(_MLN_URL.format(offset=offset))
            rows += [r["row"] for r in page["rows"]]
            offset += 100
            if offset >= page["num_rows_total"]:
                break
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    rows = json.loads(cache.read_text(encoding="utf-8"))
    return [list(zip(r["orig"], r["norm"])) for r in rows]


def _collapse(s: str) -> str:
    return _RUN3.sub(r"\1", s)


def _is_lexical(raw: str, norm: str) -> bool:
    """Kural 1: düzeltme normalizer'ın diğer adımlarıyla açıklanamıyor mu?"""
    if not norm or raw == norm:
        return False
    if to_ascii(raw) == to_ascii(norm):                       # yalnızca Türkçe karakter
        return False
    if to_ascii(_collapse(raw)) == to_ascii(norm):            # harf tekrarı (+ karakter)
        return False
    return True


def select_pairs(sentences: list[list[tuple[str, str]]], ud_freq: Counter,
                 normalizer: Normalizer) -> dict[str, tuple[str, int]]:
    """Kural 1-8'e göre lexicon girişlerini seçer: ham -> (doğru, görüldüğü tweet sayısı)."""
    fixes: dict[str, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
    unchanged: Counter[str] = Counter()
    camel: set[str] = set()
    for sid, sent in enumerate(sentences):
        for i, (o, n) in enumerate(sent):
            raw, norm = turkish_lower(o), turkish_lower(n)
            if _CAMEL.search(o):
                camel.add(raw)
            if raw == norm:
                unchanged[raw] += 1
            elif i + 1 < len(sent) and sent[i + 1][1] == "":                # kural 5
                continue
            elif _is_lexical(raw, norm):
                fixes[raw][norm].add(sid)

    key_max = Counter()   # ASCII anahtar -> o anahtara inen en sık UD kelimesinin sıklığı
    for w, f in ud_freq.items():
        key_max[to_ascii(w)] = max(key_max[to_ascii(w)], f)

    def looks_valid(raw: str) -> bool:
        return (ud_freq[raw] > 0 or normalizer._word_logp(raw, True) is not None
                or normalizer._word_logp(to_ascii(raw), False) is not None)

    selected = {}
    for raw, options in fixes.items():
        if len(raw) < 2 or not _WORD.match(raw):                          # kural 2
            continue
        if len(options) > 1 or unchanged[raw]:                             # kural 3
            continue
        norm, tweets = next(iter(options.items()))
        count = len(tweets)
        if count < _MIN_TWEETS:                                            # kural 6
            continue
        if not set(raw) <= _TR_ALPHABET:                                   # kural 7
            continue
        if _PROFANITY & set(norm.split(" ")):                              # kural 8
            continue
        if raw in camel:                                                   # kural 9
            continue
        if key_max[to_ascii(raw)] >= 3:                                    # kural 4a
            continue
        if " " in norm and ud_freq[raw] > 0:                               # kural 4b
            continue
        if count < 2 and looks_valid(raw):                                 # kural 4c
            continue
        if not all(_WORD.match(part) for part in norm.split(" ")):
            continue
        selected[raw] = (norm, count)
    return selected


def tdk_has(word: str, cache: dict[str, bool], delay: float = 1.0) -> bool | None:
    """TDK Güncel Türkçe Sözlük'te madde olarak var mı? Sonuç önbelleğe yazılır; sunucuya
    ulaşılamazsa None (önbelleğe yazılmaz, bir sonraki çalıştırmada tekrar sorulur)."""
    if word not in cache:
        try:
            data = _get_json(_TDK_URL.format(word=urllib.parse.quote(word)))
        except (OSError, ValueError):
            return None
        finally:
            time.sleep(delay)
        cache[word] = isinstance(data, list) and len(data) > 0
    return cache[word]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-tdk", action="store_true", help="TDK sorgusu yapma (yalnızca UD doğrulaması)")
    args = ap.parse_args()

    ud_freq: Counter[str] = Counter(canonical(t.form) for s in iter_conllu(_TRAIN) for t in s.tokens)
    sentences = load_multilexnorm_train()
    n_tokens = sum(len(s) for s in sentences)
    selected = select_pairs(sentences, ud_freq, Normalizer(lexicon=False))

    tdk_cache_path = _CACHE / "tdk_gts_cache.json"
    tdk_cache = json.loads(tdk_cache_path.read_text(encoding="utf-8")) if tdk_cache_path.exists() else {}

    def save_cache() -> None:
        tdk_cache_path.parent.mkdir(parents=True, exist_ok=True)
        tdk_cache_path.write_text(json.dumps(tdk_cache, ensure_ascii=False, indent=0), encoding="utf-8")

    if not args.no_tdk:   # UD'de olmayan kelimeleri TDK'ya sor (ilerleme yazılır, önbellek sık kaydedilir)
        todo = sorted({p for n, _ in selected.values() for p in n.split(" ")
                       if not ud_freq[p] and p not in tdk_cache})
        print(f"TDK'ya sorulacak {len(todo)} kelime (önbellekte {len(tdk_cache)})", flush=True)
        failed = 0
        try:
            for i, word in enumerate(todo, 1):
                failed += tdk_has(word, tdk_cache) is None
                if i % 20 == 0 or i == len(todo):
                    save_cache()
                    print(f"  {i}/{len(todo)} (ulaşılamayan: {failed})", flush=True)
        finally:
            save_cache()
        if failed:
            print(f"UYARI: {failed} kelime için TDK'ya ulaşılamadı -> script'i tekrar çalıştırın",
                  flush=True)

    def verify(norm: str) -> str | None:
        sources = set()
        for part in norm.split(" "):
            if ud_freq[part]:
                sources.add("UD")
            elif tdk_cache.get(part):
                sources.add("TDK")
            else:
                return None
        return "+".join(sorted(sources))

    rows = [(raw, norm, count, verify(norm)) for raw, (norm, count) in selected.items()]
    rows.sort(key=lambda r: (-r[2], r[0]))
    active = [r for r in rows if r[3]]
    review = [r for r in rows if not r[3]]

    header = [
        "# Normalization lexicon — gayriresmî/yanlış yazım -> doğru yazım (Türkçe)",
        "# OTOMATİK ÜRETİLDİ: python src/scripts/norm_build_lexicon.py  (elle düzenleme yerine script'i güncelle)",
        "# Kaynak: MultiLexNorm Türkçe train — Çolakoğlu, Sulubacak & Tantuğ (2019), ACL SRW;",
        "#         van der Goot et al. (2021), W-NUT. https://huggingface.co/datasets/robvanderg/MultiLexNorm",
        "# Doğrulama: doğru biçimin her kelimesi UD-BOUN train'de ya da TDK Güncel Türkçe Sözlük'te",
        "#         (https://sozluk.gov.tr) bulunur. Seçim kuralları: src/scripts/norm_build_lexicon.py",
        "# Format: ham<TAB>doğru<TAB>tweet_sayısı<TAB>doğrulama   ('#?' satırları: doğrulanamadı,",
        "#         elle kontrol edilip başındaki '#?\\t' silinirse lexicon'a girer)",
        f"# Giriş: {len(active)} aktif, {len(review)} kontrol bekliyor",
    ]
    lines = header + [f"{r}\t{n}\t{c}\t{v}" for r, n, c, v in active]
    lines += ["#", "# --- doğrulanamayanlar (elle kontrol) ---"]
    lines += [f"#?\t{r}\t{n}\t{c}\t-" for r, n, c, _ in review]
    _OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{n_tokens} token çifti -> {len(selected)} aday -> {len(active)} aktif, "
          f"{len(review)} kontrol bekliyor -> {_OUT}")


if __name__ == "__main__":
    main()
