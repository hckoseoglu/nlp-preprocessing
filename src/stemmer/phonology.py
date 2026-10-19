"""Ses kuralları (Oflazer 1994 kural listesi; Göksel & Kerslake 2005 böl. 2–3).

Geri yönde (soyma sırasında) uygulanan onarımlar ve kısıtlar. İstisnalar roots.tsv bayraklarından
gelir (voicing / vowel_drop / doubling / inv_harmony); ayrı istisna listesi yok.
"""
from __future__ import annotations

VOWELS = frozenset("aeıioöuü")
BACK = frozenset("aıou")
FRONT = frozenset("eiöü")
ROUNDED = frozenset("oöuü")
HIGH = frozenset("ıiuü")
VOICELESS = frozenset("pçtkfhsş")          # "fıstıkçı şahap"
DEVOICE = {"b": "p", "c": "ç", "d": "t", "ğ": "k", "g": "k"}   # gövde-sonu yumuşak → sert (kitab→kitap, reng→renk)
DEVOICE_ALT = {"ğ": "g"}                            # antropoloğ → antropolog
_CIRC = str.maketrans("âîûÂÎÛ", "aiuaiu")


def tr_lower(s: str) -> str:
    """Türkçe küçük harf: önce I→ı, İ→i, sonra lower()."""
    return s.replace("I", "ı").replace("İ", "i").lower()


def tr_capitalize(s: str) -> str:
    if not s:
        return s
    first = s[0]
    up = {"i": "İ", "ı": "I"}.get(first, first.upper())
    return up + s[1:]


def fold(s: str) -> str:
    """tr_lower + şapka düzleştirme (â→a, î→i, û→u)."""
    return tr_lower(s).translate(_CIRC)


def last_vowel(s: str) -> str | None:
    for ch in reversed(s):
        if ch in VOWELS:
            return ch
    return None


def ends_with_vowel(s: str) -> bool:
    return bool(s) and s[-1] in VOWELS


def harmonic(archi: str, prev: str | None) -> list[str]:
    """Arşifonem (A/I) için önceki ünlüye uyumlu gerçekleşme(ler). prev None ise tümü."""
    if archi == "A":
        if prev is None:
            return ["a", "e"]
        return ["a"] if prev in BACK else ["e"]
    if archi == "I":
        if prev is None:
            return ["ı", "i", "u", "ü"]
        if prev in BACK:
            return ["u"] if prev in ROUNDED else ["ı"]
        return ["ü"] if prev in ROUNDED else ["i"]
    raise ValueError(archi)


def harmony_ok(stem: str, vowel: str, archi: str) -> bool:
    """Ekin ilk (arşifonem) ünlüsü gövdenin son ünlüsüyle uyumlu mu? Gövdede ünlü yoksa True."""
    lv = last_vowel(stem)
    if lv is None:
        return True
    return vowel in harmonic(archi, lv)


def assimilation_ok(stem: str, first: str, archi: str | None) -> bool:
    """Kısıt 3 — ünsüz benzeşmesi: D→t / C→ç yalnız sert ünsüzden sonra, d/c diğer durumlarda."""
    if archi not in ("D", "C") or not stem:
        return True
    voiceless_stem = stem[-1] in VOICELESS
    return (first in "tç") == voiceless_stem


def buffer_ok(stem: str, opt: str | None, present: bool) -> bool:
    """Kısıt 1 — kaynaştırma: ünsüz tampon (y/s/n/ş) yalnız ünlüden sonra ve zorunlu;
    ünlü tampon (I/A) yalnız ünsüzden sonra ve zorunlu."""
    if opt is None or not stem:
        return True
    v_final = ends_with_vowel(stem)
    if opt in VOWELS or opt in ("A", "I"):      # ünlü tampon
        return present != v_final
    return present == v_final                    # ünsüz tampon


def narrowing_variants(stem: str, allo_surface: str, is_yor: bool) -> list[str]:
    """-yor daralması (bekli-yor → bekle) ve de-/ye- + y (di-ye → de). Ek soyulduktan sonra gövde için
    alternatif yazımlar üretir (gövdenin kendisi dahil değildir)."""
    out: list[str] = []
    if not stem:
        return out
    last = stem[-1]
    if is_yor and last in HIGH:
        out.append(stem[:-1] + ("a" if last in BACK else "e"))
    elif allo_surface.startswith("y") and stem in ("di", "yi"):
        out.append(stem[:-1] + "e")
    return out


def root_variants(stem: str, next_initial: str | None) -> list[tuple[str, frozenset[str]]]:
    """Kök sınırı onarımları. `next_initial`: soyulan (sağdaki) ekin ilk harfi; None = ek yok.
    Dönüş: [(aday kök, gereken bayraklar kümesi)] — ilk eleman gövdenin kendisi (bayraksız).
    Yumuşama / ünlü düşmesi / ikizleşme yalnız ünlüyle başlayan ek soyulduğunda anlamlıdır."""
    out: list[tuple[str, frozenset[str]]] = [(stem, frozenset())]
    if next_initial is None or next_initial not in VOWELS or len(stem) < 2:
        return out
    seen = {stem}

    def add(v: str, flags: set[str]) -> None:
        if v and v not in seen:
            seen.add(v)
            out.append((v, frozenset(flags)))

    cands: list[tuple[str, set[str]]] = [(stem, set())]
    # ikizleşme: hakk → hak, tıbb → tıb(→tıp)
    if len(stem) >= 3 and stem[-1] == stem[-2] and stem[-1] not in VOWELS:
        cands.append((stem[:-1], {"doubling"}))
    # yumuşama: kitab → kitap, gid → git, gözlüğ → gözlük / antropoloğ → antropolog
    for base, fl in list(cands):
        last = base[-1]
        if last in DEVOICE:
            cands.append((base[:-1] + DEVOICE[last], fl | {"voicing"}))
        if last in DEVOICE_ALT:
            cands.append((base[:-1] + DEVOICE_ALT[last], fl | {"voicing"}))
    # ünlü düşmesi: burn → burun, ağz → ağız, oğl → oğul, kayd(→kayt) → kayıt
    for base, fl in list(cands):
        if len(base) >= 3 and base[-1] not in VOWELS and base[-2] not in VOWELS:
            lv = last_vowel(base)
            for v in harmonic("I", lv):
                cands.append((base[:-1] + v + base[-1], fl | {"vowel_drop"}))
    for v, fl in cands[1:]:
        add(v, fl)
    return out
