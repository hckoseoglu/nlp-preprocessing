# CMPE 561 — Turkish Preprocessing Toolkit (Group 07)

Türkçe için preprocessing toolkit: tokenization, sentence splitting, normalization, **stemming**,
**stopword elimination**. Plan, kararlar ve ilerleme takibi için **`CLAUDE.md`** tek doğruluk kaynağıdır.

## Kurulum
Çekirdek kod yalnız standart kütüphane kullanır. Figürler, baseline'lar ve stopword dış-değerlendirmesi için:
```bash
python3 -m venv .venv && .venv/bin/python3 -m pip install -r requirements.txt   # matplotlib, scikit-learn, snowballstemmer, TurkishStemmer, nltk
.venv/bin/python3 -c "import nltk; nltk.download('punkt_tab')"               # sentence splitting dış baseline'ı (Punkt, Türkçe)
```
Veri: `data/UD_Turkish-BOUN/` (CoNLL-U train/dev/test) repo kökünde beklenir.

## Kullanım — tek giriş noktası `run.py`
Görevler: `tokenize` · `split` · `normalize` · `stopword` · `stem` · `pipeline` (= split → tokenize → normalize → stopword → stem).
Girdi dört biçimde verilir: `--text "..."` (tek cümle) · `--doc belge.txt` ya da `--doc -` (stdin; ham doküman, önce cümlelere bölünür) ·
`--file cumleler.txt` (her satır bir cümle) · `--split dev|test` / `--conllu dosya` (UD gold token'ları, `--eval` ile ölçüm).
Çıktı: `--format text` (varsayılan) | `tsv` (token başına satır) | `json`. `python3 run.py -h` tüm seçenekleri verir.

### Demo senaryoları
```bash
# 1) Tek cümle, her görev ayrı
python3 run.py tokenize  --text 'Dr. Ahmet 3. kez Ankara'"'"'ya gitti, %25 indirim aldı.'   # Dr. Ahmet 3. kez Ankara'ya gitti , %25 indirim aldı .
python3 run.py split     --text 'Dr. Ali geldi. "Neden?" diye sordu. Gitti.'               # satır başına bir cümle
python3 run.py normalize --text "Gunes dogdu, cooook guzel!"                               # güneş doğdu , çok güzel !
python3 run.py stopword  --text "Bu bir deneme cümlesidir."                                # [Bu] [bir] deneme cümlesidir .  (köşeli = elendi)
python3 run.py stem      --text "Kitapları okuyordum."                                     # kitap oku .
python3 run.py pipeline  --text "Bu kitapları okuyordum."                                  # kitap oku .

# 2) Doküman (demo'nun ana senaryosu): dosya ya da stdin → cümle başına bir satır (s1, s2, ...)
python3 run.py pipeline  --doc belge.txt
python3 run.py pipeline  --doc belge.txt --format tsv                 # token başına: cümle, token, normalized, kept, stem
python3 run.py split     --doc belge.txt                              # yalnız cümleler
python3 run.py stem      --doc - < belge.txt --format json            # stdin'den

# 3) Satır başına bir cümle olan dosya
python3 run.py pipeline  --file cumleler.txt --format tsv

# 4) Tokenizer seçimi (ham metin modları): rule (varsayılan, stdlib) | lr (Logistic Regression, scikit-learn, train'den ~1 s) | regex (eski baseline)
python3 run.py tokenize  --text "..." --tokenizer lr --lr-level 3
python3 run.py tokenize  --text "Teklifi kabul etti ya da öyle göründü." --mwe --format tsv   # MWE katmanı: 'kabul etti', 'ya da' tek token

# 5) Splitter seçimi: nb (varsayılan; dev'de en iyi özellik seti, resources/splitter_nb.json) | rule (kural tabanlı, TDK kısaltma listesi)
python3 run.py split     --doc belge.txt --method rule

# 6) Stopword listesi ve stemmer seçenekleri
python3 run.py stopword  --text "..." --list static|dynamic|union|intersection      # ya da --stopword-file kendi_listem.txt
python3 run.py stem      --text "..." --ranking score|longest|attested [--lexicon klasör]

# 7) Gold veri üzerinde hızlı ölçüm (tam tablolar için src/scripts altındaki *_evaluate.py)
python3 run.py stem      --split dev --eval            # kök doğruluğu (dev %94.1, test %94.0)   [--pos: gold POS ile üst sınır]
python3 run.py stopword  --split test --eval --list union   # UPOS-proxy P/R/F1
python3 run.py split     --split dev --eval            # sahte paragraflarda aday doğruluğu / macro-F1 / cümle exact
python3 run.py stem      --conllu baska.conllu --eval --format json
```
Tam değerlendirme tabloları (`results/`): `src/scripts/tok_evaluate.py dev|test` · `split_evaluate.py --split dev|test` ·
`stem_evaluate.py --split dev --ablation` · `stopword_evaluate.py` · `norm_evaluate.py dev|test`. Test split'i her görevde bir kez çalıştırıldı.

Kütüphane olarak (`src/` sys.path'te olmalı): `from stemmer import Stemmer` · `from stemming import stem, stem_tokens` ·
`from stopword import load_static_stopwords, remove_stopwords`.

## Yapı
```
run.py                 tek giriş noktası (ince kabuk → src/cli.py)
src/                   TÜM KOD
  cli.py                 CLI uygulaması (yukarıdaki görevler)
  io_conllu.py           CoNLL-U okuyucu (Sentence/Token/Word, SpaceAfter, MISC)
  tokenizer_baseline.py  eski regex tokenizer (--tokenizer regex; baseline)
  tokenization/          tokenization (Ecem): rules.py (RuleTokenizer: regex + UD/TDK nokta sözleşmeleri) ml.py (LRTokenizer, scikit-learn)
                         features.py (3 kümülatif set) corpus.py (aday noktaları, gold) mwe.py (MWE katmanı, resources/mwe_tr.txt)
                         special.py (sentetik URL/e-mail/hashtag) hard_cases.py metrics.py
  textutil.py            ortak yardımcılar: Türkçe küçük/büyük harf, sayı / baş harf / kısaltma testleri (splitting + tokenization)
  ml/                    kendi ML sınıflandırıcılarımız: naive_bayes.py (kategorik NB, Laplace, log-uzay; JSON kaydet/yükle)
  splitting/             sentence splitting: corpus.py (aday çıkarımı, sahte paragraf, etiket) features.py (3 iç içe set)
                         rules.py (RuleSplitter, AlwaysSplit baseline) ml.py (NBSplitter; model resources/splitter_nb.json)
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
    stopword_pseudocode.py   reports/stopword_pseudocode.png (rapor figürü: stopword sözde kodu)
    tok_evaluate.py          tokenization tabloları: `tok_evaluate.py dev|test` → results/tables_tok_{split}.md (3 test case + MWE)
    tok_build_special.py     data/tokenization/special_{dev,test}.conllu (sentetik özel varlık seti)
    tok_build_mwe.py         resources/mwe_tr.txt ← UD train deprel'leri (fixed, compound:redup, compound:lvc)
    tok_corpus_stats.py      aday nokta sayıları
    split_evaluate.py        sentence splitting tablosu: `--split dev|test` → results/tables_split_{split}.md, errors_split_{split}.tsv,
                             resources/splitter_nb.json (4 test case: full · challenging · lowercase · abbrev; NB set 1/2/3 + rule + baseline)
    split_build_abbrev.py    resources/abbreviations_tr.txt ← TDK Kısaltmalar Dizini PDF (nokta ile biten kısaltmalar)
    stopword_evaluate.py     static/dynamic/union/∩ karşılaştırması → reports/stopword_system_comparison.png
    stopword_analyze.py      K-vs-F1, TF-IDF dağılımı → reports/stopword_{k_vs_f1,tfidf_curve}.png
    stopword_extrinsic.py    genre sınıflandırma testi (scikit-learn) → reports/stopword_extrinsic.png
    stopword_build_42bin.py  ikinci korpus (42bin_haber) ile dinamik liste karşılaştırması
    norm_build_lexicon.py    resources/normalization_lexicon.tsv ← MultiLexNorm Türkçe train (indirir, data/external/)
    norm_evaluate.py         normalization test-case tablosu: `norm_evaluate.py dev|test` (test: + gerçek gürültü setleri)
lexicon/               stemmer kaynakları: roots.tsv suffixes.tsv morphotactics.tsv derived.tsv copula_fragments.tsv exceptions.tsv SOURCES.md
resources/             stopword listeleri (stopwords_tr.txt static, stopwords_dynamic_boun.txt dinamik, stopwords_gold_ahmetax.txt referans),
                       normalization_lexicon.tsv, abbreviations_tr.txt (TDK), mwe_tr.txt, splitter_nb.json (NB splitter modeli)
tests/                 test_stemmer.py test_tokenizer.py test_splitter.py test_naive_bayes.py test_cli.py
results/               stemming değerlendirme çıktıları (tables*.md, errors_*.tsv, gold/roots istatistikleri)
reports/               figürler (stemming_*.png, stopword_*.png) ve rapor taslakları
data/                  UD_Turkish-BOUN; splitting/challenging_abbrev.txt (elle); tokenization/special_*.conllu (sentetik);
                       normalization/real_noisy.tsv (elle); external/ (indirilen, gitignore)
```
Ortak arayüz: splitter `str -> List[str]` (cümleler), tokenizer `str -> List[str]` (token'lar), diğer adımlar `List[str] -> List[str]`;
çalışma-zamanı zinciri `split → tokenize → normalize → stopword → stem`.

## Testler
```bash
python3 -m unittest tests.test_stemmer tests.test_splitter tests.test_naive_bayes tests.test_cli
.venv/bin/python3 -m unittest tests.test_tokenizer                   # LR tokenizer testleri scikit-learn ister
python3 -m src.stemmer.stemmer kitabı gidiyordum        # aday analizleriyle hata ayıklama
```
