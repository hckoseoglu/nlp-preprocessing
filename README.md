# CMPE 561 — Turkish Preprocessing Toolkit (Group 07)

Türkçe için preprocessing toolkit: tokenization, sentence splitting, normalization, **stemming**,
**stopword elimination**. Plan, kararlar ve ilerleme takibi için **`CLAUDE.md`** tek doğruluk kaynağıdır.

## Kurulum
Çekirdek kod yalnız standart kütüphane kullanır. Figürler, baseline'lar ve stopword dış-değerlendirmesi için:
```bash
python3 -m pip install -r requirements.txt     # matplotlib, scikit-learn, snowballstemmer, TurkishStemmer
```
Veri: `data/UD_Turkish-BOUN/` (CoNLL-U train/dev/test) repo kökünde beklenir.

## Kullanım — tek giriş noktası `run.py`
```bash
python3 run.py stem      --text "Kitapları okuyordum."          # kitap oku .
python3 run.py stopword  --text "Bu bir deneme cümlesidir."     # [Bu] [bir] deneme cümlesidir .
python3 run.py pipeline  --text "Bu kitapları okuyordum."       # normalize → stopword → stem
python3 run.py tokenize  --text "Merhaba, dünya!"
python3 run.py stem      --file cumleler.txt --format tsv       # her satır bir cümle; token başına satır
python3 run.py stem      --split dev --eval                     # UD gold token'ları, kök doğruluğu (dev %94.1)
python3 run.py stem      --split dev --eval --pos               # gold POS ile üst sınır
python3 run.py stopword  --split test --eval --list union       # UPOS-proxy P/R/F1
python3 run.py stem      --conllu baska.conllu --eval --format json
```
Girdi: `--text` / `--file` (regex tokenizer ile bölünür) veya `--split` / `--conllu` (gold token'lar).
Çıktı: `--format text|tsv|json`. Stopword listesi: `--list static|dynamic|union|intersection` ya da `--stopword-file`.
Stemmer: `--lexicon <klasör>`, `--ranking score|longest|attested`. `python3 run.py -h` tüm seçenekleri verir.

Kütüphane olarak (`src/` sys.path'te olmalı): `from stemmer import Stemmer` · `from stemming import stem, stem_tokens` ·
`from stopword import load_static_stopwords, remove_stopwords`.

## Yapı
```
run.py                 tek giriş noktası (ince kabuk → src/cli.py)
src/                   TÜM KOD
  cli.py                 CLI uygulaması (yukarıdaki görevler)
  io_conllu.py           CoNLL-U okuyucu (Sentence/Token/Word, SpaceAfter, MISC)
  tokenizer_baseline.py  ham metin için basit regex tokenizer (runtime)
  normalization.py       normalization (Ecem): Normalizer, normalize / normalize_tokens
  noise.py               sentetik gürültü üretici (normalization eval)
  real_data.py           gerçek gürültülü test setleri (MultiLexNorm test, OSCAR-GEC test)
  stemming.py            ince sarmalayıcı → stemmer/ paketi
  evaluate.py            ortak metrik yardımcıları
  stopword/              stopword paketi: core.py (TF-IDF dinamik liste, static liste, eleme, P/R/F1)
  stemmer/               stemming paketi: stemmer.py (ters DFS + skor), suffixes.py, morphotactics.py, phonology.py, lexicon.py
  scripts/               kaynak üretimi ve deneyler (kütüphane değil; proje kökünden çalıştırılır)
    stem_build_gold.py       lexicon/derived.tsv + results/gold_stats.md
    stem_build_roots.py      lexicon/roots.tsv  (--trmorph <TRmorph klonu>)
    stem_build_fragments.py  lexicon/copula_fragments.tsv
    stem_gold.py             gold tanımı (UD lemma + tutarlı DerivedFrom) — diğer stem_* scriptlerinin ortak modülü
    stem_evaluate.py         results/tables_{split}.md, errors_{split}.tsv  (--split dev [--ablation] [--pos gold])
    stem_figures.py          reports/stemming_*.png + results/figures_data.json
    stem_pseudocode.py       reports/stemming_pseudocode.png (rapor figürü: yöntemin sözde kodu; eval çalıştırmaz)
    stopword_evaluate.py     static/dynamic/union/∩ karşılaştırması → reports/stopword_system_comparison.png
    stopword_analyze.py      K-vs-F1, TF-IDF dağılımı → reports/stopword_{k_vs_f1,tfidf_curve}.png
    stopword_extrinsic.py    genre sınıflandırma testi (scikit-learn) → reports/stopword_extrinsic.png
    stopword_build_42bin.py  ikinci korpus (42bin_haber) ile dinamik liste karşılaştırması
    norm_build_lexicon.py    resources/normalization_lexicon.tsv ← MultiLexNorm Türkçe train (indirir, data/external/)
    norm_evaluate.py         normalization test-case tablosu: `norm_evaluate.py dev|test` (test: + gerçek gürültü setleri)
lexicon/               stemmer kaynakları: roots.tsv suffixes.tsv morphotactics.tsv derived.tsv copula_fragments.tsv exceptions.tsv SOURCES.md
resources/             stopword listeleri (stopwords_tr.txt static, stopwords_dynamic_boun.txt dinamik, stopwords_gold_ahmetax.txt referans),
                       normalization_lexicon.tsv (kısaltma/yazım-hata lexicon'u)
tests/                 test_stemmer.py (72 örnek), test_cli.py (CLI duman testleri)
results/               stemming değerlendirme çıktıları (tables*.md, errors_*.tsv, gold/roots istatistikleri)
reports/               figürler (stemming_*.png, stopword_*.png) ve rapor taslakları
data/                  UD_Turkish-BOUN; normalization/real_noisy.tsv (elle); external/ (indirilen, gitignore)
```
Ortak arayüz: her adım `List[str] -> List[str]`; çalışma-zamanı zinciri `normalize → stopword → stem`.

## Testler
```bash
python3 -m unittest tests.test_stemmer tests.test_cli
python3 -m src.stemmer.stemmer kitabı gidiyordum        # aday analizleriyle hata ayıklama
```
