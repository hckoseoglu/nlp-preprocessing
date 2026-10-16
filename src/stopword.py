"""Stopword elimination — static + dynamic (Türkçe, genel domain).

SAHİP: paylaşımlı (Hikmet & Ecem)
- static: dış referans liste (resources/, cite'lı).
- dynamic: UD train frekanslarından (io_conllu.word_frequencies) metrikle (TF, entropi/varyans,
  Zipf vb.) aday üretimi.
Değerlendirme: üretilen liste vs referans -> precision/recall/F1; static vs dynamic karşılaştırması.
Bkz. CLAUDE.md.

Arayüz sözleşmesi: remove_stopwords(List[str]) -> List[str].
Çalışma-zamanı zinciri: normalize -> STOPWORD -> stem (yüzey-form, stem öncesi).
"""
from __future__ import annotations


def load_static_stopwords(path: str) -> set[str]:
    """resources/ altındaki statik listeyi yükle. TODO: liste derle + cite et."""
    raise NotImplementedError("static stopword listesi henüz eklenmedi")


def build_dynamic_stopwords(freq: dict[str, int], top_k: int = 200) -> set[str]:
    """Korpus frekanslarından dinamik stopword listesi üret. TODO: metrik seçimi."""
    raise NotImplementedError("dynamic stopword üretimi henüz implement edilmedi")


def remove_stopwords(tokens: list[str], stopwords: set[str]) -> list[str]:
    """Verilen stopword kümesine göre tokenları ele (ortak arayüz)."""
    return [t for t in tokens if t.casefold() not in stopwords]
