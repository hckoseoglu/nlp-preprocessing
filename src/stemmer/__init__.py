"""Türkçe kural-tabanlı stemmer (CMPE 561 Group 07, Hikmet Can Köseoğlu).

Eryiğit & Adalı (2004) şeması: ek-sıralama FSA'sı ters yürütülerek kelime sondan başa soyulur;
allomorflar önceden üretilir; kök sınırındaki ses değişimleri geri alınır. Fark: kök sözlüğü
(TRmorph + UD-BOUN) kullanılır ve sözlükte bulunan EN UZUN kök seçilir.

    from stemmer import Stemmer
    st = Stemmer()
    st.stem("kitabı")          # → 'kitap'
    st.stem_tokens([...])      # List[str] -> List[str]
"""
from .stemmer import Stemmer, Candidate, Config  # noqa: F401
from .phonology import tr_lower, fold  # noqa: F401
