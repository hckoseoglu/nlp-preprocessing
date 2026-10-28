#!/usr/bin/env python3
"""resources/abbreviations_tr.txt ← TDK Yazım Kılavuzu "Kısaltmalar Dizini" PDF'i.

    python3 src/scripts/split_build_abbrev.py [--pdf Kısaltmalar_Dizini.pdf]

PDF yoksa tdk.gov.tr'den indirilir (data/external/). `pdftotext -layout` ile metne çevrilir; yalnız sonu nokta ile
yazılan girişler (Dr., vb., Sok.) alınır — nokta kullanılmayan büyük harf kısaltmaları (TBMM, ABD) cümle sonu
belirsizliği yaratmadığından listeye girmez. Çıktı: kısaltma<TAB>açılım.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
URL = "https://tdk.gov.tr/wp-content/uploads/2019/01/K%C4%B1saltmalar_Dizini.pdf"
OUT = ROOT / "resources" / "abbreviations_tr.txt"
HEADER = """# Nokta ile biten Türkçe kısaltmalar — sentence splitter (kural: nokta sonrası cümle sonu değil; NB: özellik).
# Kaynak: Türk Dil Kurumu, Yazım Kılavuzu, "Kısaltmalar Dizini" (tdk.gov.tr/wp-content/uploads/2019/01/Kısaltmalar_Dizini.pdf,
# erişim Ekim 2026). Dizinden yalnız sonu nokta ile yazılan girişler otomatik süzüldü (src/scripts/split_build_abbrev.py);
# nokta kullanılmayan büyük harf kısaltmaları (TBMM, ABD) bu listeye girmez — cümle sonu belirsizliği yaratmazlar.
# Biçim: kısaltma<TAB>açılım. Karşılaştırma Türkçe küçük harfe duyarsız yapılır (textutil.is_abbreviation).
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", type=Path, default=ROOT / "data" / "external" / "tdk_kisaltmalar_dizini.pdf")
    args = ap.parse_args()
    if not args.pdf.exists():
        args.pdf.parent.mkdir(parents=True, exist_ok=True)
        print(f"indiriliyor: {URL}", file=sys.stderr)
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        args.pdf.write_bytes(urllib.request.urlopen(req).read())
    text = subprocess.run(["pdftotext", "-layout", str(args.pdf), "-"], capture_output=True, text=True, check=True).stdout
    entries: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^\s{0,4}(\S+)\s{2,}(.+?)\s*$", line)
        if m and m.group(1).endswith(".") and m.group(1) not in entries:
            entries[m.group(1)] = m.group(2)
    OUT.write_text(HEADER + "".join(f"{a}\t{e}\n" for a, e in entries.items()), encoding="utf-8")
    print(f"{len(entries)} kısaltma → {OUT}")


if __name__ == "__main__":
    main()
