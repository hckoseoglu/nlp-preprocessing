# Kaynaklar ve lisanslar (`lexicon/`)

Tüm kod bize aittir (Python 3, yalnız standart kütüphane). Aşağıdaki dış kaynaklar **veri/referans** olarak
kullanıldı; hiçbirinden kod kopyalanmadı.

## Veri

| Dosya | Kaynak | Lisans | Nasıl üretildi |
|---|---|---|---|
| `roots.tsv` | **TRmorph** kök sözlüğü (Çöltekin 2010) — <https://github.com/coltekin/TRmorph>, commit `fbceb11` (2018-12-18), `lexicon/{noun, verb, verb_la, adjective, adverb, pronoun, postposition, conjunction, determiner, interjection, qwords, clitics}` **+** UD Turkish-BOUN *train* gold kökleri (Türk vd. 2022) | TRmorph: MIT · BOUN: CC BY-SA 4.0 | `src/scripts/stem_build_roots.py` — TRmorph notasyonu (`^k` yumuşama, `@DEL@` ünlü düşmesi, `@DUP@` ikizleşme, `^pA` ters uyum, `ˈ` vurgu, `a:b` çift yazım, `%` çok sözcüklü) bayraklara çevrildi; UD kökleri frekansla eklendi; UD lemma gürültüsü (sık bir kökün saf çekimi olarak çözümlenen ≤4 frekanslı "kökler") budandı (`results/roots_pruned.tsv`). |
| `suffixes.tsv` | Kendi derlememiz. Ek envanteri: Oflazer (1994) notasyonu; Göksel & Kerslake (2005) böl. 7–8; Sak, Güngör & Saraçlar (2011) ek listesi; Eryiğit & Adalı (2004) Tablo 3–8 | — | Elle yazıldı (111 ek şablonu → 541 allomorf, `stemmer/suffixes.py` üretir). |
| `morphotactics.tsv` | Çöltekin (2010) Fig. 1–2 ve Oflazer (1994) Fig. B.1/B.2 (ders slaytı Slide03 s.47–48) sade hali | — | Elle yazıldı (13 durum, 42 geçiş; 10 ε). |
| `derived.tsv` | UD Turkish-BOUN `MISC:DerivedFrom` (train+dev+test, **tip seviyesi** çoğunluk oyu) | CC BY-SA 4.0 | `src/scripts/stem_build_gold.py` — gold tanımının parçası; stemmer yalnız `train` içeren satırları kullanır. |
| `copula_fragments.tsv` | Kural-tabanlı üretim (ek şablonları) + UD train ile çakışma giderme | — | `src/scripts/stem_build_fragments.py` — UD'nin ayrı sözcük olarak böldüğü ek-fiil parçacıkları (du, ydı, ken, dır, ise…) ve UD lemma sözleşmesi (`y`/`i`). |
| `exceptions.tsv` | Göksel & Kerslake (2005) böl. 18 (zamir çekimi); UD lemma sözleşmeleri (mı/mu/mü→mi, sana→san) | — | Elle yazıldı. |

Ham TRmorph dosyaları depoya alınmadı; `src/scripts/stem_build_roots.py --trmorph <klon>` ile yeniden üretilebilir.

## Yöntem referansları

- Eryiğit, G., & Adalı, E. (2004). *An affix stripping morphological analyzer for Turkish.* IASTED Int. Conf. on
  Artificial Intelligence and Applications (AIA 2004), Innsbruck. — Ters yönlü ek-soyma FSA şeması; sözlüksüz "en kısa
  kök" kuralı yerine biz kök sözlüğü + frekans-ağırlıklı seçim kullandık.
- Oflazer, K. (1994). *Two-level description of Turkish morphology.* Literary and Linguistic Computing, 9(2), 137–148. —
  Arşifonem notasyonu (A, I, D, C, K), ses kuralları, morfotaktik.
- Çöltekin, Ç. (2010). *A freely available morphological analyzer for Turkish.* LREC 2010, Valletta. — TRmorph; kök
  sözlüğü ve morfotaktik şekiller.
- Sak, H., Güngör, T., & Saraçlar, M. (2011). *Resources for Turkish morphological processing.* Language Resources and
  Evaluation, 45(2), 249–261. — Ek envanteri referansı.
- Türk, U., Atmaca, F., Özateş, Ş. B., Berk, G., Bedir, S. T., Köksal, A., Öztürk Başaran, B., Güngör, T., & Özgür, A.
  (2022). *Resources for Turkish dependency parsing: Introducing the BOUN Treebank and the BoAT annotation tool.*
  Language Resources and Evaluation, 56, 259–307. — UD Turkish-BOUN.
- Göksel, A., & Kerslake, C. (2005). *Turkish: A Comprehensive Grammar.* Routledge. — Ses kuralları (böl. 2–3), ekler
  (böl. 7–8), zamirler (böl. 18).
- Singh, J., & Gupta, V. (2017). *A systematic review of text stemming techniques.* Artificial Intelligence Review,
  48(2), 157–217. — Stemming yöntemleri taksonomisi (kural-tabanlı / sözlük-tabanlı).
- Çilden, E. (2006). *Stemming Turkish words using Snowball.* <https://snowballstem.org/algorithms/turkish/stemmer.html>
  — Baseline (yalnız isim çekimi). Python paketleri: `snowballstemmer` (BSD-3), `TurkishStemmer` (PyPI, Snowball portu).

## Baseline araçları (yalnız değerlendirme; stemmer'da kullanılmaz)

`pip install snowballstemmer TurkishStemmer` → `src/scripts/stem_evaluate.py` varsa raporlar, yoksa atlar.

## LLM kullanımı

Kod ve kaynak dosyalar, tasarım kararları Hikmet Can Köseoğlu tarafından verilerek **Claude Code (Claude Fable 5.1)**
yardımıyla yazıldı; ek envanteri, FSA ve ses kuralları yukarıdaki kaynaklara göre elle gözden geçirildi. Rapor/paper
metni kendi kelimelerimizle yazılır; bu kullanım raporun sonunda acknowledgment olarak belirtilir.
