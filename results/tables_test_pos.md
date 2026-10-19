# Stemming değerlendirmesi — test (+gold POS) (n=9906 içerik token; 0.2s)

Gold = UD lemma, tip-seviyesi tutarlı DerivedFrom ile köke indirgenmiş (bkz. src/scripts/stem_gold.py).
Alt kümeler: bare=form==gold · inflected=yalnız çekim · derived=gold≠lemma (türetim eşlemesi) · oov=form train'de görülmemiş · copula=UD'nin ayrı sözcük yaptığı ek-fiil parçacıkları (du, ydı, ken…) · lexical=copula dışı.

## Accuracy (%)

| yöntem | genel (n=9906) | NOUN (n=3955) | VERB (n=2199) | ADJ (n=681) | PROPN (n=677) | ADV (n=480) | PRON (n=317) | AUX (n=240) | bare (n=4353) | inflected (n=5312) | derived (n=241) | oov (n=2585) | copula (n=180) | lexical (n=9726) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bizim (kural + sözlük) | 94.0 | 94.7 | 91.0 | 91.6 | 94.1 | 93.8 | 96.8 | 83.8 | 96.4 | 92.0 | 92.5 | 87.7 | 78.3 | 94.3 |
| bizim + gold POS | 94.2 | 94.9 | 91.0 | 92.5 | 94.7 | 93.8 | 96.8 | 83.8 | 96.2 | 92.7 | 90.9 | 87.6 | 78.3 | 94.5 |
| no-stem | 43.9 | 35.9 | 3.0 | 81.2 | 61.9 | 94.8 | 28.7 | 11.7 | 100.0 | 0.0 | 0.0 | 17.8 | 0.0 | 44.8 |
| fixed-prefix-5 | 46.7 | 41.7 | 23.8 | 57.9 | 38.1 | 76.9 | 38.2 | 14.2 | 77.0 | 22.4 | 32.4 | 28.5 | 0.0 | 47.5 |
| Snowball (snowballstemmer) | 53.9 | 68.5 | 14.9 | 54.8 | 62.8 | 44.8 | 57.1 | 15.0 | 69.1 | 43.8 | 1.2 | 47.5 | 0.0 | 54.9 |
| TurkishStemmer (pip) | 55.5 | 74.6 | 13.3 | 63.1 | 53.2 | 44.2 | 58.4 | 13.8 | 70.6 | 44.4 | 25.7 | 47.4 | 0.0 | 56.5 |

## Hata sınıfları (test; toplam 575 hata, 520 farklı)

| sınıf | token | % hataların |
|---|---|---|
| over-stemming | 247 | 43.0 |
| under-stemming | 183 | 31.8 |
| türetim-fazla-soyuldu (over; gold lemma'yı korur) | 50 | 8.7 |
| UD-kopula-parçacığı | 39 | 6.8 |
| belirsizlik (iki geçerli kök) | 15 | 2.6 |
| OOV-kök | 15 | 2.6 |
| fonoloji | 8 | 1.4 |
| diğer | 7 | 1.2 |
| türetim-soyulmadı (under) | 6 | 1.0 |
| gold-gürültüsü/typo | 5 | 0.9 |

## En sık 5 hata

| form | gold | bizim | UPOS | n | sınıf |
|---|---|---|---|---|---|
| sa | i | y | AUX | 5 | UD-kopula-parçacığı |
| gerek | gerek | ger | VERB | 4 | over-stemming |
| dur | y | i | AUX | 4 | UD-kopula-parçacığı |
| tur | y | i | AUX | 4 | UD-kopula-parçacığı |
| işte | iş | işte | ADV | 4 | under-stemming |
