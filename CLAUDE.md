# CMPE 561 — Application Project 1: Turkish Preprocessing Toolkit

> Bu dosya projenin **tek doğruluk kaynağı (source of truth)** ve ortak çalışma planıdır.
> Hem Hikmet'in hem Ecem'in Claude session'ları bu planı takip eder. Değişiklik gerektiğinde
> önce buna yazılır, sonra uygulanır. Her ilerlemeden sonra en alttaki **İlerleme Takibi**
> alanları güncellenir.

## Progress report (yazım)
Google Doc: https://docs.google.com/document/d/17us7o9sWcMksMo_VYhHR-i3A4QS82oYJtnTyMJwZeJA/edit
(PDF olarak export edilip 20.10.2026 23:59'a kadar e-mail ile gönderilecek.)

## Ana kaynak (source of truth — gereksinimler)
**`/Users/hikmetcankoseoglu/Desktop/cmpe561/Application Project 1.pdf`** — Projenin tüm
gereksinimleri bu dokümandan gelir. Kapsam/karar tartışmalarında bu doküman belirleyicidir.
Diğer kaynaklar (slaytlar, makaleler) `~/Desktop/cmpe561/` altındadır.

## Takım
- Hikmet Can Köseoğlu (koseogluhikmetcan@gmail.com)
- Ecem Yıldırım
- Group 07

## Dil / teknoloji
- Hedef dil: **Türkçe** (Erasmus değiliz).
- Tüm kod **Python**. Kaynak kodun tamamı bize ait olmalı; dış kaynaklar ve araçlar açıkça
  cite edilmeli.

---

## Kapsam — 5 preprocessing görevi
1. **Tokenization** — rule-based **ve** ML-based (iki tokenizer). Özel varlıklar: URL, hashtag,
   e-mail, MWE. ML için feature set'ler elle tasarlanır.
2. **Sentence splitting** — rule-based **ve** ML-based (iki splitter). Tırnak içi EOS vb. zor
   durumlar. Feature set'ler elle tasarlanır.
3. **Normalization** — genel domain (haber vb.), domain'e özgü değil.
4. **Stemming** — tüm çekim (inflectional) ekleri + geniş yapım (derivational) eki kapsamı.
5. **Stopword elimination** — **static** (önceden tanımlı liste) **ve** **dynamic** (korpustan
   metriklerle üretilen liste), genel domain.

### ML kısıtı
- Tokenization ve sentence splitting için: biri **Naïve Bayes** (kendimiz implement edeceğiz),
  diğeri **Logistic Regression** (scikit-learn kullanılabilir). Hangi görevde hangisi? → **KARAR
  BEKLİYOR**, rapor yazımından hemen önce netleşecek (ön eğilim: NB→splitting, LR→tokenization).
- Başka klasik ML veya deep learning YASAK. Her iki görev de farklı feature set'lerle test
  edilip başarı oranları karşılaştırılacak.

### Başarı kriteri
- Her 5 görevde en az **%90–95 başarı**. Her görev için uygun metrik, farklı test case'lerde
  raporlanır.

## Veri
- Birincil: **UD Turkish-BOUN** (CoNLL-U) → `data/UD_Turkish-BOUN/`.
  - train: 7803 cümle / 100.713 token · dev: 979 · test: 979
  - Gold olarak verdikleri: `# text =` (cümle sınırı + detokenization), token sınırları +
    `SpaceAfter=No` (tokenization), **3. kolon = lemma** (stemming eval), UPOS (stopword filtre).
- Gerekli yerlerde dış veri (normalization için gürültülü/sosyal medya verisi veya sentetik
  gürültü; MWE/suffix/normalization/stopword lexicon'ları).

## Teslimler ve tarihler (STRICT)
- **Progress report** — **20.10.2026 23:59**, PDF, **e-mail ile**. 5–10 sayfa, serbest stil.
  Bu tarihte ~%70–80 tamam olmalı: korpuslar hazır; **normalization + stemming + stopword
  tamamlanmış ve test edilmiş**; tokenization + splitting **tasarımına karar verilmiş**.
  Aksi halde proje "incomplete".
- **Final (Moodle)** — **03.11.2026 23:59**: kod (zip), system paper (PDF, 4–6 sayfa konferans
  formatı, course web page template'i), work-sharing dokümanı (PDF, kişi bazında kim ne yaptı).
- Demo: her grup için ayrıca ayarlanacak; genel domain metinleriyle de test edilecek.

## LLM kullanım politikası
- Rapor/paper kendi kelimelerimizle yazılacak. LLM'i spell/grammar dışında kullanırsak, kullanım
  düzeyi rapor/paper sonunda **acknowledgment** olarak açıkça belirtilmeli.
  (Örnek log: `~/Desktop/cmpe561/AI_Usage_Log_Mishra2011.md`.)

---

# PLAN

## Roadmap (sıralı aşamalar — tarih yok, hedef rapor: 20 Eki)
1. **Zemin:** CoNLL-U okuyucu, gold token/lemma/frekans çıkarımı, ortak `token→token` arayüzü;
   dış kaynakların toplanması; iş bölümünün netleşmesi.
2. **Stemming + Normalization:** ilk çalışan sürüm + eval harness.
3. **Stopword** (static + dynamic): üç task'ın başarı tabloları, %90–95'e iterasyon.
4. **Tokenization + splitting tasarımı** + progress report PDF + e-mail.

Darboğaz riski: normalization için gürültülü test verisi — erken çözülmezse tıkanır.

## Repo yapısı
```
nlp-preprocessing/
  data/UD_Turkish-BOUN/        # indi
  resources/                   # stopword list, norm lexicon, SUFFIX lexicon (dış, cite'lı)
  src/
    io_conllu.py               # CoNLL-U parser → cümle/token/lemma/SpaceAfter
    tokenizer_baseline.py      # runtime için basit regex tokenizer
    normalization.py           # token→token
    stemming.py                # token→token (stem)
    stopword.py                # static + dynamic
    evaluate.py                # her task için metrik + test-case tabloları
  reports/                     # progress report kaynakları
```
Ortak sözleşme: her task `List[str] -> List[str]` (veya detay taşıyan Token nesnesi).
Çalışma-zamanı zinciri: **`normalize → stopword → stem`** (default). Stopword eleme tipik
pipeline'da normalization sonrası, stemming **öncesi** gelir: stopword listeleri yüzey-form'dur,
Türkçe stopword'ler de çoğunlukla çekimsiz işlev sözcükleri olduğundan stem'lemeden önce elemek
standart ve güvenli. İstisna: dynamic stopword'ler stem'lenmiş korpustan üretilirse eleme de
stem sonrası tutulur.

## Tokenizer stratejisi (önemli)
- **Dev/eval**: üç rapor-task'ı UD **gold token'ları** üstünde geliştirilir → bu üç task'ın
  başarısı tokenizer kalitesine bağlı kalmaz.
- **Runtime (ham metin)**: basit **regex baseline tokenizer** (whitespace + noktalama ayırma).
  Saf whitespace-split YETERSİZ (Türkçe'de noktalama kelimeye yapışık). Gerçek rule-based + ML
  tokenizer rapor sonrasına.

## Task bazında yöntem + metrik (nasıl %90–95)
**Normalization** — deasciification (`gelecegim→geleceğim`), case normalizasyonu, sayı/tarih/
noktalama düzeni, yaygın yazım-hata lexicon'u.
- Eval: UD temiz metne **sentetik gürültü** enjekte et (diakritik silme, tekrar harf, typo) →
  (gürültülü, temiz) çiftleri; token-level accuracy. + küçük gerçek gürültülü test seti.

**Stemming** — rule-based suffix-stripping (longest-match; çekim + geniş yapım ekleri; ünlü uyumu,
ünsüz yumuşaması alomorfları). Kendimiz yazıyoruz.
- Eval: çıktı vs UD lemma, accuracy. Uyarı: stem≠lemma — raporda belirtilir.

**Stopword** — static: dış referans liste (cite'lı); dynamic: UD train'den frekans + metrik
(TF, entropi/varyans, Zipf vb.) ile aday üretimi.
- Eval: üretilen liste vs referans → precision/recall/F1; static vs dynamic karşılaştırması.

## Tokenization & splitting — sadece *tasarım* (rapora)
- Tokenizer: rule-based (URL/email/hashtag/MWE/sayı/noktalama regex'leri, UD `SpaceAfter`
  referansı) + ML (split-noktası split/no-split sınıflama, elle feature'lar).
- Splitter: rule-based (EOS işaretleri + kısaltma listesi + tırnak içi EOS) + ML (aday sınır
  noktası boundary/değil; feature: önceki token, sonraki kelime büyük harf mi, kısaltma mı...).

## Dış kaynaklar (hepsi cite'lı)
- **Suffix lexicon — ZORUNLU** (opsiyonel değil). Spec ismen istiyor + rule-based stemmer'ın
  çekirdeği. Düz liste yetmez: çekim/yapım katmanlaması, ünlü uyumu ve ünsüz yumuşaması
  alomorfları gerekir. Derleme yöntemi (elle / dilbilgisi kaynağından cite ile) ayrı kalem.
- Türkçe stopword listesi · normalization/typo lexicon · (opsiyonel) MWE lexicon ·
  normalization için gürültülü örnek metin.

## Progress report iskeleti (serbest stil, 5–10 sayfa, PDF, e-mail)
1. Giriş / problem & kapsam (5 task)
2. Korpuslar ve kaynaklar (UD-BOUN + derlenen lexicon'lar, hazırlık durumu)
3. Tamamlanan 3 operasyon: yöntem + **metrik + test-case başarı tabloları**
4. Tokenization & splitting **tasarım kararları** (rule-based + ML; NB vs LR; feature taslakları)
5. Kalan iş planı & iş bölümü
6. (gerekiyorsa) LLM-kullanım acknowledgment

## STEMMING — DETAYLI PLAN (Hikmet, `hikmet` branch)

### Amaç
Her Türkçe kelimeyi, **tüm çekim (inflectional)** eklerini ve **geniş bir yapım (derivational)**
eki kümesini soyarak kök/gövdesine indiren, kendi yazdığımız **rule-based suffix-stripping**
stemmer. Hedef ≥%90–95.

### Temel tasarım kararı: lemma mı, kök mü? (iki mod)
Gold'umuz UD lemma; ama UD lemma genelde **çekimi atıp yapımı KORUR** (`gözlük→gözlük`,
`kitapçı→kitapçı`). Spec ise "geniş yapım eki" soymayı istiyor (`gözlük→göz`). Bu gerilimi iki
modla çözüyoruz:
- **Mod A — Lemmatization (eval default):** sadece çekim eklerini soy → UD lemma ile eşleş.
  Ana metrik buradan gelir, %90–95 hedefi buna.
- **Mod B — Aggressive root stemming:** çekim + yapım eklerini soy → köke yaklaş. UD lemma ile
  birebir eşleşmez; ayrı **elle etiketli kök test seti** ile ölçülür. IR-tarzı pipeline'da bu mod.

### Referans kural seti (SEÇİLDİ)
**Eryiğit & Adalı (2004), "An Affix Stripping Morphological Analyzer for Turkish"** (IASTED, İTÜ).
Başlıkta "analyzer" geçse de **sözlük/POS/kök-sözlüğü KULLANMIYOR** → bizim lexicon-free crude
stemmer tanımımıza uyuyor. Fiili ciddiye alan tek aday: ayrı fiil FSM'leri (zaman/görünüş/kip,
olumsuzluk -mA, yeterlilik -Abil, çatı -Il/-In/-Iş/-DIr, ortaç/ulaç -An/-DIk/-ArAk/-Ip/-UncA,
kişi ekleri). Ek envanteri makalede yayınlı: Tablo 3/5/6/7/8 = **117 jenerik ek → ~519 allomorf**
(U=ı/i/u/ü, A=a/e, C=c/ç, D=d/t, ()=opsiyonel). Python'a yeniden yazıp **cite ederiz** (kod
kopyalamadan; GPL yok). Makale **accuracy vermiyor** → sayıyı kendimiz hedef-hizalı gold ile ölçeriz.
Mekanikler (ünlü uyumu testi, min-hece, ünsüz yumuşaması) **Snowball Türkçe (BSD-3)** referanslı.
Tam metin lokalde kayıtlı (tool-results). Baseline: Snowball + fixed-prefix-5 + no-op.

### Yöntem (algoritma)
Sağdan-sola affix stripping (morfotaktik sıra) + morfofonemik onarım + "son kabul durumu"
(longest-valid-affix) ile over-stemming guard'ı. Kök sözlüğü YOK (hocanın "stemming lexicon
kullanmaz" tanımına ve Eryiğit&Adalı yaklaşımına sadık).

### Ele alınacak morfofonemik olaylar (kod, data değil)
- **Ünlü uyumu** (a/e; ı/i/u/ü) — ek alomorfları.
- **Ünsüz yumuşaması** (p/ç/t/k → b/c/d/ğ): `kitabı`→soy→`kitab`→geri-kurgu→`kitap`.
- **Ünsüz türemesi/ikizleşme**: `hakkı`→`hak`, `sırrı`→`sır`.
- **Yardımcı ünsüzler** (y, n, s, ş): `arabası`, `suyu`.
- **Ünlü düşmesi**: `burnu`→`burun`, `ağzı`→`ağız`.
- Özel adlar / yabancı kelimeler için istisna.

### İhtiyaçlar (kaynaklar — hepsi cite'lı, resources/)
- **Suffix lexicon (ZORUNLU):** çekim + yapım ekleri, kategorili (isim/fiil çekimi, yapım),
  katmanlama sırası, alomorflarıyla. Kaynak: Türkçe dilbilgisi + mevcut stemmer ek envanterleri
  (Zemberek/Çilden vb. **sadece ek listesi için referans**, kod kopyalamadan).
- **Kök sözlüğü (wordlist):** over-stemming'i önlemek + doğru geri-kurgulama için Türkçe kök
  listesi (dış kaynak, cite). Olmazsa saf stripping aşırı soyar.
- **İstisna/irregular listesi** (opsiyonel ama faydalı).
- **Eval verisi:** UD lemma çiftleri (var: `io_conllu.lemma_pairs`) + Mod B için küçük elle
  etiketli kök test seti.

### Metrikler
- **Ana:** UD lemma'ya karşı **exact-match accuracy** (Mod A), dev + test ayrı. Hedef %90–95.
- **Gevşek (ikincil):** stem/lemma **overlap** (ör. gold lemma, çıktının prefix'i mi) — aşırı
  cezalandırmayı görmek için.
- **Mod B:** elle etiketli kök setinde accuracy (ayrı raporlanır).
- **POS/ek-türü kırılımı:** hata analizi (isim vs fiil, çekim vs yapım).

### Baseline'lar (rapordaki "farklı test case" karşılaştırması için)
- No-stemming (kelime=kök varsayımı) — alt sınır.
- Fixed-prefix (ilk N=5 karakter) — ucuz Türkçe stemmer baseline'ı.
- Sadece-çekim-soyma vs çekim+yapım — kendi modlarımızın karşılaştırması (ablation).

### Riskler
- Over-stemming (kök sözlüğü yoksa) · morfofonemik geri-kurgu hataları · UD lemma'daki `null`/
  kopula artıkları (filtreleniyor) · stem≠lemma kavramsal farkı (raporda açıkça belirtilir).

## Açık kararlar (netleşince buraya işaretle)
- [ ] NB vs LR hangi task'ta (ön eğilim: NB→splitting, LR→tokenization)
- [x] Stopword sırası → **normalize → stopword → stem** (stem öncesi, yüzey-form). Dynamic
      listeyi stem'lenmiş korpustan üretirsek tekrar gözden geçir.
- [x] İş bölümü: **Hikmet → stemming**, **Ecem → normalization**, **stopword → paylaşımlı**.
- [ ] Normalization eval'i için sentetik-gürültü yaklaşımı onaylandı mı?
- [ ] Suffix lexicon derleme yöntemi (elle / mevcut envanterden cite'la)
- [ ] Stemming: Mod A + Mod B iki-mod yaklaşımı onaylandı mı?
- [ ] Stemming: kök sözlüğü (wordlist) kaynağı seçimi
- [ ] Stemming: ana metrik = UD lemma exact-match accuracy onaylandı mı?

---

# ORTAK ÇALIŞMA PROTOKOLÜ (Hikmet & Ecem session'ları)
- **Branch kuralı (ZORUNLU):** Hikmet her zaman `hikmet` branch'inde çalışır, Ecem kendi
  branch'inde — conflict olmasın. `main`'e doğrudan commit yok; işler branch'te yapılır,
  birleştirme PR/merge ile. Her oturum başında doğru branch'te olduğunu kontrol et
  (`git branch --show-current`).
- Bu dosya ortak plandır; iki kişi de aynı planı takip eder. Plan değişikliği önce buraya yazılır.
- Herkes **kendi** task'ında çalışır; ortak dosyalara (io_conllu, evaluate) dokunurken not düşer.
- Her anlamlı ilerlemeden sonra aşağıdaki **İlerleme Takibi** alanı güncellenir (hem insan hem
  agent takip edebilsin). "Next task" ve "Left off here" her zaman güncel tutulur.
- Bir şey tamamlanıp test edildiğinde "Açık kararlar" / takip alanları işaretlenir.

---

# İLERLEME TAKİBİ
> Her progress sonrası güncelle. Tarih ekle. Agent'lar bu alanlara bakarak devam eder.

## Hikmet
- **Next task:** STEMMING v1 — over-stemming'i dizginle. Öncelik: (1) morfotaktik sıralı soyma
  (her slot'tan en fazla bir ek: nominal case→poss→çoğul; verbal kişi→zaman→olumsuzluk),
  (2) ünlü uyumu kısıtı, (3) morfofonemik onarım (kitab→kitap, gözlüğ→gözlük). Sonra re-eval.
- **Left off here:** `hikmet` branch. STEMMING v0 YAZILDI ve ölçüldü:
  - `resources/suffixes_tr.txt` (düz ek listesi), `src/stemming.py` (iteratif longest-match,
    kalan>1 harf), `src/eval_stemming.py` (exact-vs-lemma, POS kırılımı + baseline).
  - dev sonuç: bizim v0 **0.314** | no-op 0.463 | fixed-prefix-5 0.464 | **snowball 0.561**.
  - POS: NOUN bizim 0.281 / snow 0.720 ; ADJ 0.254/0.701 ; **VERB bizim 0.333 / snow 0.150 (geçtik)**.
  - Teşhis: OVER-stemming baskın (2383 over / 52 under). Suçlu: tek-harfli ünlü ekleri + kısa
    ünsüzler + kısıt (uyum/morfotaktik) yokluğu.
- **Son güncelleme:** 2026-10-16

### Stemming değerlendirme komutu
`<venv>/python3 src/eval_stemming.py [dev|test|train]`  (baseline için snowballstemmer gerekli;
scratchpad venv'inde kurulu. Projeye eklenecekse requirements'a `snowballstemmer` ekle.)

## Ecem
- **Next task:** NORMALIZATION. normalization lexicon'u derle (resources/) → `normalization.py`;
  sentetik gürültü ile (gürültülü, temiz) çiftleri oluştur, `evaluate.accuracy` ile ölç.
- **Left off here:** Repo iskeleti hazır; `normalization.py` stub seni bekliyor. Ortak zemin
  (`io_conllu.py`, `evaluate.py`) kullanıma hazır.
- **Son güncelleme:** 2026-10-16
