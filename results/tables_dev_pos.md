# Stemming değerlendirmesi — dev (+gold POS) (n=10020 içerik token; 0.5s)

Gold = UD lemma, tip-seviyesi tutarlı DerivedFrom ile köke indirgenmiş (bkz. src/scripts/stem_gold.py).
Alt kümeler: bare=form==gold · inflected=yalnız çekim · derived=gold≠lemma (türetim eşlemesi) · oov=form train'de görülmemiş · copula=UD'nin ayrı sözcük yaptığı ek-fiil parçacıkları (du, ydı, ken…) · lexical=copula dışı.

## Accuracy (%)

| yöntem | genel (n=10020) | NOUN (n=3715) | VERB (n=2171) | ADJ (n=807) | PROPN (n=766) | ADV (n=570) | PRON (n=382) | AUX (n=324) | bare (n=4417) | inflected (n=5301) | derived (n=302) | oov (n=2517) | copula (n=241) | lexical (n=9779) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bizim (kural + sözlük) | 94.1 | 94.5 | 91.8 | 89.2 | 93.0 | 96.1 | 97.9 | 88.9 | 96.6 | 91.9 | 94.7 | 87.0 | 85.1 | 94.3 |
| bizim + gold POS | 94.5 | 94.9 | 93.0 | 89.1 | 93.1 | 96.5 | 97.9 | 88.9 | 96.6 | 92.9 | 93.0 | 87.4 | 85.1 | 94.7 |
| no-stem | 44.1 | 35.3 | 2.2 | 72.7 | 65.9 | 96.0 | 34.3 | 8.3 | 100.0 | 0.0 | 0.0 | 19.0 | 0.0 | 45.2 |
| fixed-prefix-5 | 46.7 | 43.5 | 22.2 | 51.2 | 38.5 | 78.8 | 42.7 | 11.4 | 76.6 | 22.9 | 25.8 | 28.2 | 0.0 | 47.8 |
| Snowball (snowballstemmer) | 53.9 | 68.9 | 14.9 | 57.5 | 64.1 | 53.5 | 54.7 | 13.3 | 69.4 | 43.9 | 3.0 | 48.5 | 0.0 | 55.2 |
| TurkishStemmer (pip) | 54.7 | 73.7 | 12.3 | 63.9 | 55.9 | 51.4 | 58.6 | 12.3 | 70.4 | 43.2 | 28.1 | 46.2 | 1.2 | 56.0 |

## Hata sınıfları (dev; toplam 551 hata, 514 farklı)

| sınıf | token | % hataların |
|---|---|---|
| over-stemming | 221 | 40.1 |
| under-stemming | 170 | 30.9 |
| türetim-fazla-soyuldu (over; gold lemma'yı korur) | 69 | 12.5 |
| UD-kopula-parçacığı | 36 | 6.5 |
| belirsizlik (iki geçerli kök) | 15 | 2.7 |
| diğer | 10 | 1.8 |
| OOV-kök | 10 | 1.8 |
| türetim-soyulmadı (under) | 8 | 1.5 |
| gold-gürültüsü/typo | 7 | 1.3 |
| fonoloji | 5 | 0.9 |

## En sık 40 hata

| form | gold | bizim | UPOS | n | sınıf |
|---|---|---|---|---|---|
| sa | i | y | AUX | 8 | UD-kopula-parçacığı |
| ken | i | y | AUX | 5 | UD-kopula-parçacığı |
| suyunu | su | suyunu | NOUN | 4 | under-stemming |
| yken | i | y | AUX | 3 | UD-kopula-parçacığı |
| suyun | su | suy | NOUN | 3 | under-stemming |
| altına | alt | altın | ADJ | 3 | under-stemming |
| ardından | art | ardından | NOUN | 2 | belirsizlik (iki geçerli kök) |
| tir | y | i | AUX | 2 | UD-kopula-parçacığı |
| üstüne | üst | üstün | ADJ | 2 | under-stemming |
| saçlı | saç | saçlı | ADJ | 2 | türetim-soyulmadı (under) |
| yoksa | yoksa | yok | ADV | 2 | over-stemming |
| beraber | beraber | berab | VERB | 2 | over-stemming |
| yitirmiş | yit | yitir | VERB | 2 | under-stemming |
| milli | mil | milli | ADJ | 2 | türetim-soyulmadı (under) |
| hepsini | hep | hepsi | PRON | 2 | under-stemming |
| dik | dik | y | ADJ | 2 | diğer |
| kalbi | kalbi | kalp | NOUN | 2 | belirsizlik (iki geçerli kök) |
| hepsi | hep | hepsi | PRON | 2 | under-stemming |
| dı | i | y | AUX | 2 | UD-kopula-parçacığı |
| yenir | ye | yen | VERB | 2 | under-stemming |
| belirtti | belir | belirt | VERB | 2 | under-stemming |
| alınıyor | al | alın | VERB | 2 | under-stemming |
| işte | iş | işte | ADV | 2 | under-stemming |
| taşınırdı | taşın | taşı | VERB | 1 | over-stemming |
| gerçekleşir | gerçek | gerçekle | VERB | 1 | under-stemming |
| öğretmenlik | öğretmenlik | öğretmen | NOUN | 1 | türetim-fazla-soyuldu (over; gold lemma'yı korur) |
| etsin | etsin | et | VERB | 1 | over-stemming |
| anlatıcı | anlatıcı | anlatı | NOUN | 1 | over-stemming |
| yarışmalar | yarış | yarışma | NOUN | 1 | türetim-soyulmadı (under) |
| öykücülüğün | öykücülük | öykü | NOUN | 1 | türetim-fazla-soyuldu (over; gold lemma'yı korur) |
| yemiş | yemiş | ye | VERB | 1 | over-stemming |
| refahlı | refahlı | refah | ADJ | 1 | türetim-fazla-soyuldu (over; gold lemma'yı korur) |
| ümraniye | ümraniye | ümran | PROPN | 1 | over-stemming |
| dinleyiciler | dinle | din | NOUN | 1 | over-stemming |
| neşelendi | neşe | neşelen | VERB | 1 | under-stemming |
| cifte | çifte | cifte | NOUN | 1 | gold-gürültüsü/typo |
| artırdığına | artır | art | VERB | 1 | over-stemming |
| incelik | incelik | ince | ADJ | 1 | türetim-fazla-soyuldu (over; gold lemma'yı korur) |
| birsen | birsen | bir | PROPN | 1 | over-stemming |
| gerçekleştirebilmek | gerçek | gerçekle | VERB | 1 | under-stemming |
