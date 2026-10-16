"""Stemming — rule-based suffix-stripping (Türkçe).

SAHİP: Hikmet
Yaklaşım: longest-match ile çekim (inflectional) + geniş yapım (derivational) eklerini soy;
ünlü uyumu ve ünsüz yumuşaması alomorflarını hesaba kat. Suffix lexicon ZORUNLU (resources/).
Değerlendirme: çıktı vs UD lemma (io_conllu.lemma_pairs), accuracy. Bkz. CLAUDE.md.

Arayüz sözleşmesi: stem(token) ve stem_tokens(List[str]) -> List[str].
Çalışma-zamanı zinciri: normalize -> stopword -> STEM.
"""
from __future__ import annotations


def stem(token: str) -> str:
    """Tek bir tokeni köküne indir. TODO(Hikmet): suffix-stripping implementasyonu."""
    raise NotImplementedError("stemming henüz implement edilmedi")


def stem_tokens(tokens: list[str]) -> list[str]:
    """Token listesini stem'ler (ortak arayüz)."""
    return [stem(t) for t in tokens]
