# Stemming — sonuç tabloları (UD Turkish-BOUN)

Üretim: `src/scripts/stem_evaluate.py --split dev --ablation` ve `src/scripts/stem_evaluate.py --split test` (test yalnız bir kez çalıştırıldı).
Gold = UD lemma, tip-seviyesi tutarlı `DerivedFrom` ile köke indirgenmiş (`src/scripts/stem_gold.py`). Karşılaştırma küçük harf + şapka düzleştirme ile.
Alt kümeler: bare=form==gold · inflected=yalnız çekim · derived=gold≠lemma (türetim eşlemesi) · oov=form train'de görülmemiş · copula=UD'nin ayrı sözcük yaptığı ek-fiil parçacıkları (du, ydı, ken…) · lexical=copula dışı.

## Dev (n=10 020)

| yöntem | genel (n=10020) | NOUN (n=3715) | VERB (n=2171) | ADJ (n=807) | PROPN (n=766) | ADV (n=570) | PRON (n=382) | AUX (n=324) | bare (n=4417) | inflected (n=5301) | derived (n=302) | oov (n=2517) | copula (n=241) | lexical (n=9779) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bizim (kural + sözlük) | 94.1 | 94.5 | 91.8 | 89.2 | 93.0 | 96.1 | 97.9 | 88.9 | 96.6 | 91.9 | 94.7 | 87.0 | 85.1 | 94.3 |
| no-stem | 44.1 | 35.3 | 2.2 | 72.7 | 65.9 | 96.0 | 34.3 | 8.3 | 100.0 | 0.0 | 0.0 | 19.0 | 0.0 | 45.2 |
| fixed-prefix-5 | 46.7 | 43.5 | 22.2 | 51.2 | 38.5 | 78.8 | 42.7 | 11.4 | 76.6 | 22.9 | 25.8 | 28.2 | 0.0 | 47.8 |
| Snowball (snowballstemmer) | 53.9 | 68.9 | 14.9 | 57.5 | 64.1 | 53.5 | 54.7 | 13.3 | 69.4 | 43.9 | 3.0 | 48.5 | 0.0 | 55.2 |
| TurkishStemmer (pip) | 54.7 | 73.7 | 12.3 | 63.9 | 55.9 | 51.4 | 58.6 | 12.3 | 70.4 | 43.2 | 28.1 | 46.2 | 1.2 | 56.0 |

## Test (n=9 906) — tek sefer

| yöntem | genel (n=9906) | NOUN (n=3955) | VERB (n=2199) | ADJ (n=681) | PROPN (n=677) | ADV (n=480) | PRON (n=317) | AUX (n=240) | bare (n=4353) | inflected (n=5312) | derived (n=241) | oov (n=2585) | copula (n=180) | lexical (n=9726) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bizim (kural + sözlük) | 94.0 | 94.7 | 91.0 | 91.6 | 94.1 | 93.8 | 96.8 | 83.8 | 96.4 | 92.0 | 92.5 | 87.7 | 78.3 | 94.3 |
| no-stem | 43.9 | 35.9 | 3.0 | 81.2 | 61.9 | 94.8 | 28.7 | 11.7 | 100.0 | 0.0 | 0.0 | 17.8 | 0.0 | 44.8 |
| fixed-prefix-5 | 46.7 | 41.7 | 23.8 | 57.9 | 38.1 | 76.9 | 38.2 | 14.2 | 77.0 | 22.4 | 32.4 | 28.5 | 0.0 | 47.5 |
| Snowball (snowballstemmer) | 53.9 | 68.5 | 14.9 | 54.8 | 62.8 | 44.8 | 57.1 | 15.0 | 69.1 | 43.8 | 1.2 | 47.5 | 0.0 | 54.9 |
| TurkishStemmer (pip) | 55.5 | 74.6 | 13.3 | 63.1 | 53.2 | 44.2 | 58.4 | 13.8 | 70.6 | 44.4 | 25.7 | 47.4 | 0.0 | 56.5 |

## Kök seçim kuralı karşılaştırması (dev, genel accuracy %)

| seçim kuralı | dev |
|---|---|
| sözlüksüz en kısa kök (Eryiğit & Adalı; prototip, `proto_stemmer.py`) | 22–54 |
| sözlükte EN UZUN kök (`ranking=longest`) | 89.3 |
| önce korpusta görülen kökler, sonra en uzun (`ranking=attested`) | 91.5 |
| log-frekans skoru: ln(freq+1)↑5 + 0.5·|kök| − ek maliyeti − onarım − uyum ihlali + tam-sözcük bonusu (`ranking=score`, **varsayılan**) | **94.1** |

## Ablation (genel accuracy, %)

| varyant | genel | lexical | derived | oov |
|---|---|---|---|---|
| tam sistem | 94.1 | 94.3 | 94.7 | 87.0 |
| ünlü uyumu kapalı | 94.0 | 94.3 | 94.7 | 86.9 |
| ünlü uyumu katı | 93.9 | 94.1 | 94.7 | 87.1 |
| kaynaştırma kısıtı kapalı | 94.2 | 94.4 | 94.7 | 87.1 |
| ünsüz benzeşmesi kapalı | 94.1 | 94.3 | 94.7 | 86.9 |
| onarım bayrakları kapalı | 94.0 | 94.3 | 94.7 | 86.9 |
| derived.tsv eşlemesi kapalı | 92.9 | 93.1 | 56.3 | 86.2 |
| DER soyma kuralları kapalı | 93.6 | 93.8 | 54.0 | 88.6 |
| kopula tablosu kapalı | 92.0 | 94.3 | 94.7 | 86.9 |
| özel ad (kesme) yolu kapalı | 94.1 | 94.3 | 95.0 | 86.8 |
| OOV: dokunma | 94.0 | 94.3 | 94.7 | 86.8 |
| OOV: en kısa gövde | 94.0 | 94.2 | 94.7 | 86.8 |
| OOV: en uzun gövde | 93.9 | 94.1 | 94.7 | 86.4 |


## Hata sınıfları (dev; toplam 593 hata, 543 farklı)

| sınıf | token | % hataların |
|---|---|---|
| over-stemming | 215 | 36.3 |
| under-stemming | 213 | 35.9 |
| türetim-fazla-soyuldu (over; gold lemma'yı korur) | 71 | 12.0 |
| UD-kopula-parçacığı | 36 | 6.1 |
| belirsizlik (iki geçerli kök) | 18 | 3.0 |
| diğer | 10 | 1.7 |
| OOV-kök | 10 | 1.7 |
| türetim-soyulmadı (under) | 8 | 1.3 |
| gold-gürültüsü/typo | 7 | 1.2 |
| fonoloji | 5 | 0.8 |

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
| sa | i | y | AUX | 8 | UD-kopula-parçacığı |
| ken | i | y | AUX | 5 | UD-kopula-parçacığı |
| demek | de | demek | VERB | 4 | under-stemming |
| suyunu | su | suyunu | NOUN | 4 | under-stemming |
| yken | i | y | AUX | 3 | UD-kopula-parçacığı |
| doğan | doğ | doğan | VERB | 3 | under-stemming |
| suyun | su | suy | NOUN | 3 | under-stemming |
| benzer | benze | benzer | VERB | 3 | under-stemming |
| ardından | art | ardından | NOUN | 2 | belirsizlik (iki geçerli kök) |
| tir | y | i | AUX | 2 | UD-kopula-parçacığı |
| çalışan | çalış | çalışan | VERB | 2 | under-stemming |
| saçlı | saç | saçlı | ADJ | 2 | türetim-soyulmadı (under) |
| yeter | yet | yeter | VERB | 2 | under-stemming |
| yoksa | yoksa | yok | ADV | 2 | over-stemming |
| süren | sür | süre | VERB | 2 | under-stemming |
| aşkın | aşk | aşkın | NOUN | 2 | under-stemming |
| yitirmiş | yit | yitir | VERB | 2 | under-stemming |
| milli | mil | milli | ADJ | 2 | türetim-soyulmadı (under) |
| yoksun | yoksun | yok | ADJ | 2 | over-stemming |
| hepsini | hep | hepsi | PRON | 2 | under-stemming |
| dik | dik | y | ADJ | 2 | diğer |
| gelin | gelin | gel | NOUN | 2 | over-stemming |
| kalbi | kalbi | kalp | NOUN | 2 | belirsizlik (iki geçerli kök) |
| hepsi | hep | hepsi | PRON | 2 | under-stemming |
| dı | i | y | AUX | 2 | UD-kopula-parçacığı |
| örneğin | örnek | örneğin | NOUN | 2 | belirsizlik (iki geçerli kök) |
| kurulu | kurul | kurulu | NOUN | 2 | under-stemming |
| yenir | ye | yen | VERB | 2 | under-stemming |
| belirtti | belir | belirt | VERB | 2 | under-stemming |
| alınıyor | al | alın | VERB | 2 | under-stemming |
| işte | iş | işte | ADV | 2 | under-stemming |
| sıradan | sıradan | sıra | ADJ | 2 | over-stemming |
| yürüyüş | yürü | yürüyüş | VERB | 2 | under-stemming |
| taşınırdı | taşın | taşı | VERB | 1 | over-stemming |
| umarım | um | umarım | VERB | 1 | under-stemming |
| öğretmenlik | öğretmenlik | öğretmen | NOUN | 1 | türetim-fazla-soyuldu (over; gold lemma'yı korur) |
| etsin | etsin | et | VERB | 1 | over-stemming |
| anlatıcı | anlatıcı | anlat | NOUN | 1 | türetim-fazla-soyuldu (over; gold lemma'yı korur) |
| yarışmalar | yarış | yarışma | NOUN | 1 | türetim-soyulmadı (under) |
| öykücülüğün | öykücülük | öykü | NOUN | 1 | türetim-fazla-soyuldu (over; gold lemma'yı korur) |
| refahlı | refahlı | refah | ADJ | 1 | türetim-fazla-soyuldu (over; gold lemma'yı korur) |
| ümraniye | ümraniye | ümran | PROPN | 1 | over-stemming |
| neşelendi | neşe | neşelen | VERB | 1 | under-stemming |
| cifte | çifte | cifte | NOUN | 1 | gold-gürültüsü/typo |
| artırdığına | artır | art | VERB | 1 | over-stemming |
| incelik | incelik | ince | ADJ | 1 | türetim-fazla-soyuldu (over; gold lemma'yı korur) |
| birsen | birsen | bir | PROPN | 1 | over-stemming |
| burcunun | burç | burcu | NOUN | 1 | belirsizlik (iki geçerli kök) |
| izinden | iz | izin | NOUN | 1 | under-stemming |
| benzer | benze | benzer | NOUN | 1 | under-stemming |


Tam liste: `results/errors_dev.tsv`, `results/errors_test.tsv` (form, gold, bizim, UPOS, n, sınıf).

## İsteğe bağlı gold-POS girdisi (`stem(word, pos=UPOS)`) — üst sınır karşılaştırması

POS verilince adaylar fiil/isim ağına göre süzülür (AUX hariç) ve sözlük POS'u etiketle aynı olan kök +1 bonus alır.
Ayrıntı: `results/tables_dev_pos.md`, `results/tables_test_pos.md`, hatalar `results/errors_dev_pos.tsv`.

| | genel dev | lexical dev | genel test | lexical test | VERB dev | inflected dev | derived dev |
|---|---|---|---|---|---|---|---|
| bizim (POS'suz) | 94.1 | 94.3 | 94.0 | 94.3 | 91.8 | 91.9 | 94.7 |
| bizim + gold POS | 94.5 | 94.7 | 94.2 | 94.5 | 93.0 | 92.9 | 93.0 |

Gold POS yalnız +0.4 (dev) / +0.2 (test) kazandırır: under-stemming hataları 213→170 düşer (doğan→doğ, çalışan→çalış,
alan→al) ama derived alt kümesinde aynı-POS bonusu birkaç türetim eşlemesini bozar (94.7→93.0). Yani kalan hataların
çoğu bağlamsız POS belirsizliği değil; UD ile TRmorph'un sözlükselleşme kararları arasındaki fark ve gold gürültüsü.

## Figürler (`src/scripts/stem_figures.py` → `reports/`)

- `stemming_system_comparison.png` — yöntemler, dev/test genel accuracy
- `stemming_pos_breakdown.png` — POS sınıfına göre Snowball / bizim / bizim+POS (dev)
- `stemming_subsets.png` — token tipine göre POS'suz vs POS'lu (dev)
- `stemming_ranking_ablation.png` — kök seçim kuralı ilerlemesi (89.3→91.5→94.1→94.5) + bileşen ablation'ı (dev)
- `stemming_error_classes.png` — hata sınıfları POS'suz vs POS'lu (dev)

Sayılar: `results/figures_data.json`.

## Snowball vs bizim — POS'suz (tüm tokenler) ve gold POS ile süzülmüş token kümeleri

Snowball Türkçe stemmer yalnız isim ekleri (ve ek-fiil) için tasarlandığı için adil karşılaştırma: aynı gold, token kümesi
gold UPOS ile daraltılıyor (stemmer'a POS verilmiyor, yalnız hangi tokenlerin puanlandığı değişiyor). Figür:
`reports/stemming_pos_filtered_eval.png`.

| token kümesi (dev / test n) | Snowball dev | Snowball test | TurkishStemmer dev | TurkishStemmer test | bizim dev | bizim test |
|---|---|---|---|---|---|---|
| tüm tokenler (10 020 / 9 906) | 53.9 | 53.9 | 54.7 | 55.5 | 94.1 | 94.0 |
| isim sınıfı: NOUN+PROPN+ADJ+PRON+ADV (6 240 / 6 110) | 64.6 | 63.9 | 67.3 | 67.7 | 94.0 | 94.3 |
| yalnız NOUN (3 715 / 3 955) | 68.9 | 68.5 | 73.7 | 74.6 | 94.5 | 94.7 |
| yalnız VERB (2 171 / 2 199) | 14.9 | 14.9 | 12.3 | 13.3 | 91.8 | 91.0 |

Snowball'un kendi alanında (yalnız isimler) bile fark 20+ puan; isim-dışı kalan kısım Snowball'da 14.9'a düşerken bizde 91.8.

## Kural-tabanlı (sözlüksüz) sistemde POS bilgisinin etkisi — Snowball + fiil kuralları

Soru: Snowball yalnız isim kuralları içeriyor; üstüne fiil kuralları eklenirse ve sözcüğün isim mi fiil mi olduğu
bilinirse ne olur? Fiil kuralları = bizim fiil ek envanteri + FSA + ses kısıtları, **sözlüksüz** (`Stemmer.rule_stem(word, "V",
"strip2")`: yalnız ≥2 harfli eklerden oluşan en uzun geçerli zincir soyulur; dev'de denenen shortest / longest / strip2
politikalarının en iyisi). POS'suz birleşimde karar kuralı: fiil kuralı bir şey soyuyorsa fiil say, yoksa Snowball uygula.
Figür: `reports/stemming_rule_only_pos_effect.png`.

| sistem (dev) | genel | NOUN | VERB | ADJ |
|---|---|---|---|---|
| Snowball (yalnız isim kuralları, POS'suz) | 53.9 | 68.9 | 14.9 | 57.5 |
| Snowball + fiil kuralları, POS'suz | 57.6 | 56.5 | 59.8 | 53.4 |
| Snowball + fiil kuralları, **gold POS** | 63.4 | 68.9 | 58.7 | 57.5 |
| kural-only iki ağ (bizim ek envanteri, sözlüksüz), POS'suz | 59.2 | 54.6 | 58.2 | 59.9 |
| kural-only, **gold POS** (VERB→fiil ağı, diğer→isim ağı) | 63.0 | 60.5 | 58.7 | 64.8 |
| bizim (sözlük + skor), POS'suz | 94.1 | 94.5 | 91.8 | 89.2 |
| bizim + gold POS | 94.5 | 94.9 | 93.0 | 89.1 |

Okuma: POS bilgisi kural-only sisteme ~4–6 puan kazandırır (fiil kuralları isimlere yanlış uygulanmaz: NOUN 56.5→68.9),
ama fiillerde tavan ~59'dur çünkü sözlük olmadan hangi ek zincirinin doğru olduğu seçilemez (gel-iyor-du-m vs ge-l-...).
Yani Snowball'un düşük sonucu POS bilgisizliğinden çok sözlüksüzlükten geliyor; sözlük + skor 30 puan, POS 4–6 puan katıyor.
