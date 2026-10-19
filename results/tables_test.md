# Stemming değerlendirmesi — test (n=9906 içerik token; 0.4s)

Gold = UD lemma, tip-seviyesi tutarlı DerivedFrom ile köke indirgenmiş (bkz. src/scripts/stem_gold.py).
Alt kümeler: bare=form==gold · inflected=yalnız çekim · derived=gold≠lemma (türetim eşlemesi) · oov=form train'de görülmemiş · copula=UD'nin ayrı sözcük yaptığı ek-fiil parçacıkları (du, ydı, ken…) · lexical=copula dışı.

## Accuracy (%)

| yöntem | genel (n=9906) | NOUN (n=3955) | VERB (n=2199) | ADJ (n=681) | PROPN (n=677) | ADV (n=480) | PRON (n=317) | AUX (n=240) | bare (n=4353) | inflected (n=5312) | derived (n=241) | oov (n=2585) | copula (n=180) | lexical (n=9726) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bizim (kural + sözlük) | 94.0 | 94.7 | 91.0 | 91.6 | 94.1 | 93.8 | 96.8 | 83.8 | 96.4 | 92.0 | 92.5 | 87.7 | 78.3 | 94.3 |
| no-stem | 43.9 | 35.9 | 3.0 | 81.2 | 61.9 | 94.8 | 28.7 | 11.7 | 100.0 | 0.0 | 0.0 | 17.8 | 0.0 | 44.8 |
| fixed-prefix-5 | 46.7 | 41.7 | 23.8 | 57.9 | 38.1 | 76.9 | 38.2 | 14.2 | 77.0 | 22.4 | 32.4 | 28.5 | 0.0 | 47.5 |
| Snowball (snowballstemmer) | 53.9 | 68.5 | 14.9 | 54.8 | 62.8 | 44.8 | 57.1 | 15.0 | 69.1 | 43.8 | 1.2 | 47.5 | 0.0 | 54.9 |
| TurkishStemmer (pip) | 55.5 | 74.6 | 13.3 | 63.1 | 53.2 | 44.2 | 58.4 | 13.8 | 70.6 | 44.4 | 25.7 | 47.4 | 0.0 | 56.5 |

## Hata sınıfları (test; toplam 596 hata, 538 farklı)

| sınıf | token | % hataların |
|---|---|---|
| over-stemming | 229 | 38.4 |
| under-stemming | 219 | 36.7 |
| türetim-fazla-soyuldu (over; gold lemma'yı korur) | 51 | 8.6 |
| UD-kopula-parçacığı | 39 | 6.5 |
| belirsizlik (iki geçerli kök) | 16 | 2.7 |
| OOV-kök | 15 | 2.5 |
| fonoloji | 9 | 1.5 |
| diğer | 7 | 1.2 |
| türetim-soyulmadı (under) | 6 | 1.0 |
| gold-gürültüsü/typo | 5 | 0.8 |

## En sık 50 hata

| form | gold | bizim | UPOS | n | sınıf |
|---|---|---|---|---|---|
| sa | i | y | AUX | 5 | UD-kopula-parçacığı |
| dur | y | i | AUX | 4 | UD-kopula-parçacığı |
| tur | y | i | AUX | 4 | UD-kopula-parçacığı |
| işte | iş | işte | ADV | 4 | under-stemming |
| giderek | git | gider | VERB | 3 | belirsizlik (iki geçerli kök) |
| yıllarca | yıllarca | yıl | ADV | 3 | over-stemming |
| ydı | i | y | AUX | 3 | UD-kopula-parçacığı |
| ilgili | ilgili | ilgi | NOUN | 3 | over-stemming |
| gelir | gelir | gel | VERB | 3 | over-stemming |
| alan | al | alan | VERB | 3 | under-stemming |
| belirtildi | belir | belirt | VERB | 2 | under-stemming |
| değerlendirme | değerlen | değerlendirme | VERB | 2 | under-stemming |
| geçen | geç | geçen | VERB | 2 | under-stemming |
| kesin | kes | kesin | ADJ | 2 | under-stemming |
| bilen | bil | bile | VERB | 2 | under-stemming |
| sözde | sözde | söz | ADJ | 2 | over-stemming |
| cumhurbaşkanı | cumhurbaşkan | cumhurbaşkanı | NOUN | 2 | under-stemming |
| alışmış | alış | al | VERB | 2 | over-stemming |
| temiz | te | temiz | NOUN | 2 | under-stemming |
| belirterek | belir | belirt | VERB | 2 | under-stemming |
| hepsi | hep | hepsi | PRON | 2 | under-stemming |
| hazırlanışı | hazırla | hazırlanış | VERB | 2 | under-stemming |
| artırma | artır | art | VERB | 2 | over-stemming |
| öylece | öylece | öyle | ADV | 2 | over-stemming |
| ydü | i | y | AUX | 2 | UD-kopula-parçacığı |
| anı | an | anı | NOUN | 2 | under-stemming |
| aheste | aheste | ahes | ADV | 2 | over-stemming |
| halka | halk | halka | NOUN | 2 | under-stemming |
| iken | ik | i | VERB | 2 | over-stemming |
| sudan | sudan | su | NOUN | 2 | over-stemming |
| dı | i | y | AUX | 2 | UD-kopula-parçacığı |
| demek | de | demek | VERB | 2 | under-stemming |
| suyunu | su | suyunu | NOUN | 2 | under-stemming |
| ken | i | y | AUX | 2 | UD-kopula-parçacığı |
| heyecanlı | heyecanlı | heyecan | ADV | 2 | over-stemming |
| tir | y | i | AUX | 2 | UD-kopula-parçacığı |
| çıkarken | çıkar | çık | VERB | 2 | over-stemming |
| kurulu | kuru | kurulu | ADJ | 2 | under-stemming |
| hırçın | hırç | hırçın | NOUN | 2 | under-stemming |
| bangır | bangır | bank | ADJ | 2 | OOV-kök |
| artış | art | artış | NOUN | 2 | under-stemming |
| umarım | umar | umarım | ADJ | 2 | under-stemming |
| yapın | yapı | yap | ADJ | 2 | over-stemming |
| çıkarmış | çıkar | çık | VERB | 1 | over-stemming |
| cezaevi | cezaev | cezaevi | NOUN | 1 | under-stemming |
| paldür | paldır | pal | NOUN | 1 | over-stemming |
| küldür | küldür | kül | NOUN | 1 | over-stemming |
| uçarlar | uçar | uç | VERB | 1 | over-stemming |
| postmodernleşen | postmodernleş | postmodern | VERB | 1 | over-stemming |
| hoşça | hoşça | hoş | ADV | 1 | over-stemming |
