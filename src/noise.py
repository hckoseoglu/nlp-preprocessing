"""Sentetik gürültü üretici — normalization değerlendirmesi için.

SAHİP: Ecem
UD'nin temiz tokenlarını bilerek bozar; (gürültülü, temiz) çiftleri normalizer'ın test case'leri
olur. Her gürültü tipi ayrı fonksiyon; rastgelelik sabit seed'li `random.Random` ile verilir ki
sonuçlar tekrarlanabilsin. Bkz. CLAUDE.md "Normalization".
"""
from __future__ import annotations

import random
import re
import unicodedata

_DATE_DOT = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4}|\d{2})(?=$|')")   # 16.10.2026
_TIME_DOT = re.compile(r"^([01]?\d|2[0-3])\.([0-5]\d)(?=$|')")           # 19.30
_PERCENT_PRE = re.compile(r"^%(\d+(?:[.,]\d+)?)(?=$|')")                  # %25

_ASCII_MAP = str.maketrans("çğıöşüâîûÇĞİÖŞÜÂÎÛ", "cgiosuaiuCGIOSUAIU")
_VOWELS = set("aeıioöuüâîûAEIİOÖUÜÂÎÛ")

# Türkçe Q klavyede komşu tuşlar (typo üretimi için).
_KEYBOARD_ROWS = ["qwertyuıopğü", "asdfghjklşi", "zxcvbnmöç"]
_NEIGHBORS: dict[str, str] = {}
for _r, _row in enumerate(_KEYBOARD_ROWS):
    for _c, _ch in enumerate(_row):
        near = [_row[i] for i in (_c - 1, _c + 1) if 0 <= i < len(_row)]
        for _rr in (_r - 1, _r + 1):
            if 0 <= _rr < len(_KEYBOARD_ROWS):
                near += [_KEYBOARD_ROWS[_rr][i] for i in (_c - 1, _c, _c + 1)
                         if 0 <= i < len(_KEYBOARD_ROWS[_rr])]
        _NEIGHBORS[_ch] = "".join(near)


def is_word(token: str) -> bool:
    """En az bir harf içeren token (noktalama/sayı bozulmaz, metrikte de sayılmaz)."""
    return any(c.isalpha() for c in token)


# --- Tekil gürültü tipleri (token -> token) ---------------------------------------

def strip_diacritics(token: str) -> str:
    """Türkçe karakterleri ASCII karşılığına indirir: geleceğim -> gelecegim."""
    return token.translate(_ASCII_MAP)


def naive_upper(token: str) -> str:
    """Türkçe'yi bilmeyen büyük harf: i -> I (KİTAP değil KITAP), ı -> I."""
    return token.upper()


def repeat_letter(token: str, rng: random.Random) -> str:
    """Bir harfi (tercihen ünlü) 2-4 kez fazladan tekrarlar: çok -> çoooook."""
    positions = [i for i, c in enumerate(token) if c in _VOWELS]
    if not positions:
        positions = [i for i, c in enumerate(token) if c.isalpha()]
    i = rng.choice(positions)
    return token[:i + 1] + token[i] * rng.randint(2, 4) + token[i + 1:]


def typo(token: str, rng: random.Random) -> str:
    """Tek bir klavye hatası: harf düşürme, yer değiştirme, komşu tuş, fazladan komşu tuş."""
    i = rng.randrange(len(token))
    kind = rng.choice(("delete", "swap", "replace", "insert"))
    if kind == "delete":
        return token[:i] + token[i + 1:]
    if kind == "swap" and i < len(token) - 1 and token[i] != token[i + 1]:
        return token[:i] + token[i + 1] + token[i] + token[i + 2:]
    near = _NEIGHBORS.get(token[i].lower())
    if not near:
        return token[:i] + token[i + 1:]
    ch = rng.choice(near)
    if kind == "insert":
        return token[:i + 1] + ch + token[i + 1:]
    return token[:i] + ch + token[i + 1:]


def format_variant(token: str, rng: random.Random) -> str:
    """Aynı tokenin standart dışı yazımı: kıvrık tırnak/kesme, uzun tire, … , !!!, 19:30,
    16/10/2026, 25%, ayrık Unicode (Mac'ten kopyalanan metinde ş = s + çengel)."""
    if token == '"':
        return rng.choice(["“", "”", "''"])
    if token == "...":
        return rng.choice(["…", "..", "...."])
    if token == "-":
        return rng.choice(["–", "—"])
    if token in ("!", "?"):
        return token * rng.randint(2, 4)
    m = _DATE_DOT.match(token)
    if m:
        sep = rng.choice("/-")
        return f"{m[1]}{sep}{m[2]}{sep}{m[3]}{token[m.end():]}"
    m = _TIME_DOT.match(token)
    if m:
        return f"{m[1]}:{m[2]}{token[m.end():]}"
    m = _PERCENT_PRE.match(token)
    if m:
        return f"{m[1]}%{token[m.end():]}"
    return unicodedata.normalize("NFD", token.replace("'", "’"))


# --- Cümle düzeyinde bozma ---------------------------------------------------------

def corrupt(tokens: list[str], kind: str, rate: float, rng: random.Random) -> list[str]:
    """Bir cümlenin harf içeren tokenlarının `rate` kadarını `kind` tipiyle bozar
    ("format" tipinde noktalama ve sayı tokenları da bozulur).

    kind: "diacritics" | "upper" | "repeat" | "typo" | "format" | "mixed" | "clean"
    "mixed": cümle %50 ihtimalle Türkçe karaktersiz yazılır (klavye cümle düzeyinde bir
    özelliktir), üstüne tokenların ~%10'unda harf tekrarı, ~%5'inde typo.
    """
    if kind == "clean":
        return list(tokens)
    if kind == "mixed":
        no_tr_keyboard = rng.random() < 0.5
        out = []
        for t in tokens:
            if is_word(t):
                if no_tr_keyboard:
                    t = strip_diacritics(t)
                r = rng.random()
                if r < 0.10:
                    t = repeat_letter(t, rng)
                elif r < 0.15 and t.isalpha() and len(t) >= 4:
                    t = typo(t, rng)
            out.append(t)
        return out

    out = []
    for t in tokens:
        if (is_word(t) or kind == "format") and rng.random() < rate:
            if kind == "format":
                t = format_variant(t, rng)
            elif kind == "diacritics":
                t = strip_diacritics(t)
            elif kind == "upper":
                t = naive_upper(t)
            elif kind == "repeat":
                t = repeat_letter(t, rng)
            elif kind == "typo" and t.isalpha() and len(t) >= 4:
                t = typo(t, rng)
        out.append(t)
    return out


if __name__ == "__main__":
    rng = random.Random(0)
    ornek = "Fakülteyi bitirenler en uçtan göreve başlıyorlarmış .".split()
    for k in ("diacritics", "upper", "repeat", "typo", "mixed"):
        print(f"{k:<11}", " ".join(corrupt(ornek, k, 1.0, rng)))
    bicim = ['"', "Saat", "19.30'da", "%25'lik", "...", "08.02.2007", "-", "Türkiye'nin", "!"]
    print(f"{'format':<11}", [ascii(t) for t in corrupt(bicim, "format", 1.0, rng)])
