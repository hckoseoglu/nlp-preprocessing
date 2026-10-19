# Gold istatistikleri (stem_build_gold.py)

min_count=2, min_ratio=0.5, chain=True

## derived.tsv

- accepted: 579
- chained: 25
- rejected_low_count: 1260
- rejected_low_ratio: 107
- rejected_not_prefix: 73
- rejected_root_eq_lemma: 81
- rejected_root_not_lemma: 355
- rejected_short_root: 6
- types_with_df: 2461
- zincir derinliği dağılımı: {1: 554, 2: 25}
- yalnız train'de görülen tip: 575

## Split başına token sayıları

| split | içerik token | form==gold (çıplak) | gold≠lemma (türetim eşlemesi) | DerivedFrom taşıyan |
|---|---|---|---|---|
| train | 81851 | 35917 | 2634 | 4514 |
| dev | 10020 | 4417 | 302 | 395 |
| test | 9906 | 4353 | 241 | 249 |

## Örnek eşlemeler (en sık 25)

| lemma | upos | kök | derinlik | n_agree/n_df/n_lemma |
|---|---|---|---|---|
| ilgili | ADJ | ilgi | 1 | 55/55/61 |
| farklı | ADJ | fark | 1 | 48/48/51 |
| önemli | ADJ | önem | 1 | 39/39/46 |
| hastalık | NOUN | hasta | 1 | 30/30/45 |
| çeşitli | ADJ | çeşit | 1 | 33/33/34 |
| birlik | NOUN | bir | 1 | 18/18/33 |
| kimlik | NOUN | kim | 1 | 22/22/33 |
| milli | ADJ | mil | 1 | 17/17/33 |
| güvenlik | NOUN | güven | 1 | 22/22/29 |
| gerçekleş | VERB | gerçek | 1 | 17/17/29 |
| türlü | ADJ | tür | 1 | 23/23/29 |
| yardımcı | NOUN | yardım | 1 | 18/18/29 |
| varlık | NOUN | var | 1 | 18/18/28 |
| kişilik | NOUN | kişi | 1 | 22/22/27 |
| bağlı | ADJ | bağ | 1 | 25/25/27 |
| önemli | NOUN | önem | 1 | 24/24/25 |
| tatlı | ADJ | tat | 1 | 20/20/24 |
| gizli | ADJ | giz | 1 | 22/22/24 |
| oyuncu | NOUN | oyun | 1 | 21/21/23 |
| ünlü | ADJ | ün | 1 | 20/20/22 |
| karşılık | NOUN | karşı | 1 | 12/12/22 |
| adlı | NOUN | ad | 1 | 22/22/22 |
| başarılı | ADJ | başarı | 1 | 21/21/22 |
| gençlik | NOUN | genç | 1 | 18/18/21 |
| hazırlık | NOUN | hazır | 1 | 15/15/20 |
