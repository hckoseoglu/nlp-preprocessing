"""Ortak metin yardımcıları — sentence splitting ve tokenization'ın paylaştığı küçük modül.

Türkçe büyük/küçük harf (İ/ı), kelime sınıfı testleri (sayı, baş harf, kısaltma) ve tırnak/parantez
temizliği. Her iki görev de bunu import eder; görev-özel kural buraya girmez.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ABBREV_FILE = ROOT / "resources" / "abbreviations_tr.txt"

_TO_LOWER = str.maketrans({"I": "ı", "İ": "i"})
_TO_UPPER = str.maketrans({"ı": "I", "i": "İ"})

OPEN_QUOTES = "\"“„«‘'([{"
CLOSE_QUOTES = "\"”»’')]}"

_NUMBER_RE = re.compile(r"[+-]?\d+(?:[.,:/]\d+)*%?")
_INITIAL_RE = re.compile(r"[A-ZÇĞİÖŞÜ](?:\.[A-ZÇĞİÖŞÜ])*")   # A  /  T.C  /  M.Ö


def tr_lower(s: str) -> str:
    """Türkçe küçük harf: I→ı, İ→i (str.lower tek başına İ'yi 'i̇' yapar)."""
    return s.translate(_TO_LOWER).lower()


def tr_upper(s: str) -> str:
    return s.translate(_TO_UPPER).upper()


def strip_quotes(word: str) -> str:
    """Baştaki açılış ve sondaki kapanış tırnak/parantezlerini at."""
    return word.lstrip(OPEN_QUOTES).rstrip(CLOSE_QUOTES)


def first_alpha_case(word: str) -> str:
    """Kelimenin ilk anlamlı karakterinin sınıfı: upper / lower / digit / other / none."""
    w = word.lstrip(OPEN_QUOTES)
    if not w:
        return "none"
    ch = w[0]
    if ch.isdigit():
        return "digit"
    if ch.isalpha():
        return "upper" if ch == tr_upper(ch) and ch != tr_lower(ch) else "lower"
    return "other"


def is_number(word: str) -> bool:
    """Sayı, saat, tarih, oran: 3  19.30  08.02.2007  3,5  %25."""
    w = strip_quotes(word).lstrip("%")
    return bool(w) and _NUMBER_RE.fullmatch(w) is not None


def is_initial(word: str) -> bool:
    """Tek büyük harf ya da nokta ile ayrılmış büyük harfler (A, T.C, M.Ö) — nokta ile biten baş harf."""
    return _INITIAL_RE.fullmatch(strip_quotes(word)) is not None


def load_abbreviations(path: str | Path = ABBREV_FILE) -> set[str]:
    """TDK kısaltma listesi → Türkçe küçük harfli, sondaki noktası atılmış küme."""
    abbrs: set[str] = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        abbr = line.split("\t", 1)[0].strip()
        abbrs.add(tr_lower(abbr.rstrip(".")))
    return abbrs


def is_abbreviation(word: str, abbrs: set[str]) -> bool:
    """Kelime (nokta hariç) kısaltma listesinde mi? Büyük/küçük harfe duyarsız."""
    return tr_lower(strip_quotes(word).rstrip(".")) in abbrs
