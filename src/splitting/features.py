"""NB splitter özellik setleri — iç içe (1 ⊂ 2 ⊂ 3), rapor bölüm 4.2.

Set 1  noktalama + sağ kelimenin büyük/küçük harf durumu + kapanış tırnağı     (Gillick 2009: cap(R); R&R 1997: Suffix)
Set 2  + sol kelime kısaltma / baş harf / sayı mı, uzunluğu, içinde nokta var mı  (Gillick: len(L); R&R: abbreviation)
Set 3  + sol kelimenin son 2 ve 3 harfi (-dı, -yor: Türkçe'de yüklem sondadır)     (Güz, Favre et al. 2009: morfoloji)
"""
from __future__ import annotations

from textutil import OPEN_QUOTES, first_alpha_case, is_abbreviation, is_initial, is_number, strip_quotes, tr_lower

from .corpus import Candidate

FEATURE_LEVELS = (1, 2, 3)


def _len_bucket(n: int) -> str:
    if n <= 3:
        return str(n)
    return "4-5" if n <= 5 else "6+"


def extract(c: Candidate, abbrs: set[str], level: int = 3) -> dict[str, str]:
    f: dict[str, str] = {
        "punct": c.punct,
        "close": "y" if c.close else "n",
        "right_case": ("q_" if (c.right and c.right[0] in OPEN_QUOTES) else "") + (first_alpha_case(c.right) if c.right else "END"),
    }
    if level >= 2:
        left = strip_quotes(c.left)
        f.update({
            "left_abbr": "y" if is_abbreviation(left, abbrs) else "n",
            "left_initial": "y" if is_initial(left) else "n",
            "left_number": "y" if is_number(left) else "n",
            "left_len": _len_bucket(len(left)),
            "left_dot": "y" if "." in left else "n",
        })
    if level >= 3:
        low = tr_lower(strip_quotes(c.left))
        f["left_suf2"] = low[-2:].rjust(2, "_")
        f["left_suf3"] = low[-3:].rjust(3, "_")
    return f
