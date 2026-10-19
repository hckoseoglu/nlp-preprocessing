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
- **Next task:** (1) Progress report'a stemming bölümünü `results/progress_report_section.md`'den kendi
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
- **Son güncelleme:** 2026-10-19

### Stemming komutları
```
python3 run.py stem --text "Kitapları okuyordum."            # CLI: kitap oku .   (stopword / pipeline / tokenize de aynı yolla)
python3 run.py stem --split dev --eval [--pos]                 # gold token'larda kök doğruluğu (dev %94.1)
python3 src/scripts/stem_build_gold.py                             # lexicon/derived.tsv + results/gold_stats.md
python3 src/scripts/stem_build_roots.py --trmorph <TRmorph klonu>   # lexicon/roots.tsv (+ budama listesi results/roots_pruned.tsv)
python3 src/scripts/stem_build_fragments.py                        # lexicon/copula_fragments.tsv
<venv>/python3 src/scripts/stem_evaluate.py --split dev --ablation  # results/tables_dev.md, errors_dev.tsv (baseline için snowballstemmer, TurkishStemmer)
python3 -m src.stemmer.stemmer kitabı gidiyordum                   # aday analizleri
<venv>/python3 src/scripts/stem_evaluate.py --split dev --pos gold  # isteğe bağlı gold-POS girdisiyle karşılaştırma (üst sınır)
<venv>/python3 src/scripts/stem_figures.py                         # reports/stemming_*.png (9 figür) + results/figures_data.json
<venv>/python3 src/scripts/stem_pseudocode.py                      # reports/stemming_pseudocode.png (sözde kod figürü)
<venv>/python3 src/scripts/stopword_pseudocode.py                  # reports/stopword_pseudocode.png (sözde kod figürü)
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
