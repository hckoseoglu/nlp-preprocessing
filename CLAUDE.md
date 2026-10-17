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
  data/normalization/          # elle hazırlanan gerçek gürültülü test seti (Ecem)
  data/external/               # indirilen dış veri + önbellek (gitignore'da; build_lexicon.py üretir)
  resources/                   # stopword list, norm lexicon, SUFFIX lexicon (dış, cite'lı)
  src/
    io_conllu.py               # CoNLL-U parser → cümle/token/lemma/SpaceAfter
    tokenizer_baseline.py      # runtime için basit regex tokenizer
    normalization.py           # token→token (Ecem)
    noise.py                   # sentetik gürültü üretici — normalization eval (Ecem)
    eval_normalization.py      # normalization test-case tabloları (Ecem)
    build_lexicon.py           # normalization lexicon'unu MultiLexNorm'dan üretir (Ecem)
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
    Türkçe train**'den `src/build_lexicon.py` ile otomatik üretiliyor (Çolakoğlu, Sulubacak &
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

## Açık kararlar (netleşince buraya işaretle)
- [ ] NB vs LR hangi task'ta (ön eğilim: NB→splitting, LR→tokenization)
- [x] Stopword sırası → **normalize → stopword → stem** (stem öncesi, yüzey-form). Dynamic
      listeyi stem'lenmiş korpustan üretirsek tekrar gözden geçir.
- [x] İş bölümü: **Hikmet → stemming**, **Ecem → normalization**, **stopword → paylaşımlı**.
- [x] Normalization eval'i → **sentetik gürültü, yalnızca UD-BOUN** + elle hazırlanan küçük
      gerçek gürültülü set (Ecem, 2026-10-16; Hikmet'e bilgi verilecek).
- [ ] Suffix lexicon derleme yöntemi

---

# ORTAK ÇALIŞMA PROTOKOLÜ (Hikmet & Ecem session'ları)
- Bu dosya ortak plandır; iki kişi de aynı planı takip eder. Plan değişikliği önce buraya yazılır.
- Herkes **kendi** task'ında çalışır; ortak dosyalara (io_conllu, evaluate) dokunurken not düşer.
- Her anlamlı ilerlemeden sonra aşağıdaki **İlerleme Takibi** alanı güncellenir (hem insan hem
  agent takip edebilsin). "Next task" ve "Left off here" her zaman güncel tutulur.
- Bir şey tamamlanıp test edildiğinde "Açık kararlar" / takip alanları işaretlenir.

---

# İLERLEME TAKİBİ
> Her progress sonrası güncelle. Tarih ekle. Agent'lar bu alanlara bakarak devam eder.

## Hikmet
- **Next task:** STEMMING. Suffix lexicon'u derle (resources/) → `stemming.py` içinde
  rule-based suffix-stripping; `io_conllu.lemma_pairs` + `evaluate.accuracy` ile ölç.
- **Left off here:** Repo iskeleti kuruldu; `io_conllu.py` çalışıyor (gold token/lemma/frekans).
  `stemming.py` stub hazır, implementasyon bekliyor.
- **Son güncelleme:** 2026-10-16

## Ecem
- **Next task:** (1) **Hocanın cevabını bekle** (2026-10-17 mail atıldı: sentetik test yeterli
  mi, yoksa gerçek gürültü için MultiLexNorm Türkçe **test** kısmı kullanılsın mı?).
  Gerekirse plan: kuralları yalnız MultiLexNorm **train**'de geliştir (hata sayıları, lexicon
  kapalı: yarım Türkçe karakter ~100 — bir kısmı â→a etiketleme farkı; soru eki `yokmu`/`mı`
  uyumu 29; bitişik yazım 191; konuşma dili `gelcem`/`biliyo` 527) → her kuraldan sonra UD
  tablosu düşmemeli → test kısmını en sonda **bir kez** çalıştır, tabloya satır ekle.
  (2) Hikmet'le main'de: 3 kararın onayı (eval yöntemi, Türkçe küçük harf çıktı, lexicon kaynağı).
  (3) Rapor 3.1 normalization bölümü (Ecem yazacak). (4) Lexicon'daki 3 `#?` satırı — opsiyonel.
- **Left off here:** NORMALIZATION çalışıyor + test edildi (`ecem` branch, yerel).
  `python src/eval_normalization.py test` (Windows'ta `PYTHONUTF8=1`). UD-BOUN **test** sonuçları
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
- **Son güncelleme:** 2026-10-17
