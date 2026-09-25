"""Deterministic cross-checks for calculation evidence.

This module deliberately reports only arithmetic/textual contradictions that
can be established from extracted values. Engineering adequacy remains a
review item when units, section/model identity, or source context are missing.
"""
from __future__ import annotations
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class NumericCheck:
    code: str
    status: str
    message: str
    evidence: tuple[str, ...] = ()

_NUM = r"[-+]?\d+(?:[,.]\d+)?"

def _f(s: str) -> float:
    return float(s.replace(",", "."))

def check_comparison(actual: str, required: str, *, label: str = "") -> NumericCheck:
    a, r = _f(actual), _f(required)
    if a < r:
        return NumericCheck(
            "REQUIRED_EXCEEDS_ACTUAL", "REVIEW",
            f"{label} фактическое значение меньше требуемого; инженерную достаточность необходимо проверить.",
            (actual, required),
        )
    return NumericCheck(
        "ACTUAL_NOT_BELOW_REQUIRED", "PASS",
        f"{label} фактическое значение не меньше требуемого.",
        (actual, required),
    )

def check_limit(value: str, limit: str, *, label: str = "") -> NumericCheck:
    v, l = _f(value), _f(limit)
    if v > l:
        return NumericCheck(
            "VALUE_EXCEEDS_LIMIT", "FAIL",
            f"{label} значение превышает указанное предельное значение.",
            (value, limit),
        )
    return NumericCheck(
        "VALUE_WITHIN_LIMIT", "PASS",
        f"{label} значение не превышает указанное предельное значение.",
        (value, limit),
    )

def extract_simple_limit_pairs(text: str) -> tuple[NumericCheck, ...]:
    out = []
    pattern = re.compile(
        rf"(?i)(?:прогиб|перемещени\w*)[^\n]{{0,100}}?({_NUM})\s*мм[^\n]{{0,100}}?"
        rf"(?:предельн\w*|допустим\w*)[^\n]{{0,100}}?({_NUM})\s*мм"
    )
    for m in pattern.finditer(text):
        out.append(check_limit(m.group(1), m.group(2), label="Прогиб/перемещение"))
    return tuple(out)
