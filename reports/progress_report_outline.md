# CMPE 561 — Application Project 1: Progress Report (Group 07)

> İskelet. Serbest stil, 5–10 sayfa, PDF, 20.10.2026 23:59'a kadar e-mail. İçerik sonra
> doldurulacak; köşeli parantezli notlar o bölüme ne gireceğini anlatır.

**Authors:** Hikmet Can Köseoğlu, Ecem Yıldırım — Group 07
**Date:** [tarih]

---

## 1. Introduction
[Problemin ve projenin kısa tanımı: Türkçe için preprocessing toolkit. Beş görev (tokenization,
sentence splitting, normalization, stemming, stopword elimination) tek cümleyle. Bu raporun amacı:
şu ana kadarki ilerleme.]

## 2. Corpora and Resources
[Kullanılan korpuslar ve derlenen kaynaklar + hazırlık durumu.]
- UD Turkish-BOUN (CoNLL-U): boyut (train/dev/test), neyi gold olarak sağladığı.
- Derlenen lexicon'lar: suffix lexicon, normalization lexicon, stopword listesi (kaynak + cite).
- Normalization için gürültülü/sentetik veri hazırlığı.

## 3. Completed Operations
[Tamamlanan üç operasyon. Her alt bölüm: yöntem + kullanılan metrik + farklı test case'lerde
başarı oranı TABLOSU. Hedef %90–95.]

### 3.1 Normalization
[Yöntem (deasciification, case, sayı/noktalama, typo lexicon). Değerlendirme kurulumu
(sentetik gürültü + gerçek test). Sonuç tablosu.]

### 3.2 Stemming
[Yöntem (rule-based suffix-stripping; çekim + yapım ekleri; ünlü uyumu/ünsüz yumuşaması).
UD lemma vs stem notu. Sonuç tablosu.]

### 3.3 Stopword Elimination
[Static (referans liste) + dynamic (korpus metriği). Precision/recall/F1 ile değerlendirme;
static vs dynamic karşılaştırması. Sonuç tablosu.]

## 4. Design of Remaining Operations
[Tokenization ve sentence splitting için KARARLAŞTIRILMIŞ tasarım — henüz implementasyon değil.]

### 4.1 Tokenization
[Rule-based tasarım (URL/email/hashtag/MWE/noktalama). ML tasarım: NB mı LR mı, aday feature set.]

### 4.2 Sentence Splitting
[Rule-based tasarım (EOS işaretleri, kısaltma, tırnak içi EOS). ML tasarım: NB mı LR mı, feature set.]

## 5. Work Plan and Division of Labor
[Kalan iş: iki operasyonun tamamlanması, kapsamlı test, ablation, paper yazımı.
İş bölümü: Hikmet → stemming, Ecem → normalization, stopword → paylaşımlı; sentence/tokenization
sorumlulukları.]

## 6. Acknowledgment of Tool Usage
[LLM'in spell/grammar dışında kullanıldığı yerler ve düzeyi — spec gereği açıkça.]

## References
[UD-BOUN, stopword listesi kaynağı, suffix/normalization lexicon kaynakları, kullanılan araçlar.]
