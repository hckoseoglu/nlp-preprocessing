# Tokenization — UD-BOUN dev

## Test case 1: all sentences (979), gold: UD-BOUN + TDK periods (Dr. / 3.) — main score

| tokenizer | precision | recall | F1 | sentence exact |
|---|---|---|---|---|
| whitespace | 80.57% | 66.96% | 73.14% | 6.54% (64/979) |
| regex baseline | 99.06% | 99.49% | 99.27% | 95.10% (931/979) |
| rule-based | 99.45% | 99.64% | 99.55% | 97.04% (950/979) |
| LR set 1 | 99.35% | 99.51% | 99.43% | 96.22% (942/979) |
| LR set 2 | 99.51% | 99.65% | 99.58% | 97.14% (951/979) |
| LR set 3 | 99.51% | 99.68% | 99.59% | 97.14% (951/979) |

## Test case 1: all sentences, gold: plain UD-BOUN — for transparency

| tokenizer | precision | recall | F1 | sentence exact |
|---|---|---|---|---|
| whitespace | 80.50% | 66.86% | 73.05% | 6.54% (64/979) |
| regex baseline | 99.17% | 99.55% | 99.36% | 95.81% (938/979) |
| rule-based | 99.39% | 99.53% | 99.46% | 96.32% (943/979) |
| LR set 1 | 99.39% | 99.49% | 99.44% | 96.32% (943/979) |
| LR set 2 | 99.53% | 99.61% | 99.57% | 97.04% (950/979) |
| LR set 3 | 99.53% | 99.63% | 99.58% | 97.04% (950/979) |

## Test case 2: hard cases (gold: tdk; only the tokens inside hard chunks; per kind: chunk exact match)

| tokenizer | precision | recall | F1 | chunk exact (357) | apostrophe (231) | number (10) | period (25) | punctuation (105) |
|---|---|---|---|---|---|---|---|---|
| whitespace | 59.38% | 38.27% | 46.54% | 59.38% | 87.45% | 30.00% | 28.00% | 0.95% |
| regex baseline | 83.67% | 90.61% | 87.00% | 87.68% | 95.24% | 60.00% | 24.00% | 80.95% |
| rule-based | 91.08% | 94.04% | 92.54% | 93.28% | 94.81% | 50.00% | 96.00% | 92.38% |
| LR set 1 | 87.89% | 91.70% | 89.75% | 90.76% | 94.81% | 30.00% | 76.00% | 91.43% |
| LR set 2 | 90.54% | 93.32% | 91.91% | 92.16% | 95.67% | 40.00% | 76.00% | 90.48% |
| LR set 3 | 91.07% | 93.86% | 92.44% | 92.72% | 95.67% | 50.00% | 84.00% | 92.38% |

## Test case 3: special entities (979 sentences, one synthetic entity each; gold: tdk)

| tokenizer | precision | recall | F1 | sentence exact | url kept (239) | email kept (241) | hashtag kept (255) | mention kept (244) |
|---|---|---|---|---|---|---|---|---|
| whitespace | 80.05% | 66.28% | 72.51% | 4.80% | 52.72% | 49.38% | 50.59% | 52.87% |
| regex baseline | 94.87% | 96.81% | 95.83% | 73.95% | 36.82% | 73.44% | 100.00% | 100.00% |
| rule-based | 99.50% | 99.68% | 99.59% | 97.04% | 100.00% | 100.00% | 100.00% | 100.00% |
| LR set 1 | 90.56% | 95.66% | 93.04% | 48.21% | 0.00% | 0.00% | 100.00% | 95.90% |
| LR set 2 | 98.84% | 99.40% | 99.12% | 93.36% | 86.61% | 97.51% | 100.00% | 100.00% |
| LR set 3 | 99.56% | 99.71% | 99.63% | 97.14% | 100.00% | 100.00% | 100.00% | 100.00% |

## MWE layer (rule-based tokenizer + resources/mwe_tr.txt + repeat rule; gold: UD MWE relations)

| MWE kind | gold | predicted | correct | precision | recall | F1 |
|---|---|---|---|---|---|---|
| fixed | 12 | 11 | 9 | 81.82% | 75.00% | 78.26% |
| redup | 31 | 20 | 17 | 85.00% | 54.84% | 66.67% |
| lvc | 130 | 111 | 91 | 81.98% | 70.00% | 75.52% |
| all | 173 | 142 | 118 | 83.10% | 68.21% | 74.92% |
| all, lexicon only (no repeat rule) | 173 | 137 | 113 | 82.48% | 65.32% | 72.90% |
