"""Baseline tokenizer — yalnızca RUNTIME (ham metin girişi) için.

Dev/eval'de UD gold token'ları kullanılır (io_conllu.gold_tokens); bu modül sadece ham metni
işleme sokmak için basit bir regex tokenizer sağlar. Saf whitespace-split YETERSİZ (Türkçe'de
noktalama kelimeye yapışık gelir). Gerçek rule-based + ML tokenizer rapor sonrasına.
"""
from __future__ import annotations

import re

# Kelime karakterleri (Türkçe dahil) vs noktalama; URL/e-mail kabaca korunur.
_PATTERN = re.compile(
    r"""
    (?:https?://\S+)            # URL
  | (?:[\w.+-]+@[\w-]+\.[\w.-]+) # e-mail
  | (?:[#@]\w+)                  # hashtag / mention
  | (?:\d+(?:[.,:/]\d+)+(?:['’]\w+)?)   # sayı / saat / tarih (+kesmeli ek): 19.30'da  3,5  08.02.2007
  | (?:\w+['’]\w+)              # kesmeli özel ad: İstanbul'daki (UD'de tek token)
  | \w+                         # kelime (unicode harf+rakam)
  | [^\s\w]                     # tek noktalama
    """,
    re.UNICODE | re.VERBOSE,
)


def tokenize(text: str) -> list[str]:
    """Ham metni basit kurallarla tokenlara ayır (runtime baseline)."""
    return _PATTERN.findall(text)


if __name__ == "__main__":
    print(tokenize("Merhaba dünya! Bkz. https://a.b ve mail@x.com #nlp"))
