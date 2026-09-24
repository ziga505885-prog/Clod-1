"""Domain-level analyzer for engineering inspection report consistency.

This layer maps defects across the main report text, the consolidated defect
table, section 4 characteristics, and drawing/graphics labels. It is
deliberately conservative: it reports mismatches and duplicates but never
invents defect IDs, severity, causes, or engineering conclusions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable

from .analyzer import AnalysisResult
from .model import Defect

_ID_RE = re.compile(r"\b(?:ДКР|Деф|Дефект|Тр|Т|К|Р)?\s*[-№]?\s*(\d+)\b", re.I)
_SECTION4_RE = re.compile(r"^\s*4(?:[.\s]|$).*характеристик", re.I)
_SUMMARY_HINTS = ("сводная ведомость", "ведомость дефектов", "сводная таблица", "дефектов")
_CHARACTERISTIC_HINTS = ("характеристик дефектов", "характеристика дефектов")
_DRAWING_HINTS = ("условные обозначения", "графика", "схема", "чертеж")

@dataclass(frozen=True)
class DomainFinding:
    code: str
    message: str
    source: str
    evidence: tuple[str, ...] = ()

@dataclass(frozen=True)
class DomainDefect:
    id: str | None
    description: str
    source: str
    row_index: int | None = None

@dataclass(frozen=True)
class DomainAnalysisResult:
    summary: tuple[DomainDefect, ...] = ()
    characteristics: tuple[DomainDefect, ...] = ()
    report: tuple[DomainDefect, ...] = ()
    drawings: tuple[DomainDefect, ...] = ()
    findings: tuple[DomainFinding, ...] = ()

def _norm(value: str) -> str:
    value = (value or "").lower().replace("ё", "е")
    return " ".join(re.findall(r"[a-zа-я0-9]+", value))

def _extract_id(value: str) -> str | None:
    match = _ID_RE.search(value or "")
    if not match:
        return None
    prefix = (value[:match.start()] or "").strip().lower()
    if prefix.startswith("дкр"):
        return f"ДКР-{match.group(1)}"
    if re.search(r"\bтр\b", prefix, re.I):
        return f"Тр-{match.group(1)}"
    return match.group(1)

def _looks_like_summary(headers: list[str], rows: list[list[str]]) -> bool:
    blob = _norm(" ".join(headers) + " " + " ".join(" ".join(r) for r in rows[:3]))
    return any(_norm(x) in blob for x in _SUMMARY_HINTS)

def _looks_like_characteristics(headers: list[str], rows: list[list[str]]) -> bool:
    blob = _norm(" ".join(headers) + " " + " ".join(" ".join(r) for r in rows[:3]))
    return any(_norm(x) in blob for x in _CHARACTERISTIC_HINTS) or (
        "характеристика" in blob and "дефект" in blob
    )

def _looks_like_drawing(headers: list[str], rows: list[list[str]]) -> bool:
    blob = _norm(" ".join(headers) + " " + " ".join(" ".join(r) for r in rows[:3]))
    return any(_norm(x) in blob for x in _DRAWING_HINTS)

def _row_defect(row: list[str], headers: list[str], source: str, row_index: int) -> DomainDefect | None:
    if not row:
        return None
    text = " | ".join(x for x in row if x)
    if not text:
        return None
    id_value = None
    id_cols = [i for i, h in enumerate(headers) if any(k in _norm(h) for k in ("номер", "обознач", "дефект"))]
    for i in id_cols:
        if i < len(row):
            id_value = _extract_id(row[i])
            if id_value:
                break
    if id_value is None:
        id_value = _extract_id(text)
    # A row without an explicit number is valid: general defects must not
    # receive a synthetic identifier.
    return DomainDefect(id_value, text, source, row_index)

def _find_section4_paragraphs(paragraphs: list[str]) -> set[int]:
    indexes = set()
    active = False
    for i, p in enumerate(paragraphs):
        if _SECTION4_RE.search(p):
            active = True
            indexes.add(i)
            continue
        if active and re.match(r"^\s*5(?:[.\s]|$)", p, re.I):
            active = False
        elif active:
            indexes.add(i)
    return indexes

def analyze_domain(analysis: AnalysisResult) -> DomainAnalysisResult:
    tables = analysis.tables
    summary: list[DomainDefect] = []
    characteristics: list[DomainDefect] = []
    drawings: list[DomainDefect] = []

    for ti, table in enumerate(tables):
        if not table:
            continue
        headers = table[0]
        rows = table[1:]
        if _looks_like_summary(headers, rows):
            for ri, row in enumerate(rows, 1):
                item = _row_defect(row, headers, "summary", ri)
                if item:
                    summary.append(item)
        elif _looks_like_characteristics(headers, rows):
            for ri, row in enumerate(rows, 1):
                item = _row_defect(row, headers, "characteristics", ri)
                if item:
                    characteristics.append(item)
        elif _looks_like_drawing(headers, rows):
            for ri, row in enumerate(rows, 1):
                item = _row_defect(row, headers, "drawing", ri)
                if item:
                    drawings.append(item)

    report: list[DomainDefect] = []
    section4 = _find_section4_paragraphs(analysis.paragraphs)
    for i, paragraph in enumerate(analysis.candidate_defect_paragraphs):
        # Candidate paragraphs remain unnumbered unless an explicit ID exists.
        report.append(DomainDefect(_extract_id(paragraph), paragraph, "report", i))

    findings: list[DomainFinding] = []
    _compare_sources(summary, "summary", characteristics, "characteristics", findings)
    _compare_sources(report, "report", summary, "summary", findings)
    _compare_sources(report, "report", characteristics, "characteristics", findings)
    _duplicates(summary, "summary", findings)
    _duplicates(characteristics, "characteristics", findings)
    _duplicates(drawings, "drawing", findings)

    if not section4 and characteristics:
        findings.append(DomainFinding(
            "SECTION4_NOT_FOUND",
            "A characteristics table was found, but a textual section 4 heading was not detected.",
            "characteristics",
        ))

    return DomainAnalysisResult(tuple(summary), tuple(characteristics), tuple(report), tuple(drawings), tuple(findings))

def _same(a: DomainDefect, b: DomainDefect) -> bool:
    if a.id and b.id:
        return a.id.casefold() == b.id.casefold()
    na, nb = _norm(a.description), _norm(b.description)
    if not na or not nb:
        return False
    # Conservative token containment avoids treating short generic labels as
    # equivalent to unrelated engineering defects.
    sa, sb = set(na.split()), set(nb.split())
    return len(sa & sb) >= 3 and (sa <= sb or sb <= sa or len(sa & sb) / max(len(sa), len(sb)) >= 0.6)

def _compare_sources(left: list[DomainDefect], left_name: str, right: list[DomainDefect], right_name: str, findings: list[DomainFinding]) -> None:
    for item in left:
        if not any(_same(item, other) for other in right):
            findings.append(DomainFinding(
                f"DEFECT_MISSING_FROM_{right_name.upper()}",
                f"Defect from {left_name} has no conservative match in {right_name}.",
                left_name,
                (item.description,),
            ))

def _duplicates(items: list[DomainDefect], source: str, findings: list[DomainFinding]) -> None:
    seen: dict[str, DomainDefect] = {}
    for item in items:
        key = item.id.casefold() if item.id else _norm(item.description)
        if not key:
            continue
        if key in seen:
            findings.append(DomainFinding(
                "DUPLICATE_DEFECT",
                f"Duplicate defect identity detected in {source}.",
                source,
                (seen[key].description, item.description),
            ))
        else:
            seen[key] = item
