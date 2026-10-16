"""Stemming — rule-based suffix-stripping (Türkçe). SAHİP: Hikmet, `hikmet` branch.

v1 YAKLAŞIM: morfotaktik **sıralı** soyma + morfofonemik onarım.
- Ekleri gerçek eklenme sırasının TERSİNDEN, slot slot soyarız; her slot'tan **en fazla bir**
  ek (o slot içinde longest-match). Böylece v0'daki "köke kadar inen" greedy zincir kırılır
  (örn. çocukları → [case ı] çocuklar → [plural lar] çocuk).
- Soyma sonrası **morfofonemik onarım**: ünlüyle başlayan ek soyulunca gövde-sonu yumuşak ünsüzü
  sertleştir (kitab→kitap, gözlüğ→gözlük, reng→renk).
- Ünlü uyumu kısıtı HENÜZ YOK (v2). Suffix envanteri: resources/suffixes_tr.txt (düz liste);
  burada slot yapısı kodda tanımlı.

Değerlendirme: eval_stemming.py. Bkz. CLAUDE.md "STEMMING — DETAYLI PLAN".
"""
from __future__ import annotations

MIN_STEM = 2                 # soyma sonrası kalan gövde en az bu kadar harf ("1 harften uzun")
VOWELS = set("aeıioöuü")
_HARDEN = {"b": "p", "c": "ç", "d": "t", "ğ": "k", "g": "k"}  # morfofonemik geri-kurgu


def tr_lower(s: str) -> str:
    """Türkçe'ye duyarlı küçük harf (I→ı, İ→i)."""
    return s.replace("I", "ı").replace("İ", "i").lower()


# Morfotaktik slotlar — SOYMA sırasıyla (dıştan içe). Her slot bir kez uygulanır.
# Her listedeki ekler longest-match için uzundan kısaya sıralanır (kodda otomatik).
_SLOTS_RAW: list[tuple[str, list[str]]] = [
    ("copula", ["ydı", "ydi", "ymış", "ymiş", "yse", "ysa",
                "dır", "dir", "dur", "dür", "tır", "tir", "tur", "tür", "ken"]),
    ("person", ["sınız", "siniz", "sunuz", "sünüz", "sın", "sin", "sun", "sün",
                "yım", "yim", "yız", "yiz", "ız", "iz", "uz", "üz",
                "ım", "im", "um", "üm", "lar", "ler", "k"]),  # fiil kişi ekleri (3çk lar/ler dahil)
    ("tense",  ["ıyor", "iyor", "uyor", "üyor", "yor", "yacak", "yecek", "acak", "ecek",
                "mış", "miş", "muş", "müş", "malı", "meli", "sa", "se",
                "dı", "di", "du", "dü", "tı", "ti", "tu", "tü",
                "ar", "er", "ır", "ir", "ur", "ür", "r"]),
    ("neg",    ["ma", "me"]),
    ("case",   ["ndan", "nden", "nın", "nin", "nun", "nün", "dan", "den", "tan", "ten",
                "yla", "yle", "nda", "nde", "yı", "yi", "yu", "yü", "nı", "ni", "nu", "nü",
                "ya", "ye", "na", "ne", "ca", "ce", "ça", "çe",
                "da", "de", "ta", "te", "la", "le",
                "ın", "in", "un", "ün", "ı", "i", "u", "ü", "a", "e"]),
    ("poss",   ["ımız", "imiz", "umuz", "ümüz", "ınız", "iniz", "unuz", "ünüz",
                "ları", "leri", "sı", "si", "su", "sü",
                "ım", "im", "um", "üm", "ın", "in", "un", "ün",
                "ı", "i", "u", "ü", "m", "n"]),
    ("plural", ["lar", "ler"]),
]
_SLOTS = [(name, sorted(set(sfx), key=len, reverse=True)) for name, sfx in _SLOTS_RAW]


def _harden_final(stem: str) -> str:
    """Gövde-sonu yumuşak ünsüzü sertleştir (ünlüyle başlayan ek soyulduktan sonra)."""
    if stem and stem[-1] in _HARDEN:
        return stem[:-1] + _HARDEN[stem[-1]]
    return stem


def stem(token: str, min_stem: int = MIN_STEM) -> str:
    """Tek tokeni köküne indir: morfotaktik sıralı soyma + morfofonemik onarım."""
    w = tr_lower(token)
    for name, sfx_list in _SLOTS:
        max_strips = 2 if name == "tense" else 1   # bileşik zaman (ırdı, yordu) için 2
        for _ in range(max_strips):
            for s in sfx_list:            # uzundan kısaya → ilk eşleşen = en uzun
                if len(w) - len(s) >= min_stem and w.endswith(s):
                    w = w[: -len(s)]
                    if s[0] in VOWELS:    # ünlüyle başlayan ek → yumuşama geri-kurgu
                        w = _harden_final(w)
                    break
            else:
                break                     # bu slot'ta eşleşme kalmadı
    return w


def stem_tokens(tokens: list[str]) -> list[str]:
    """Token listesini stem'ler (ortak arayüz)."""
    return [stem(t) for t in tokens]


if __name__ == "__main__":
    for w in ["evlerimizden", "gidiyorum", "kitabı", "gözlüğü", "başlıyorlarmış",
              "arabası", "güzellik", "çocukları", "yazabilirdim", "rengi", "ara", "kutu"]:
        print(f"  {w:16} -> {stem(w)}")
