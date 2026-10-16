"""Değerlendirme yardımcıları — her task için metrik + test-case tabloları.

Hedef: her 5 görevde %90–95 başarı; farklı test case'lerde raporla (bkz. CLAUDE.md).
Ortak metrikler burada toplanır ki üç task tutarlı raporlasın.
"""
from __future__ import annotations


def accuracy(pred: list[str], gold: list[str]) -> float:
    """Token-level accuracy (stemming, normalization için)."""
    if not gold:
        return 0.0
    correct = sum(p == g for p, g in zip(pred, gold))
    return correct / len(gold)


def prf(pred_set: set[str], gold_set: set[str]) -> tuple[float, float, float]:
    """Küme tabanlı precision/recall/F1 (stopword için)."""
    if not pred_set:
        return 0.0, 0.0, 0.0
    tp = len(pred_set & gold_set)
    precision = tp / len(pred_set) if pred_set else 0.0
    recall = tp / len(gold_set) if gold_set else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def report_table(rows: list[tuple[str, float]], title: str = "") -> str:
    """Basit test-case -> skor tablosu (rapora kopyalanabilir)."""
    lines = [title] if title else []
    lines.append(f"{'test case':<30} | skor")
    lines.append("-" * 42)
    for name, score in rows:
        lines.append(f"{name:<30} | {score:.4f}")
    return "\n".join(lines)
