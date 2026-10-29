# Tokenization — UD-BOUN test

## Test case 1: all sentences (979), gold: UD-BOUN + TDK periods (Dr. / 3.) — main score

| tokenizer | precision | recall | F1 | sentence exact |
|---|---|---|---|---|
| whitespace | 80.72% | 67.12% | 73.29% | 4.60% (45/979) |
| regex baseline | 99.18% | 99.49% | 99.34% | 95.20% (932/979) |
| rule-based | 99.48% | 99.67% | 99.58% | 96.94% (949/979) |
| LR set 1 | 99.59% | 99.58% | 99.59% | 97.04% (950/979) |
| LR set 2 | 99.49% | 99.58% | 99.54% | 96.53% (945/979) |
| LR set 3 | 99.53% | 99.66% | 99.60% | 97.04% (950/979) |

## Test case 1: all sentences, gold: plain UD-BOUN — for transparency

| tokenizer | precision | recall | F1 | sentence exact |
|---|---|---|---|---|
| whitespace | 80.69% | 67.07% | 73.26% | 4.60% (45/979) |
| regex baseline | 99.23% | 99.52% | 99.37% | 95.51% (935/979) |
| rule-based | 99.46% | 99.62% | 99.54% | 96.63% (946/979) |
| LR set 1 | 99.57% | 99.53% | 99.55% | 96.73% (947/979) |
| LR set 2 | 99.47% | 99.53% | 99.50% | 96.22% (942/979) |
| LR set 3 | 99.51% | 99.61% | 99.56% | 96.73% (947/979) |

## Test case 2: hard cases (gold: tdk; only the tokens inside hard chunks; per kind: chunk exact match)

| tokenizer | precision | recall | F1 | chunk exact (372) | apostrophe (257) | number (10) | period (18) | punctuation (97) |
|---|---|---|---|---|---|---|---|---|
| whitespace | 63.98% | 43.35% | 51.68% | 63.98% | 88.72% | 30.00% | 33.33% | 1.03% |
| regex baseline | 86.59% | 90.53% | 88.51% | 88.98% | 97.28% | 30.00% | 27.78% | 76.29% |
| rule-based | 92.83% | 94.35% | 93.59% | 94.09% | 97.28% | 30.00% | 100.00% | 89.69% |
| LR set 1 | 94.58% | 95.45% | 95.01% | 95.70% | 97.28% | 40.00% | 100.00% | 94.85% |
| LR set 2 | 91.38% | 92.71% | 92.04% | 92.47% | 97.67% | 20.00% | 77.78% | 84.54% |
| LR set 3 | 92.49% | 94.17% | 93.32% | 93.82% | 97.67% | 30.00% | 100.00% | 87.63% |

## Test case 3: special entities (979 sentences, one synthetic entity each; gold: tdk)

| tokenizer | precision | recall | F1 | sentence exact | url kept (221) | email kept (248) | hashtag kept (273) | mention kept (237) |
|---|---|---|---|---|---|---|---|---|
| whitespace | 80.53% | 66.90% | 73.08% | 3.37% | 50.68% | 52.02% | 56.41% | 52.74% |
| regex baseline | 95.87% | 97.02% | 96.44% | 76.20% | 38.91% | 77.42% | 100.00% | 100.00% |
| rule-based | 99.53% | 99.70% | 99.61% | 96.94% | 100.00% | 100.00% | 100.00% | 100.00% |
| LR set 1 | 90.72% | 95.80% | 93.19% | 49.54% | 0.00% | 0.00% | 100.00% | 97.05% |
| LR set 2 | 98.44% | 99.19% | 98.82% | 90.70% | 77.38% | 97.18% | 100.00% | 100.00% |
| LR set 3 | 99.58% | 99.69% | 99.63% | 97.04% | 100.00% | 100.00% | 100.00% | 100.00% |

## MWE layer (rule-based tokenizer + resources/mwe_tr.txt + repeat rule; gold: UD MWE relations)

| MWE kind | gold | predicted | correct | precision | recall | F1 |
|---|---|---|---|---|---|---|
| fixed | 16 | 17 | 15 | 88.24% | 93.75% | 90.91% |
| redup | 46 | 33 | 29 | 87.88% | 63.04% | 73.42% |
| lvc | 114 | 112 | 81 | 72.32% | 71.05% | 71.68% |
| all | 176 | 162 | 125 | 77.16% | 71.02% | 73.96% |
| all, lexicon only (no repeat rule) | 176 | 151 | 115 | 76.16% | 65.34% | 70.34% |
