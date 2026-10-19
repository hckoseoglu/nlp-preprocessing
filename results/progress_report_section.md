# Stemming (Hikmet Can Köseoğlu) — progress report bölümü taslağı

> Kaynak dosyalar: `src/stemmer/` (kod), `lexicon/` (veri + `SOURCES.md`), `src/scripts/` (üretim/değerlendirme),
> `results/tables.md` (tüm tablolar), `results/errors_dev.tsv` (tüm hatalar). Sayılar 2026-10-18 itibarıyla.

## 1. Amaç ve kapsam

Türkçe isim ve fiilleri **köküne kadar** soyan, tüm çekim eklerini ve yaygın türetim eklerini kaldıran, sözlük
biçimi döndüren bir stemmer: `kitabı→kitap`, `gidiyordum→git`, `öğretmenlerimizin→öğretmen`, `önemliydi→önem`,
`öldürülen→öl`. Yalnız Python 3 standart kütüphanesi; tüm kod bize ait. Başarı ölçütü: UD Turkish-BOUN dev/test'te
kök accuracy ≥ %90.

## 2. Yöntem

Ders slaytındaki (Slide03 s.23) üç bileşen aynen var: **lexicon** (kök sözlüğü), **morphotactics** (ek sırası FSA'sı),
**orthographic/phonological rules** (ses değişimi onarımları ve kısıtları).

**Çatı: Eryiğit & Adalı (2004) affix stripping şeması.** Ek-sıralama FSA'sı *ters* yürütülür: kelime **sondan başa**
soyulur; allomorflar program başında şablonlardan üretilir (`(I)mIz → mız miz muz müz ımız imiz umuz ümüz`); kök
sınırında ses değişimleri geri alınır. Tür baştan verilmez: `END` durumundan hem isim hem fiil ağına girilir, türü
soyulan ekler + bulunan kök belirler. Arama DFS/backtracking ile, `(durum, kalan, sağ bağlam)` üçlüsü üzerinden
memoize edilir (10k token/0.4 s).

**Eryiğit & Adalı'dan farkımız: kök sözlüğü + frekans-ağırlıklı seçim.** Makale sözlüksüz çalışır ve "en kısa kökü"
seçer; bu kural sözlükle birleştirilince aşırı soyar (`kalem→kale`, `gelin→gel`; prototipte dev %22–54). Biz
TRmorph (Çöltekin 2010) + BOUN-train köklerinden bir **kök sözlüğü** kurduk ve seçimi üç aşamada geliştirdik
(dev, genel accuracy): sözlükte **en uzun kök** %89.3 → önce korpusta görülen kökler, sonra en uzun %91.5 →
**log-frekans skoru %94.1**. Skor:

    skor = min(ln(freq+1), 5) + 0.5·|kök| − Σ ek maliyeti − 0.5·#onarım − 5·uyum-ihlali + 1·[tam sözcük, korpusta var]
    ek maliyeti: çekim 0.7 · çatı 1.0 · isim-fiil/sıfat-fiil 1.0 · türetim 3.0

Gerekçe: saf en-uzun-kök, UD lemma gürültüsünden gelen sahte kökleri (`insanlar`, `beni`) ve nadir uzun kökleri
(`evin`, `bun`) seçiyordu; frekans tavanı (`bir`, `de`, `o` gibi çok sık kökler her şeyi yutmasın) ve tam-sözcük bonusu
(`biri`, `deniz`, `kim`) kalan iki sistematik hatayı kapattı. Ağırlıklar dev'de küçük bir grid ile seçildi; yüzey düz
(%93.2–%93.9 arası), yani sonuç ağırlıklara duyarlı değil.

**Kısıtlar (soyma sırasında):** (1) kaynaştırma — `y/s/n/ş` tamponlu allomorf yalnız ünlüden sonra, ünlü tampon
(`(I)m`) yalnız ünsüzden sonra; (2) ünlü uyumu — ekin ilk arşifonem ünlüsü gövdenin son ünlüsüyle uyumlu olmalı
(yumuşak: ihlal cezalandırılır, `inv_harmony` bayraklı köklerde — `saat-i`, `alkol-ü` — serbest); (3) ünsüz
benzeşmesi — `D→t`, `C→ç` yalnız sert ünsüzden sonra; (4) `K` sonlu ekler (`-(y)AcAK`, `-DIK`, `-lIK`) `ğ` ile yalnız
ünlü önünde (`geleceğ-im`).

**Onarımlar (kök sınırında, yalnız ünlüyle başlayan ek soyulduğunda):** yumuşama `kitab→kitap`, `gid→git`,
`reng→renk`; ünlü düşmesi `burn→burun`, `ağz→ağız`, `kayd→kayıt`; ikizleşme `hakk→hak`; `-yor` daralması
`bekli→bekle`, `di→de`; `de-/ye-` + y `diye→de`. Onarım, eşleşen kökün TRmorph/UD bayrağıyla (`voicing`,
`vowel_drop`, `doubling`) uyumlu olmalı — ayrı istisna listesi yok.

**Özel yollar:** kesme işaretli büyük harfli sözcük → yalnız isim çekimi soyulur, kök sözlükte olmalı
(`Tesisleri'nde→tesis`, `İstanbul'daki→İstanbul`); korpusta özel ad olarak görülmüş büyük harfli tam sözcük →
dokunulmaz; UD'nin ayrı sözcük olarak böldüğü ek-fiil parçacıkları (`du`, `ydı`, `ken`, `dır`, `ise`) kural-tabanlı
üretilen 506 biçimlik tabloyla UD lemma sözleşmesine (`y`/`i`) eşlenir; sözlükte kök bulunamazsa (OOV) ≥2 harfli
geçerli ekler katı ünlü uyumuyla soyulur, büyük harfliyse dokunulmaz.

**Türetim politikası.** Çok sık (sözlükselleşmiş) türetimler korunur, görülmemiş olanlar soyulur: `öğretmen`
(korpusta 38 kez) kalır, `gözlüğü→göz`, `kuduzlu→kuduz`. Ayrıca train'den öğrenilen tip-seviyesi eşleme
(`derived.tsv`, 524 lemma: `önemli→önem`, `hastalık→hasta`, `araştırmacı→araştırma→araştır`) seçilen köke uygulanır.

## 3. Kaynaklar (`lexicon/SOURCES.md`)

| dosya | içerik | boyut |
|---|---|---|
| `roots.tsv` | TRmorph 12 sözlük dosyası (MIT) + BOUN train gold kökleri (frekanslı); bayraklar: voicing / vowel_drop / inv_harmony / doubling / derived | 26 269 (kök, POS) satırı, 24 154 yüzey; 1 590 tek-örnek POS gürültüsü ve 211 lemma-gürültüsü kökü (`beni`, `insanlar`, `olma`) budandı |
| `suffixes.tsv` | Oflazer (1994) notasyonuyla elle yazılan ek şablonları: isim çekimi, ek-fiil, fiil çekimi (çatı, olumsuz, yeterlik, 10 zaman/kip, bileşik zaman, emir, kişi, isim-/sıfat-/zarf-fiil), 20 türetim eki | 111 şablon → 541 allomorf |
| `morphotactics.tsv` | Çöltekin (2010) Fig. 1–2 / Oflazer Fig. B.1–B.2 sade hali; türetim kök durumları arası geçiş | 13 durum, 42 geçiş (10 ε) |
| `derived.tsv` | BOUN `DerivedFrom` tip-seviyesi eşlemesi (gold tanımının parçası) | 579 tip (25 zincirli); stemmer yalnız train'de görülen 524 lemma'yı kullanır |
| `copula_fragments.tsv` | ek-fiil parçacıkları (kural üretimi + train ile çakışma giderme) | 506 biçim |
| `exceptions.tsv` | düzensiz zamir biçimleri (`bana`, `onlar`), `mı/mu/mü→mi`, `kü→ki`, `iler→ileri` | 14 satır |

Baseline'lar: no-stem, fixed-prefix-5, Snowball Türkçe (Çilden 2006; `snowballstemmer`), `TurkishStemmer` (pip).

## 4. Gold tanımı

İçerik tokeni: UPOS ∉ {PUNCT, SYM, NUM, X}, lemma `null` değil (dev 10 020, test 9 906 token). **gold = LEMMA**
(küçük harf, şapka düzleştirme, `din(I)→din`), ancak `(LEMMA, UPOS)` tipi için MISC `DerivedFrom` **tip seviyesinde
tutarlıysa** gold = DerivedFrom kökü: train+dev+test'te çoğunluk oyu; kabul koşulları kök ≥2 harf, LEMMA'nın ön-eki
(son ünsüz p/b ç/c t/d k/ğ toleransı), korpusta kendisi de lemma, ≥2 token desteği ve tipin tokenlerinin ≥%50'si
DerivedFrom taşıyor (bu oran olmadan `yıl→yı` 10/329, `öğretmen→öğret` 4/38 gibi gürültü gold'a giriyordu). Kök de
türetilmişse zincirlenir (≤3 adım; PROPN ve <3 tokenli tipler zincire girmez). Sonuç: 2 461 DerivedFrom'lu tipten 579'u
kabul; dev'de 302, test'te 241 token lemma'dan farklı kök alır. Karşılaştırma küçük harf duyarsız (PROPN lemmaları büyük
harfli).

## 5. Sonuçlar (accuracy %, `results/tables.md`)

| | genel | lexical¹ | NOUN | VERB | ADJ | PROPN | bare | inflected | derived | OOV² |
|---|---|---|---|---|---|---|---|---|---|---|
| **dev — bizim** | **94.1** | 94.3 | 94.5 | 91.8 | 89.2 | 93.0 | 96.6 | 91.9 | 94.7 | 87.0 |
| dev — Snowball | 53.9 | 55.2 | 68.9 | 14.9 | 57.5 | 64.1 | 69.4 | 43.9 | 3.0 | 48.5 |
| dev — TurkishStemmer | 54.7 | 56.0 | 73.7 | 12.3 | 63.9 | 55.9 | 70.4 | 43.2 | 28.1 | 46.2 |
| dev — fixed-prefix-5 | 46.7 | 47.8 | 43.5 | 22.2 | 51.2 | 38.5 | 76.6 | 22.9 | 25.8 | 28.2 |
| dev — no-stem | 44.1 | 45.2 | 35.3 | 2.2 | 72.7 | 65.9 | 100.0 | 0.0 | 0.0 | 19.0 |
| **test — bizim** (tek sefer) | **94.0** | 94.3 | 94.7 | 91.0 | 91.6 | 94.1 | 96.4 | 92.0 | 92.5 | 87.7 |
| test — Snowball | 53.9 | 54.9 | 68.5 | 14.9 | 54.8 | 62.8 | 69.1 | 43.8 | 1.2 | 47.5 |

¹ ek-fiil parçacıkları (dev 241, test 180 token; UD lemma `y`/`i` sözleşmesi) dışında. ² form train'de görülmemiş.

**İsteğe bağlı POS girdisi (üst sınır):** `stem(word, pos=UPOS)` verilince adaylar fiil/isim ağına göre süzülür ve
sözlük POS'u eşleşen kök bonus alır. Gold POS ile dev **94.5**, test **94.2** (POS'suz 94.1 / 94.0): VERB 91.8→93.0,
under-stemming hataları 213→170 (`doğan→doğ`, `çalışan→çalış`, `alan→al`); derived alt kümesi 94.7→93.0 düşer. Kazanç
küçük olduğu için kalan hataların çoğu bağlamsız POS belirsizliği değil, UD–TRmorph sözlükselleşme farkı ve gold
gürültüsüdür. Figürler: `reports/stemming_{system_comparison,pos_breakdown,subsets,ranking_ablation,error_classes}.png`
(`src/scripts/stem_figures.py`).

**Snowball ile adil karşılaştırma (POS ile süzülmüş token kümeleri, stemmer'a POS verilmeden):** yalnız NOUN tokenlerinde
Snowball 68.9 / TurkishStemmer 73.7 / bizim 94.5 (dev); isim sınıfı (NOUN+PROPN+ADJ+PRON+ADV) 64.6 / 67.3 / 94.0; yalnız VERB
14.9 / 12.3 / 91.8. Figür: `reports/stemming_pos_filtered_eval.png`.

**Kural-only sistemde POS'un etkisi:** Snowball'a sözlüksüz fiil kuralları (bizim fiil ek envanteri + FSA) eklenip gold POS
ile yönlendirilince dev 53.9 → 63.4 (POS'suz birleşim 57.6); VERB 14.9 → 58.7. Sözlüksüz fiil soyma ~59'da tavan yapıyor;
sözlük + skor 94.1. Figür: `reports/stemming_rule_only_pos_effect.png`.

**Ablation (dev):** kopula tablosu kapalı −2.1; `derived.tsv` eşlemesi kapalı −1.2 (derived alt kümesi 94.7→56.3);
türetim soyma kuralları kapalı −0.5 (derived 94.7→54.0, OOV +1.6); ünlü uyumu / kaynaştırma / benzeşme / onarım
bayrakları kapalı ±0.1 — ses kısıtları doğruluğu değil çözümleme hızını ve aday sayısını etkiliyor, seçimi sözlük +
skor yapıyor. OOV stratejileri (dokunma / en kısa / en uzun gövde) ±0.2.

## 6. Hata analizi (dev: 593 hata, 543 farklı; `results/errors_dev.tsv`)

| sınıf | % | tipik örnek (form → gold / bizim) |
|---|---|---|
| over-stemming | 36 | `yoksun→yoksun/yok`, `gelin→gelin/gel`, `sıradan→sıradan/sıra`, `ümraniye→ümraniye/ümran` |
| under-stemming | 36 | `doğan→doğ/doğan`, `çalışan→çalış/çalışan`, `yeter→yet/yeter`, `yitirmiş→yit/yitir`, `belirtti→belir/belirt`, `hepsi→hep/hepsi` |
| türetim fazla soyuldu (gold lemma'yı korur) | 12 | `öğretmenlik→öğretmenlik/öğretmen`, `anlatıcı→anlatıcı/anlat`, `refahlı→refahlı/refah` |
| UD kopula parçacığı (gold'da iki sözleşme) | 6 | `sa→i/y` (train: 101 y, 16 i), `ken→i/y`, `tir→y/i` |
| belirsizlik (iki geçerli kök) | 3 | `ardından→art/ardından`, `örneğin→örnek/örneğin`, `kalbi→kalbi/kalp` |
| OOV kök / typo / gold gürültüsü | 4 | `cifte→çifte`, `milli→mil`, `suyunu→su/suyunu` |

Kalan hatalar **uzun kuyruk** (543 farklı hatanın 500'ü tek token) ve büyük ölçüde **bağlamsız belirsizlik**:
`doğan`, `çalışan`, `alan`, `gelir`, `giderek` hem sözlükselleşmiş isim/sıfat hem fiil sıfat-fiili; UD bağlama göre
etiketler, bağlamsız stemmer korpustaki daha sık okumayı seçer. İkinci grup UD lemma politikasıyla TRmorph'un
sözlükselleşme kararlarının çatışması: UD çatı eklerini her zaman soyar (`yitir→yit`, `belirt→belir`, `alın→al`)
ama `geliş`, `karış` gibi kökleri kendi lemma'sı sayar; `w_voice=1` bu ikisi arasındaki dengenin dev'de en iyi noktası.
Üçüncü grup gold gürültüsü (`suyunu` lemma'sı 4 kez `suyunu`; `milli→mil`).

## 7. Sınırlılıklar

- **Bağlamsız belirsizlik:** `gelin` (gelin / gel-in), `yazın` (yazın / yaz-ın), `doğan`, `alan` için stemmer korpusta
  daha sık olan okumayı seçer; POS bilgisi verilirse (`Stemmer.analyze` adayları POS taşır) çözülebilir — pipeline'da
  tagger yok, bu yüzden raporlanan sayı POS'suz.
- **Kök sözlüğüne bağımlılık:** sözlükte olmayan köklerde (dev'de gold kökü sözlükte olmayan 415 token, çoğu özel ad)
  OOV yolu çalışır; `Ümraniye→ümran` gibi "görülmemiş uzun kök vs. görülmüş kısa kök" hatası kaçınılmaz.
- **UD gold'un kendi gürültüsü:** lemma=form hataları, tutarsız kopula lemmaları (`y`/`i`), UPOS'a göre değişen türetim
  kararları (`ilgili` ADJ→`ilgi` ama NOUN→`ilgili`). Üst sınır %100 değil.
- **Türetim ≠ UD lemma:** hocanın "köküne kadar" talebi ile UD'nin sözlükselleşmiş türetimleri koruması çelişir; biz
  frekans tabanlı uzlaşma (sık → koru, nadir → soy) ve train'den gelen tip eşlemesi kullanıyoruz.

## 8. Sonraki adımlar

- `suy→su` gibi birkaç düzensiz gövde istisnası (dev'de 7 token); kesme işaretsiz büyük harfli, sözlükte olmayan
  özel adlar için "tüm adaylar görülmemiş kökse dokunma" kuralı (dev'de 45 token).
- İsteğe bağlı POS girdisi (`stem(word, pos=...)`) ve toolkit pipeline'ında tokenizer → normalize → stopword → stem
  zinciriyle genel-domain metinlerde demo.
- Mod B ("saf kök") için küçük elle etiketli test seti; Final paper'da hata analizi örneklerinin elle doğrulanması.

## 9. LLM kullanım notu

Kod, kaynak dosyalar ve bu bölümün taslağı, tasarım kararları ve kabul kriterleri tarafımızca belirlenerek **Claude
Code (Claude Fable 5.1)** yardımıyla yazıldı; ek envanteri, FSA ve ses kuralları yukarıdaki kaynaklara göre elle gözden
geçirildi. Raporun nihai metni kendi kelimelerimizle yazılacak; bu kullanım raporun sonundaki acknowledgment'ta
belirtilecek.
