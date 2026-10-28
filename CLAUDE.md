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
  run.py                       # TEK GİRİŞ NOKTASI — ince kabuk, src/cli.py'yi çağırır:
                               #   run.py {tokenize|normalize|stopword|stem|pipeline} --text|--file|--split|--conllu [--eval] [--format text|tsv|json]
  src/                         # TÜM KOD BURADA
    cli.py                     # CLI uygulaması
    io_conllu.py               # CoNLL-U parser → cümle/token/lemma/SpaceAfter/MISC
    tokenizer_baseline.py      # runtime için basit regex tokenizer
    normalization.py           # token→token (Ecem): Normalizer, normalize/normalize_tokens
    noise.py                   # sentetik gürültü üretici — normalization eval (Ecem)
    real_data.py               # gerçek gürültülü test setleri: MultiLexNorm test, OSCAR-GEC test (Ecem)
    stemming.py                # token→token (stem) — ince sarmalayıcı → stemmer/ paketi
    evaluate.py                # ortak metrik yardımcıları
    stopword/                  # stopword paketi: core.py (static + dynamic çekirdek; `from stopword import ...`)
    stemmer/                   # STEMMING paketi (Hikmet): stemmer.py suffixes.py morphotactics.py phonology.py lexicon.py
    scripts/                   # KAYNAK ÜRETİMİ + DENEYLER (görev ön-ekli, proje kökünden çalıştırılır):
                               #   stem_gold.py stem_build_{gold,roots,fragments}.py stem_evaluate.py stem_figures.py
                               #   stopword_{evaluate,analyze,extrinsic,build_42bin}.py
                               #   norm_build_lexicon.py (lexicon ← MultiLexNorm train)  norm_evaluate.py [dev|test] (Ecem)
  lexicon/                     # stemmer kaynakları: roots.tsv suffixes.tsv morphotactics.tsv derived.tsv copula_fragments.tsv exceptions.tsv SOURCES.md
  resources/                   # stopword listeleri (static / dynamic / referans), normalization_lexicon.tsv (Ecem)
  tests/                       # test_stemmer.py (72 örnek) test_cli.py (CLI duman testleri)
  results/                     # stemming değerlendirme çıktıları: tables*.md errors_*.tsv gold/roots istatistikleri
  reports/                     # figürler (stemming_*.png, stopword_*.png) + rapor taslakları
  data/UD_Turkish-BOUN/        # korpus
  data/normalization/          # elle hazırlanan gerçek gürültülü test seti (Ecem)
  data/external/               # indirilen dış veri + önbellek (gitignore'da; norm_build_lexicon.py / real_data.py üretir)
```
Kural: kod yalnız `src/` altında (`src/scripts/` deneyler, gerisi import edilen kütüphane); kökte yalnız `run.py`, veri/kaynak
klasörleri ve dokümanlar. Scriptler ve paketler yolu `Path(__file__).resolve().parents[2]` ile proje köküne göre kurar.
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
- (Ecem, 2026-10-16) Detaylar:
  - Çıktı biçimi **Türkçe küçük harf** (İ→i, I→ı; stopword `casefold` + UD lemmalarıyla uyumlu).
    Gold = UD formunun Türkçe küçük harfi. Metrik sadece harf içeren tokenlarda.
  - Test case'ler: temiz (hiç bozulmamış), diakritik silme (tamamı / %30), büyük harf (`KITAP`),
    harf tekrarı, typo, biçim (Unicode/noktalama/sayı-tarih; tüm tokenlarda ölçülür), karışık.
    Dev'de geliştir, **test'te raporla**. Seed her case'in adından türetilir (sabit).
  - Sayı/tarih/noktalama düzeni = Türkçe yazım standardı (TDK; UD de böyle): `16/10/2026 →
    16.10.2026`, `19:30 → 19.30`, `25% → %25`, `… / .. → ...`, `!!! → !`, kıvrık tırnak/kesme →
    düz, Unicode NFC. Ondalık (`1.38` / `1,38`) belirsiz olduğu için dokunulmaz.
  - Her satırda: düzeltmesiz baz skoru + sistem skoru + bozulan tokenları düzeltme oranı +
    bozulmayanları koruma oranı (aksi halde "hiçbir şey yapmayan" sistem de %90 alır).
  - Sözlük/frekanslar **yalnızca UD train**'den. Dış veri ancak skor yetmezse (Ecem kararı).
  - Kısaltma/yazım lexicon'u (`tmm→tamam`) sentetik testte ölçülmez (gürültü aynı lexicon'dan
    üretilirse döngüsel olur) → elle hazırlanan küçük gerçek gürültülü sette ölçülür.
  - (2026-10-16) Lexicon kaynağı: ilk sürüm LLM taslağıydı (cite edilemez) → **MultiLexNorm
    Türkçe train**'den `src/scripts/norm_build_lexicon.py` ile otomatik üretiliyor (Çolakoğlu, Sulubacak &
    Tantuğ 2019, ACL SRW; van der Goot et al. 2021, W-NUT). Doğru biçimler UD train ya da TDK
    Güncel Türkçe Sözlük ile doğrulanır; doğrulanamayanlar `#?` (elle kontrol). MultiLexNorm
    **test** bölümüne dokunulmadı (hoca gerçek gürültü testi isterse kullanılabilir).
    `.gitignore`'a `data/external/` eklendi (ortak dosya — Ecem notu).
    Sonuç: **22 aktif** giriş (UD/TDK doğrulamalı), 3 `#?`. Seçim kuralları: yalnız "yaygın"
    hatalar (≥2 farklı tweet; plandaki "yaygın yazım-hata lexicon'u"), doğru kelimelerle karışanlar
    elenir (kader, olum/ölüm, bende), tek seferlik typo, süs karakterli yazım (αcı), küfür ve
    '#'i düşmüş hashtag'ler (kelime ortasında büyük harf: MaliyeAtama) alınmaz. İlk denemede 187
    giriş vardı ama çoğu tek seferlik/garip olduğu için elendi.
    UD test'te lexicon açık/kapalı fark yok (lexicon kelimeleri UD test'te hiç geçmiyor — domain
    farkı). BÜYÜK HARFLİ ≤4 harfli token'lar (TM, ABD) kısaltma sayılır, lexicon'a girmez.
  - (2026-10-18) **Gerçek gürültü testi** — hoca cevabı: "MultiLexNorm'u kullanabilirsiniz; yapay
    hatalara ek olarak gerçek bir veri iyi olur; haber metni de olabilir ama doğrusu elle
    hazırlanmalı." Hazır, elle düzeltilmiş haber verisi bulunamadı (HF, Boğaziçi, İTÜ, Koç, Sabancı
    tarandı; ITU Web Treebank izinle alınıyor, yetişmez). Karar (Ecem): iki gerçek test seti,
    **yalnızca test** (ayar yapılmaz, `norm_evaluate.py test` içinde bir kez çalıştırılır;
    dev'de gösterilmez), lexicon açık (train'den üretildi, testler hiç görülmedi), normalizer kodu
    değişmez:
    - **MultiLexNorm Türkçe test** (tweet, Çolakoğlu et al. 2019).
    - **OSCAR-GEC test** (web metni: haber parçası, forum, yorum; Ersoy & Yıldız 2024,
      arXiv:2405.15320; HF `asimokby/Turkish-GEC-Evaluation`, MIT). Gramer düzeltme (GEC) verisi.
    Puanlama kuralları (sonuç görülmeden sabitlendi): ortak → harf içermeyen token, @mention,
    #hashtag, URL puanlanmaz. MultiLexNorm → birleştirme (2+ token → 1 kelime) parçaları
    puanlanmaz, bölme (yokmu → yok mu) puanlanır. OSCAR-GEC → düzeltilmemiş tokenlar puanlanır
    (koruma); bir kaynak tokene dokunan düzeltme, iki taraftaki ayrı noktalama tokenları atıldıktan
    sonra (a) yalnızca büyük/küçük harf, Türkçe karakter ya da kelime bölme farkıysa (etiketten
    bağımsız; "o -> . O" dahil) veya (b) tek kelime → tek kelime olup etiketi SPELL/ORTH/OTHER ve
    ASCII-katlanmış Damerau-Levenshtein uzaklığı ≤ 2 ise puanlanır; diğerleri (dilbilgisi
    NOUN/VERB/..., kelime değişimi/ekleme, birleştirme, silme) puanlanmaz. Çoklu token düzeltmesi
    kelime sayısı eşitse kelime kelime değerlendirilir. (Kural, sistem çalıştırılmadan önce veri
    örneklerine bakılarak bir kez inceltildi: "o -> . O" kapsama alındı, "calisiyor -> çalışıyor
    ve" dışarıda bırakıldı.)

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

> **DURUM 2026-10-18 — TAMAMLANDI (v2): dev %94.1 / test %94.0** (tek sefer ölçüldü), lexical %94.3; baseline'lar
> no-stem 44, prefix-5 47, Snowball 54, TurkishStemmer 55. Uygulanan tasarım aşağıdaki plandan şu noktalarda
> **değişti** (karar: `~/Desktop/cmpe561/stemmer_superprompt_v3.md`):
> - İki-mod (A/B) yerine **tek gold**: UD lemma + tip-seviyesi tutarlı `DerivedFrom` köküne indirgeme
>   (`src/scripts/stem_gold.py`; kabul: ≥2 destek, tipin ≥%50'si DerivedFrom'lu, ön-ek, kök de lemma). Mod B kök test seti
>   "sonraki adım".
> - **Kök sözlüğü KULLANILIYOR**: TRmorph (MIT) + UD train kökleri (`lexicon/roots.tsv`, 26 269 satır); Eryiğit & Adalı
>   sözlüksüz "en kısa kök" kuralı over-stemming yaptığı için seçim **log-frekans skoru** (en uzun kök %89.3 →
>   korpusta-görülen-önce %91.5 → skor %94.1).
> - Ek sözlüğü artık `lexicon/suffixes.tsv` (Oflazer notasyonu, 111 şablon → 541 allomorf) + `morphotactics.tsv`
>   (13 durum FSA, ters DFS). `resources/suffixes_tr.txt` ve `src/eval_stemming.py` kaldırıldı.
> - Değerlendirme: `src/scripts/stem_evaluate.py --split dev [--ablation]` veya `run.py stem --split dev --eval`; test **yalnız bir kez** çalıştırıldı — tekrar
>   çalıştırma gerekirse raporda belirt. Tüm tablolar `results/tables.md`, rapor taslağı
>   `results/progress_report_section.md`, kaynaklar `lexicon/SOURCES.md`.
> - Ortak dosya notu: `src/io_conllu.Word`'e `misc` alanı eklendi (geriye uyumlu, default "_").

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

## STOPWORD — DETAYLI PLAN (paylaşımlı)
- **static**: dış genel-domain liste (stopwords-iso MIT / POS-kategorili tkorkunckaya GPL / HF 504).
  Henüz indirilmedi. Gerekçe cite: Can et al. 2008, Metin & Karaoğlan 2017.
- **dynamic**: **Achsan, Suhartanto, Wibowo, Dewi & Ismed (2023), IJACSA 14(2), TF-IDF yöntemi.**
  - Doküman = **pseudo-doküman ≈ 20 cümle** (BOUN'da makale sınırı yok). Cümle granülerliği tf-idf'i
    bozuyor (stopword "tüm dokümanlarda" varsayımı tutmaz) → gruplama şart.
  - **Seed'li shuffle** ile gruplama (ardışık cümleler aynı kaynaktan = bağımlı; df/idf için bağımsızlık).
  - En düşük koleksiyon-TF-IDF'li K kelime = stopword. tfidf = (Σ tf / df)·log(N/df).
  - `idf` varyantı ablation olarak tutulur (tf-idf ≈ idf çıktı).
- **Eval**: UPOS-proxy gold (kapalı-sınıf: ADP/AUX/CCONJ/SCONJ/DET/PRON/PART) → token-level P/R/F1.
  K dev'de F1 ile seçilir (elbow değil). static ∪ dynamic birleşimi en iyi beklenir (Lo et al. 2005).
- **Durum (dev):** dynamic TF-IDF K=75 → **F1=0.713** (P=0.696, R=0.731); idf ablation 0.712.
  Kod: **`src/stopword/`** paketi (core.py) + `src/scripts/stopword_{evaluate,analyze,extrinsic,build_42bin}.py`, liste `resources/stopwords_tr.txt`.
  CLI: `run.py stopword --text "..." [--list static|dynamic|union|intersection]`, `run.py stopword --split dev --eval`.
  Görseller: `reports/stopword_*.png`. static(467)/dynamic(75)/union/∩ karşılaştırması `evaluate.py`'de
  (test F1: static 0.735, dynamic 0.724, union 0.726/en yüksek recall, ∩ 0.736/en yüksek precision).
  Artefakt: `du/dı/ken` AUX kopula parçaları (UD multi-word split) — filtrelenebilir.
  Not: F1 %90 değil; UPOS-proxy + sadece-dynamic sınırı. static + union + metrik tartışması kaldı.

## Açık kararlar (netleşince buraya işaretle)
- [ ] NB vs LR hangi task'ta (ön eğilim: NB→splitting, LR→tokenization)
- [x] Stopword sırası → **normalize → stopword → stem** (stem öncesi, yüzey-form). Dynamic
      listeyi stem'lenmiş korpustan üretirsek tekrar gözden geçir.
- [x] İş bölümü: **Hikmet → stemming**, **Ecem → normalization**, **stopword → paylaşımlı**.
- [x] Normalization eval'i → **sentetik gürültü, yalnızca UD-BOUN** + elle hazırlanan küçük
      gerçek gürültülü set (Ecem, 2026-10-16; Hikmet'e bilgi verilecek).
      (2026-10-18, hoca onayı) + gerçek gürültü: MultiLexNorm Türkçe test (tweet) + OSCAR-GEC
      test (web metni). Elle hazırlanan haber seti opsiyonel (final'e).
- [x] Suffix lexicon derleme yöntemi → **elle, Oflazer (1994) notasyonu**; kaynaklar Göksel & Kerslake, Sak vd.,
      Eryiğit & Adalı (`lexicon/suffixes.tsv`, `lexicon/SOURCES.md`)
- [x] Stemming: Mod A + Mod B yerine **tek gold** (UD lemma + tip-seviyesi DerivedFrom indirgeme); Mod B kök seti → sonraki adım
- [x] Stemming: kök sözlüğü → **TRmorph (Çöltekin 2010, MIT) + UD train kökleri**, UD lemma gürültüsü budanmış
- [x] Stemming: ana metrik = **gold kök exact-match accuracy** (dev %94.1 / test %94.0); POS + alt küme kırılımları raporlanır

---

# PLAN — FAZ 2: FİNAL TESLİM (28 Eki → 3 Kas 2026, 23:59 Moodle)

> Durum 28 Eki: progress report gönderildi (bölüm 4'teki tasarım başlangıç noktası; kötü karar varsa değiştirilir,
> değişiklik paper'da bir cümleyle gerekçelendirilir). Kalan: tokenization +
> sentence splitting (rule + ML), 5 görevde kapsamlı test + ablation, system paper (4–6 sayfa, kurs şablonu),
> work-sharing dokümanı, kod zip'i, demo. **6 iş günü var → kapsam disiplini şart.**

## Rapordaki tasarım (bölüm 4) — başlangıç noktası
- Tokenization: rule-based (URL, e-mail, hashtag, sayı `19.30'da`, kısaltma `Dr.`, kesmeli `Ankara'ya` tek token;
  gerisi ayrılır; kısaltma listesi TDK Yazım Kılavuzu, MWE listesi UD-BOUN) + **Logistic Regression (scikit-learn)**,
  3 feature seti: (1) sınıra komşu karakterler, (2) geniş karakter penceresi, (3) kısaltma/sayı/URL bilgisi.
  Metrik P/R/F1; 3 test case: tüm UD test · zor durumlar · URL/e-mail/hashtag (UD'de yok → kendimiz ekleriz).
- Splitting: rule-based (kısaltma / baş harf / sıra sayısı sonrası bölme yok; tırnak içi noktalamadan sonra küçük
  harfle devam ediyorsa bölme yok; aksi halde sonraki kelime büyükse böl) + **Naïve Bayes (kendi implementasyonumuz)**,
  3 feature seti: (1) noktalama + sonraki kelime büyük/küçük, (2) önceki kelime kısaltma/sayı mı, (3) önceki kelimenin
  son karakterleri (-dı, -yor). Metrik P/R/F1; 3 test case: tüm UD test · zor durumlar · tamamı küçük harf.
- Korpus: raporda "train'den 7 610 splitting + 22 713 tokenization aday noktası" dendi → aynı tanımla yeniden üretilir.

## Rapor kararlarının değerlendirmesi (28 Eki) — KORUNAN / DEĞİŞEN
- **KORUNDU: LR → tokenization, NB → splitting.** Tokenization'da aday çok (on binlerce) ve karakter özellikleri
  birbirine bağımlı → NB'nin bağımsızlık varsayımı bozulur, LR doğru; splitting'de aday az, özellikler kategorik ve
  sayıca az → kendi yazacağımız NB için en güvenli görev. Ters çevirmenin kazancı yok.
- **DEĞİŞTİ (metrik, splitting):** train'de aday noktaların %89'u "böl" (7 161 cümle-sonu vs 906 cümle-içi; içlerinin
  412'si `:`/`;`, 143'ü tırnak-içi `."`/`?"`/`!"`). "Böl" sınıfının P/R/F1'i "her noktada böl" baseline'ında bile ~0.94
  → raporda yalnız o verilirse anlamsız. Yeni rapor biçimi: her iki sınıfın P/R/F1 + **macro-F1** + cümle-bazında
  exact match, ve **"her noktalamada böl" baseline'ı** tabloda. Zor-durum seti (tırnak-içi EOS, kısaltma, sıra sayısı)
  başlık sonuç olarak öne çıkar.
- **DEĞİŞTİ (MWE kaynağı):** "MWE listesi UD-BOUN'dan" → UD'de boşluklu token yok; liste **deprel'lerden** üretilir:
  `fixed` (ya da, hem de, ne var ki; 15 tip), `compound:redup` (yavaş yavaş; 395), `compound:lvc` (yardım et; 1 015),
  isteğe bağlı `flat` (çok parçalı özel ad; 1 617). MWE birleştirme **ayrı, isteğe bağlı katman** (`--mwe`): UD token
  eval'inde kapalı, kendi P/R/F1'i gold deprel span'larına karşı ayrı tabloda. Dış liste gerekmez (cite: UD-BOUN).
- **DEĞİŞTİ (feature setleri iç içe):** her görevde set 1 ⊂ set 2 ⊂ set 3 (kümülatif) → ablation "bilgi eklendikçe"
  okunur; raporda "üç set karşılaştırılacak" sözü aynen tutulur.
- **KORUNDU:** test case'ler (UD test · zor durumlar · URL/e-mail/hashtag sentetik; splitting'de · tamamı küçük harf),
  rule-based tanımlar, kısaltma listesi TDK. Tokenization zor-durum seti **gerçek** (UD'deki `."`, `.)`, `2.`,
  `yerde"nin`, `G.Saray`), sentetik değil.

## Veriden gelen tasarım gerçekleri (28 Eki ölçümleri)
- `src/tokenizer_baseline.py` dev'de **cümle-bazında %95.8 birebir** (938/979). Kalan hatalar UD-BOUN sözleşmeleri:
  `."` ve `.)` tek token, sıra sayısı `2.` tek token, `G.Saray`, `yerde"nin` gibi tırnak-içi ek. → Rule-based tokenizer =
  baseline + bu sözleşmeler + kısaltma/URL/e-mail/hashtag katmanı. %90–95 hedefi zaten aşılıyor; iş, özel varlıklar +
  ML karşılaştırmasında.
- Tokenization gold = `Sentence.tokens` (yüzey token; MWT'ler birleşik: `yılındayız` tek token, 2 914 MWT train'de).
  Aday nokta tanımı: `# text` içinde boşluk olmayan iki komşu karakter arasında, en az biri harf/rakam olmayan her
  konum → etiket = gold token sınırı mı. Boşluk her zaman sınır (UD'de boşluklu token YOK → MWE birleştirme UD
  eval'inde KAPALI; MWE lexicon'u ayrı küçük elle test setiyle gösterilir, raporda "UD'de yok" notuyla).
- Splitting: UD `sent_id`'leri tür/doküman bakımından karışık sıralı (`bio_9, ins_1282, ess_1145, …`) → ardışık
  cümleler doküman oluşturmaz. **Sahte paragraf**: seed'li karıştırma + ardışık 5 cümleyi birleştir (gold sınırlar
  bilinir). Aday = `. ! ? … : ;` + isteğe bağlı kapanış tırnağı/parantez, ardından boşluk. Noktalamasız biten cümleler
  (dev'de ~%1: `ler`, `yor`) ve `:`/`,` ile bitenler (dev 26/979) aday dışı → recall kaybı olarak **dürüstçe sayılır**,
  ayrıca "noktalamayla biten" alt kümesi raporlanır. Tırnaklı cümle train'de 1 091 (zor-durum seti için yeterli).
  UD'de nokta ile biten kısaltma çok az (gr., kg., vs.) → kısaltma zor-durum seti TDK listesiyle **sentetik** eklenir.
- Metrikler: her iki görevde aday-nokta sınıflaması için boundary P/R/F1 (pozitif sınıf = böl) + tokenization için
  token-span F1, splitting için cümle-bazında exact match. Dev'de ayar, **test bir kez**.

## Kod planı (hepsi `src/`, stdlib + scikit-learn yalnız LR için)
```
src/tokenization/           rules.py (RuleTokenizer: regex + kısaltma/MWE lexicon)  features.py (3 feature seti)
                            ml.py (LRTokenizer: aday nokta → böl/bölme; sklearn LogisticRegression)  corpus.py (aday çıkarımı)
src/splitting/              rules.py (RuleSplitter)  features.py (3 feature seti)  ml.py (NBSplitter)  corpus.py (sahte paragraf)
src/ml/naive_bayes.py       kendi Multinomial/Bernoulli NB (Laplace, log-uzay) — splitting'de kullanılır
src/scripts/tok_evaluate.py / split_evaluate.py   results/tables_tok_*.md, tables_split_*.md (+ ablation = feature setleri)
src/scripts/tok_build_special.py                  URL/e-mail/hashtag sentetik test seti (UD cümlelerine ekleme)
resources/abbreviations_tr.txt (TDK, cite)  resources/mwe_tr.txt (UD-BOUN `# text`/dış kaynak, cite)
tests/test_tokenizer.py  tests/test_splitter.py  tests/test_naive_bayes.py
```
- **Sıra kararı (28 Eki): önce splitter, sonra tokenizer.** Splitter ham metinde çalışır (aday = noktalama + boşluk;
  önceki/sonraki kelime = boşluk sınırlarıyla), tokenizer her cümleyi ayrı tokenize eder. Gerekçe: iki görev bağımsız
  ölçülür (tokenizer hatası cümle sınırına sızmaz), tokenizer zaten cümle-düzeyi `# text` üzerinde eğitilir/ölçülür,
  iki kişi paralel başlar. Paylaşılan parçalar yalnız `resources/abbreviations_tr.txt` ve `src/textutil.py`
  (Türkçe büyük/küçük harf, `is_abbreviation`, `is_number`); bunlar ilk gün yazılır, iki taraf da import eder.
- CLI: `run.py tokenize --method rule|ml`, yeni `run.py split --text|--file [--method rule|nb]`, ve **doküman modu**
  `run.py pipeline --doc dosya.txt` = split → tokenize → normalize → stopword → stem (demo "dokümanı girdi alır" diyor).
  `--eval` her ikisinde de çalışır.
- Ortak dosyalara (cli.py, io_conllu.py, evaluate.py) dokunan not düşer; `src/ml/` ve eval tabloları Hikmet'in.

## İş bölümü (ÖNERİ — Ecem onaylayınca [x] yapılır)
- [ ] **Hikmet → sentence splitting** (rule + NB kendi implementasyonu) + sahte paragraf korpusu + `run.py split`/
      `--doc` pipeline + demo dosyası + tüm görevlerin final tablolarını toplama + paper iskeleti/stemming/stopword/
      splitting bölümleri + zip.
- [ ] **Ecem → tokenization** (rule + LR) + kısaltma/MWE lexicon'ları + URL/e-mail/hashtag sentetik seti + paper
      normalization/tokenization bölümleri + work-sharing dokümanı taslağı.
- Gerekçe: NB'yi sıfırdan yazmak + korpus kurmak altyapı işi (CLI/eval zaten Hikmet'te); tokenization'ın regex tabanı
  hazır ve LR sklearn ile hızlı, Ecem'in token-düzeyi normalizer'ıyla doğal komşu. Tersi de olur; önemli olan bugün
  karar verip başlamak.

## Literatür — hangi çalışma ne için (28 Eki, sabitlendi; paper'da bu rollerle cite edilir)
**Sentence splitting (Hikmet)**
| Çalışma | Kullanım |
|---|---|
| Reynar & Ratnaparkhi 1997 (ANLP) | Problem çerçevesi: her `. ? !` aday, ikili sınıflandırma; Candidate/Prefix/Suffix + sol/sağ kelime özellikleri; kısaltma listesinin **train'den otomatik türetilmesi** (feature set 2'nin veri-güdümlü alternatifi) |
| Gillick 2009 (NAACL) | `L. R` biçimi; `len(L)` ve `cap(R)` özellikleri (set 1–2); **NB'nin yeterliliği** (NB %0.35 vs SVM %0.25 hata); elle kısaltma listesinin ML'de zarar verebileceği uyarısı; kümülatif ablation tablo biçimi; çoğunluk-sınıfı baseline |
| Güz, Favre, Hakkani-Tür & Tur 2009 (IEEE TASLP) | Türkçe'de **morfolojik özelliklerin** cümle bölmeye katkısı → feature set 3'ün (önceki kelimenin son harfleri) gerekçesi |
| Bektaş & Özel 2018 (ASYU) | Türkçe emsal: TNC'den 30 000 aday, NB dahil 5 klasik sınıflandırıcı; sonuç kıyası ve "kural tabanlı çalışmalardan özellik türetme" gerekçesi |
| Kiss & Strunk 2006 (CL) — Punkt | Related work (kısaltma = ana zorluk; gözetimsiz alternatif). **NLTK Punkt Türkçe modeli = dış baseline** (kod kopyalanmaz, araç olarak cite) |
| Palmer & Hearst 1997 (CL) — SATZ | Related work: POS/sözlük tabanlı yaklaşım; bizde POS yok, gerekçe |
| Safaya et al. 2022 — Mukayese (TRSEG-41) | Related work: Türkçe modern benchmark; derin modeller kapsam dışı (spec yasağı). Zaman kalırsa ek "başka genel-domain metin" testi |
| Jurafsky & Martin, SLP3 böl. 2 ve 4 | NB tanımı, Laplace, log-uzay; cümle bölmenin sınıflandırma olarak kurulması — **kendi NB implementasyonunun referansı** |
| McCallum & Nigam 1998 | Bernoulli vs multinomial NB (ikili özelliklerle Bernoulli/kategorik seçimi) — opsiyonel |
| Read et al. 2012 (COLING) | Related work: "çözülmüş problem mi?" → zor durum/tür bazlı değerlendirme gerekçesi — opsiyonel |
| TDK Yazım Kılavuzu, Kısaltmalar Dizini | `resources/abbreviations_tr.txt` kaynağı (rule-based'de kural, ML'de özellik) |
| Türk et al. 2022 (UD-BOUN) | Korpus; cümle/tokenization sözleşmeleri; sahte paragraf kurgusunun dayanağı |

**Tokenization (Ecem) — şimdiden sabitlenen**
| Çalışma | Kullanım |
|---|---|
| Jurafsky & Martin SLP3 böl. 2 | Regex tabanlı tokenization, Treebank tarzı sözleşmeler; ML tokenization'ın sınır sınıflandırması olarak kurulması |
| Türk et al. 2022 + UD v2 kılavuzu (Nivre et al. 2020) | Gold token tanımı, MWT/klitik, `SpaceAfter`; `fixed`/`flat`/`compound` → MWE lexicon'u |
| Sag et al. 2002 | MWE tanımı ve neden ayrı katman ("pain in the neck") |
| Pedregosa et al. 2011 | scikit-learn LogisticRegression (zaten referansta) |
| Akın & Akın 2007 — Zemberek | Türkçe kural tabanlı tokenizer emsali; opsiyonel dış baseline |
| Gimpel et al. 2011 / O'Connor et al. 2010 (twokenize) | URL/hashtag/mention regex sözleşmeleri için related work — opsiyonel |

Kural: tablo dışına çıkan cite gerekiyorsa önce buraya eklenir. Dış araç yalnız **baseline** olarak (NLTK Punkt, Snowball gibi), kod kopyalanmaz.

## Takvim
| Gün | İş |
|---|---|
| **28 Eki (bugün)** | Plan onayı (Ecem). `hikmet` → `main` merge, Ecem `main`'den yeni branch. Paket iskeletleri + aday-nokta/sahte-paragraf korpus kodu + sayıların rapordaki 7 610 / 22 713 ile tutması. Paper şablonunu Moodle'dan indir (Overleaf). |
| **29 Eki** | Rule-based tokenizer (UD sözleşmeleri + kısaltma/URL/e-mail/hashtag) ve rule-based splitter; dev tabloları. Kısaltma listesi (TDK). |
| **30 Eki** | ML: NB sınıfı + NB splitter 3 feature seti; LR tokenizer 3 feature seti; dev'de karşılaştırma + hata analizi. |
| **31 Eki** | Zor-durum setleri (tırnak, kısaltma, sıra sayısı, küçük harf; URL/e-mail/hashtag; MWE mini set). CLI `split` + `--doc` pipeline + testler. **Test split bir kez** (tok + split). |
| **1 Kas** | Kapsamlı test + ablation tabloları 5 görev için (normalization bayrak ablation'ı dahil), **uçtan uca satır** (UD test ham `# text` → kendi splitter+tokenizer → normalize → stopword → stem, gold'a hizalanıp ölçülür; görev tabloları gold token'da kalır — spec görev başına metrik istiyor), figürler, demo metni (genel-domain haber + URL/hashtag) ile uçtan uca prova. **Kod dondurulur**, README güncellenir, zip. |
| **2 Kas** | System paper (4–6 sayfa, şablon): progress report'tan sıkıştırma + yeni iki görev + ablation; work-sharing dokümanı; LLM acknowledgment. |
| **3 Kas** | Son okuma, sayfa sınırı, referans kontrolü, 3 dosya Moodle'a **23:59'dan önce** (öğleden sonra hedef). |

## Riskler / kısıtlar
- Zaman: ML kısmı 30 Eki'de kapanmazsa feature seti 3'ü "basit sürüm"le kapat, ablation'ı tablo olarak yine ver.
- Paper 4–6 sayfa (ek hariç): progress report ~10 sayfa → tablolar birleştirilmeli, sözde kod figürleri ek'e.
- Demo hocanın kendi metinleriyle: `--doc` modu ham metinde (kesme/tırnak/URL) sağlam olmalı; ek-fiil tablosu yalnız
  dataset modunda (zaten böyle).
- Ecem'in branch'i 18 Ekim'den beri `hikmet`'in gerisinde → merge önce yapılmalı, yoksa iki tokenizer/CLI çakışır.

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
- **Next task (28 Eki, FAZ 2):** Hikmet'in onayı bekleyen kararlar (aşağıda), sonra: `hikmet` → `main` merge; Ecem'e tokenization
  başlangıcı (textutil + abbreviations_tr hazır); `pipeline --doc` doküman modu; test split **bir kez** (31 Eki); tablolar + paper.
- **SPLITTING DURUMU (28 Eki) — ilk sürüm çalışıyor, dev ölçüldü, commit edilmedi.** Kod: `src/splitting/` (corpus, features,
  rules, ml), `src/ml/naive_bayes.py` (kendi NB), `src/textutil.py`, `src/scripts/split_evaluate.py`, `split_build_abbrev.py`,
  `resources/abbreviations_tr.txt` (TDK dizininden 159 noktalı kısaltma), `resources/splitter_nb.json` (set 3 modeli),
  `data/splitting/challenging_abbrev.txt` (elle, 41 paragraf), `tests/test_{naive_bayes,splitter}.py` (20 test OK), CLI `run.py split`.
  Dev (sahte paragraf 5 cümle, seed 2; aday 809, böl 714 / bölme 95), aday acc / macro-F1 / cümle exact:
  always-split 0.917 / 0.752 / 0.799 · rule 0.910 / 0.798 / 0.766 · NB1 0.926 / 0.787 / 0.805 · **NB2 0.942 / 0.841 / 0.815** ·
  NB3 0.925 / 0.816 / 0.788. Zor durum (170 aday): rule 0.835, NB2 0.841. **Küçük harf:** rule 0.151 (hiç bölmez), NB1 0.206,
  NB2 0.733, **NB3 0.786** → ek bilgisi (set 3) büyük harf olmayınca tek sinyal. Elle kısaltma seti (87 aday): rule 0.954, NB3 0.954,
  always 0.494. NB α taraması (dev): set 2 duyarsız; set 3 α=2 → 0.934 / 0.835.
  **TEST (28 Eki, BİR KEZ çalıştırıldı; sahte paragraf 5, seed 3; aday 838, böl 718 / bölme 120; erişilemeyen sınır 65/783 = %8.3;
  şüpheli negatif 34):** aday acc / macro-F1 / cümle exact — always 0.911 / 0.788 / 0.789; NB1 0.928 / 0.819 / 0.822; NB3 0.916 / 0.825 / 0.787; **rule 0.918 / 0.835 / 0.775 · NB2 0.932 / 0.843 / 0.816 ·
  Punkt 0.890 / 0.778 / 0.754**. Zor durum (184): rule 0.842, NB2 0.848, Punkt 0.652. Küçük harf: rule 0.172, NB2 0.723,
  Punkt 0.878. Tam tablo `results/tables_split_test.md`; tekrar çalıştırma gerekirse paper'da belirt.
  **Bulgular / Hikmet'in karar vereceği noktalar:**
  (a) Gold gürültüsü: dev'de 31 negatif (train'de 293/906) `. ! ?` + büyük harfle devam ediyor — UD iki cümleyi tek birimde
      tutmuş ("nelerdir? Tartışınız."). Dahil mi, "şüpheli gold" alt kümesi olarak ayrı mı raporlanır? (şimdilik dahil, sayı tabloda)
  (b) Gold sınırların %8.8'i (69/783) noktalamasız/virgülle biten UD cümleleri (tarif malzeme satırları, başlıklar) → hiçbir
      noktalama tabanlı splitter bulamaz; sınır-düzeyi recall'da FN sayılıyor, tabloda ayrıca belirtiliyor.
  (c) [KARAR 28 Eki] CLI dev'de macro-F1'i en yüksek seti kullanır (şu an **set 2**; `split_evaluate.py` kaydeder); set 3'ün küçük
      harf kazancı ve α duyarlılığı paper'da discussion'a.
  (d) [28 Eki] NLTK Punkt (tr) dış baseline kuruldu: proje venv'i `.venv/` (gitignore'da; `python3 -m venv .venv &&
      .venv/bin/python3 -m pip install -r requirements.txt`, Punkt verisi `nltk.download('punkt_tab')`, ~/nltk_data, Türkçe 640K).
      `split_evaluate.py` nltk bulursa Punkt satırını ekler, bulamazsa sessizce atlar. Punkt tırnaklı cümleleri parçalıyor
      (`"Neden gelmedin?" | diye sordu.`) — paper'da kısa bir not.
  Önceki liste (arşiv): (1) Progress report'a stemming bölümünü `results/progress_report_section.md`'den kendi
  kelimelerimizle aktar (Google Doc), tabloları `results/tables.md`'den al; (2) stopword static+union+metrik
  tartışmasını bitir; (3) tokenization/splitting tasarım kararları (NB vs LR). Stemming'de küçük kalanlar: `suy→su`
  istisnası, kesmesiz büyük harfli OOV özel adlar (dev'de 45 token), isteğe bağlı POS girdisi.
- **Left off here:** `hikmet` branch, **henüz commit edilmedi** (çalışma ağacında: run.py, stemmer/, lexicon/, scripts/, tests/,
  results/, README, CLAUDE.md, src/stemming.py sarmalayıcı, src/io_conllu.py misc; silinen: src/eval_stemming.py,
  resources/suffixes_tr.txt). **2026-10-19 repo düzeni:** tüm kod `src/` altında (`src/stemmer/`, `src/scripts/` görev ön-ekli
  `stem_*`/`stopword_*`, `src/cli.py`); eski `scripts/evaluate.py`↔`src/evaluate.py` ad çakışması giderildi; **`run.py` CLI** eklendi (cümle/dosya/split üzerinde tokenize·normalize·stopword·stem·pipeline,
  `--eval`, `--format text|tsv|json`); `tests/test_cli.py` eklendi. **2026-10-19 merge:** `origin/ecem` (normalization) `hikmet`'e merge edildi; Ecem'in iki scripti
  `src/scripts/norm_build_lexicon.py`, `src/scripts/norm_evaluate.py` adıyla taşındı (kütüphane modülleri `src/normalization.py`,
  `src/noise.py`, `src/real_data.py` yerinde); `run.py normalize|pipeline` artık gerçek normalizer'ı çağırıyor; `norm_evaluate.py dev`
  doğrulandı. STEMMING v2 TAMAM ve ölçüldü:
  - dev **%94.1** (NOUN 94.5 / VERB 91.8 / ADJ 89.2 / PROPN 93.0; derived 94.7; OOV 87.0), test **%94.0** (tek sefer).
  - Baseline dev: no-stem 44.1 · prefix-5 46.7 · Snowball 53.9 · TurkishStemmer 54.7.
  - Hata profili dev: 593 hata / 543 farklı — over 36 %, under 36 %, türetim-fazla 12 %, kopula-parçacığı 6 %
    (gold'da iki sözleşme), belirsizlik 3 %. Uzun kuyruk + bağlamsız belirsizlik (doğan, çalışan, gelin).
  - Testler: `python3 -m unittest tests.test_stemmer` (OK, 70+ örnek).
  - **POS girdili sürüm** (`stem(word, pos=UPOS)`: fiil/isim ağı süzme + aynı-POS bonusu): dev 94.5 / test 94.2 — gold POS
    yalnız +0.4/+0.2; kalan hatalar bağlamsız belirsizlikten çok UD/TRmorph sözlükselleşme farkı + gold gürültüsü.
    Figürler: `reports/stemming_{system_comparison,pos_breakdown,subsets,ranking_ablation,error_classes,pos_filtered_eval,rule_only_pos_effect,snowball_pos}.png`;
    rapor figürü (Tablo 7'nin yerine, yalnız test): `reports/stemming_test_breakdown.png`. Google Doc'ta Tablo 6 → tek cümle, Tablo 7 → Figure 1 (görsel elle eklenecek).
  - **Kural-only + POS deneyi** (`Stemmer.rule_stem`, sözlüksüz): Snowball 53.9 → +fiil kuralı POS'suz 57.6 → +gold POS 63.4
    (dev). POS 4–6 puan, sözlük+skor ~30 puan katıyor → Snowball'un zayıflığı POS'suzluktan değil sözlüksüzlükten.
- **Son güncelleme:** 2026-10-28

### Stemming komutları
```
python3 run.py stem --text "Kitapları okuyordum."            # CLI: kitap oku .   (stopword / pipeline / tokenize de aynı yolla)
python3 run.py stem --split dev --eval [--pos]                 # gold token'larda kök doğruluğu (dev %94.1)
python3 src/scripts/stem_build_gold.py                             # lexicon/derived.tsv + results/gold_stats.md
python3 src/scripts/stem_build_roots.py --trmorph <TRmorph klonu>   # lexicon/roots.tsv (+ budama listesi results/roots_pruned.tsv)
python3 src/scripts/stem_build_fragments.py                        # lexicon/copula_fragments.tsv
.venv/bin/python3 src/scripts/stem_evaluate.py --split dev --ablation  # results/tables_dev.md, errors_dev.tsv (baseline için snowballstemmer, TurkishStemmer)
python3 -m src.stemmer.stemmer kitabı gidiyordum                   # aday analizleri
.venv/bin/python3 src/scripts/stem_evaluate.py --split dev --pos gold  # isteğe bağlı gold-POS girdisiyle karşılaştırma (üst sınır)
.venv/bin/python3 src/scripts/stem_figures.py                         # reports/stemming_*.png (9 figür) + results/figures_data.json
.venv/bin/python3 src/scripts/stem_pseudocode.py                      # reports/stemming_pseudocode.png (sözde kod figürü)
.venv/bin/python3 src/scripts/stopword_pseudocode.py                  # reports/stopword_pseudocode.png (sözde kod figürü)
python3 -m unittest tests.test_stemmer tests.test_cli          # testler
```
TRmorph klonu depoda değil (`git clone https://github.com/coltekin/TRmorph`, commit fbceb11); roots.tsv üretilmiş halde depoda.

## Ecem
- **Next task:** (1) Rapor 3.1'e gerçek gürültü satırlarını ekle (Ecem yazıyor). (2) Hikmet'le
  main'de: kararların onayı (eval yöntemi + gerçek gürültü setleri, Türkçe küçük harf çıktı,
  lexicon kaynağı, plandaki test türleri için eklenen harf tekrarı + typo adımları).
  (3) Opsiyonel / final'e: elle düzeltilmiş küçük haber seti (`data/normalization/real_noisy.tsv`);
  iyileştirmeler yalnız MultiLexNorm **train**'de geliştirilir (yarım Türkçe karakter `bır`/
  `Gecmiş`, kelime bölme `oteldede → otelde de`, sözlüğü diğer UD Türkçe setleriyle büyütme) →
  UD tablosu düşmemeli; gerçek test setleri yeniden çalıştırılırsa raporda belirtilir.
  (4) Lexicon'daki 3 `#?` satırı — opsiyonel.
- **Left off here:** NORMALIZATION çalışıyor + test edildi (`ecem` branch, yerel).
  `python src/scripts/norm_evaluate.py test` (Windows'ta `PYTHONUTF8=1`). UD-BOUN **test** sonuçları
  (sistem accuracy / bozulan tokenları düzeltme):
  temiz 98.3% · diakritik(tümü) 96.3% / 94.9% · diakritik(%30) 97.7% / 95.2% ·
  büyük harf 97.7% / 96.8% · harf tekrarı 98.2% / 98.2% · typo(%10) 94.2% / 46.5% ·
  biçim 98.6% / 99.3% · karışık 95.2% / 89.0%. Sayı/tarih/noktalama düzeni eklendi (planın
  normalization bileşenleri tamam). Zayıf nokta: typo düzeltme. Dev analizi: bozulan kelimelerin ~%35'i
  Türkçe'ye benzediği için fark edilmiyor, ~%30'unun doğrusu UD train sözlüğünde yok, ~%2.5'i
  başka gerçek kelimeye dönüşüyor. "Kök + ek" geçerlilik kontrolü eklendi (%35 → %46).
  Daha fazlası için dış kelime listesi gerekir (Hikmet'le konuşulacak). Bileşenler
  `Normalizer(...)` bayraklarıyla kapatılabilir (ablation hazır). Ayarlar dev'de seçildi
  (typo_margin=2.0, typo_min_freq=30, min_stem=2, min_end=2, ctx_size=4, min_ctx=1).
  (2026-10-17) Tablo yeniden çalıştırıldı, sayılar aynı; lexicon script'i birebir aynı dosyayı
  üretiyor. Gerçek gürültü ön izlemesi (MultiLexNorm **train**, lexicon kapalı, rapora girmez):
  %80.08 doğruluk.
  (2026-10-18) Hoca gerçek veriyi önerdi → `src/real_data.py` + `norm_evaluate.py test`'e iki
  satır; **bir kez** çalıştırıldı (normalizer değişmedi, UD satırları aynı). Sonuç (baz / sistem /
  düzeltme / koruma): **web (OSCAR-GEC test)** 78.0% / **90.1%** / 64.3% / 97.4% (54.728
  token, 12.035'i bozuk; 5.072 token kapsam dışı düzeltme yüzünden puanlanmadı) · **tweet
  (MultiLexNorm test)** 66.0% / **79.3%** / 47.6% / 95.7% (1.234 token). Lexicon katkısı: web
  +0.2, tweet +0.8 puan. Hata dağılımı (web): Türkçe karakter %32 (gerçek metinde `bır`,
  `gerçegı` gibi yarım/yanlış Türkçe harf), typo/kısaltma/konuşma dili %31, doğruyu bozma %21,
  kelime bölme %16 (sistem bölmüyor). Tweet: konuşma dili/kısaltma %55, kelime bölme %17.
- **Son güncelleme:** 2026-10-18
