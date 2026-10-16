# CMPE 561 — Turkish Preprocessing Toolkit (Group 07)

Türkçe için preprocessing toolkit: tokenization, sentence splitting, normalization, stemming,
stopword elimination. Proje planı, kararlar ve ilerleme takibi için **`CLAUDE.md`** tek doğruluk
kaynağıdır — başlamadan önce onu oku.

## Kurulum
```bash
python3 -m pip install -r requirements.txt
```

## Yapı
- `data/UD_Turkish-BOUN/` — birincil korpus (CoNLL-U).
- `resources/` — stopword list, normalization lexicon, suffix lexicon (dış kaynaklar, cite'lı).
- `src/`
  - `io_conllu.py` — CoNLL-U okuyucu + gold token / lemma / frekans yardımcıları (ortak zemin).
  - `tokenizer_baseline.py` — runtime için basit regex tokenizer.
  - `normalization.py` — Ecem.
  - `stemming.py` — Hikmet.
  - `stopword.py` — paylaşımlı.
  - `evaluate.py` — ortak metrikler.
- `reports/` — progress report kaynakları.

## Ortak arayüz
Her task `List[str] -> List[str]`. Çalışma-zamanı zinciri: `normalize -> stopword -> stem`.

## Hızlı test
```bash
python3 src/io_conllu.py      # parser smoke-test
```
# nlp-preprocessing
