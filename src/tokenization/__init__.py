"""Tokenization package — rule-based and Logistic Regression tokenizers (Ecem).

Each tokenizer takes a single sentence and returns a list of tokens (in document mode the sentences
come from Hikmet's splitter, see CLAUDE.md "Sıra kararı"). The model decides at every candidate point
inside a whitespace-free chunk whether to split there; candidate points and their UD labels are in
corpus.py.
"""
from .corpus import Candidate, chunk_candidates, gold_chunks, gold_tokens, sentence_candidates  # noqa: F401
from .rules import RuleTokenizer  # noqa: F401
