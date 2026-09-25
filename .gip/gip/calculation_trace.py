"""Contextual trace matching for trusted engineering calculations.

A numeric value is comparable only after its calculation context is identified.
"""
from __future__ import annotations
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class CalculationResultEvidence:
    value: float
    unit: str
    metric: str
    section: str | None
    block: str | None
    model: str | None
    limit: float | None
    limit_unit: str | None
    source_text: str

@dataclass(frozen=True)
class TraceMatch:
    comparable: bool
    reason: str
    evidence: CalculationResultEvidence
    reference: CalculationResultEvidence | None = None

_NUM = r"(-?\d+(?:[.,]\d+)?)"
_PAIR_RE = re.compile(
    rf"(?i)(?P<metric>прогиб|крен|армирован[ие]|площад[ьи] арматуры)"
    rf".{{0,100}}?{_NUM}\s*(?P<unit>мм|см2|см²|мм2|мм²|т|кН)?"
)
_LIMIT_RE = re.compile(rf"(?i)предельн(?:ый|ого)\s+(?:прогиб|значени[ея]).{{0,100}}?{_NUM}\s*(мм|см2|см²|мм2|мм²)?")

def _f(value: str) -> float:
    return float(value.replace(",", "."))

def extract_result_evidence(text: str, *, section: str | None = None, block: str | None = None, model: str | None = None) -> list[CalculationResultEvidence]:
    out = []
    limits = list(_LIMIT_RE.finditer(text))
    for m in _PAIR_RE.finditer(text):
        value = _f(m.group(2))
        unit = m.group("unit") or ""
        limit = _f(limits[0].group(1)) if limits else None
        limit_unit = limits[0].group(2) if limits else None
        out.append(CalculationResultEvidence(value, unit, m.group("metric"), section, block, model, limit, limit_unit, m.group(0)))
    return out

def match_results(actual: CalculationResultEvidence, reference: CalculationResultEvidence) -> TraceMatch:
    if actual.metric != reference.metric:
        return TraceMatch(False, "different_metric", actual, reference)
    if actual.unit != reference.unit:
        return TraceMatch(False, "different_unit", actual, reference)
    if actual.section != reference.section or actual.block != reference.block:
        return TraceMatch(False, "different_section_or_block", actual, reference)
    if actual.model != reference.model:
        return TraceMatch(False, "different_model", actual, reference)
    return TraceMatch(True, "same_calculation_context", actual, reference)
