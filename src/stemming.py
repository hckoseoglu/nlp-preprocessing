"""Stemming — ortak toolkit arayüzü (List[str] -> List[str]). SAHİP: Hikmet, `hikmet` branch.

Gerçek uygulama kök dizindeki `stemmer/` paketidir (kural-tabanlı ek soyma + kök sözlüğü; bkz.
`lexicon/SOURCES.md`, `results/progress_report_section.md`). Bu modül yalnız ince bir sarmalayıcıdır; Stemmer
nesnesi ilk çağrıda yüklenir (sözlük ~26k kök, ~0.2 s).

    from stemming import stem, stem_tokens
    stem("kitabı")                      # 'kitap'
    stem_tokens(["gidiyordum", "eve"])  # ['git', 'ev']
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # src/
from stemmer import Stemmer, tr_lower  # noqa: E402,F401

_STEMMER: Stemmer | None = None


def get_stemmer() -> Stemmer:
    global _STEMMER
    if _STEMMER is None:
        _STEMMER = Stemmer()
    return _STEMMER


def stem(token: str) -> str:
    """Tek tokeni köküne indir."""
    return get_stemmer().stem(token)


def stem_tokens(tokens: list[str]) -> list[str]:
    """Token listesini stem'ler (ortak arayüz)."""
    return get_stemmer().stem_tokens(tokens)


if __name__ == "__main__":
    for w in sys.argv[1:] or ["evlerimizden", "gidiyorum", "kitabı", "gözlüğü", "başlıyorlarmış", "arabası",
                              "güzellik", "çocukları", "yazabilirdim", "rengi", "ara", "kutu"]:
        print(f"  {w:16} -> {stem(w)}")
