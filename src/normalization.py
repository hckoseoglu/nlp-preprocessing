"""Normalization — genel domain (haber vb.), Türkçe.

SAHİP: Ecem
Bileşenler: deasciification (gelecegim->geleceğim), case normalizasyonu, sayı/tarih/noktalama
düzeni, yaygın yazım-hata lexicon'u (resources/). Değerlendirme: UD temiz metne sentetik gürültü
enjekte edip (gürültülü, temiz) çiftlerinde token-level accuracy + küçük gerçek gürültülü test
seti. Bkz. CLAUDE.md.

Arayüz sözleşmesi: normalize(token) ve normalize_tokens(List[str]) -> List[str].
Çalışma-zamanı zinciri: NORMALIZE -> stopword -> stem.
"""
from __future__ import annotations


def normalize(token: str) -> str:
    """Tek bir tokeni normalize et. TODO(Ecem): implementasyon."""
    raise NotImplementedError("normalization henüz implement edilmedi")


def normalize_tokens(tokens: list[str]) -> list[str]:
    """Token listesini normalize eder (ortak arayüz)."""
    return [normalize(t) for t in tokens]
