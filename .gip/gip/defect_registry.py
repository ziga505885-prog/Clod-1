"""Unified defect registry.

Creates links only from explicit IDs or conservative textual matches.
It never creates a new defect merely because a source contains unmatched text.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from .model import Defect, InspectionReport

_WORD_RE = re.compile(r"[a-zа-яё0-9]+", re.I)
_ID_RE = re.compile(r"\b(?:ДКР|Деф|Дефект|Тр)\s*[-№]?\s*\d+\b", re.I)


def normalize(text: str) -> str:
    return " ".join(_WORD_RE.findall((text or "").lower().replace("ё", "е")))


def explicit_id(defect: Defect) -> str | None:
    if defect.id:
        return normalize(defect.id)
    match = _ID_RE.search(defect.description or "")
    return normalize(match.group(0)) if match else None


def _tokens(defect: Defect) -> set[str]:
    return set(normalize(defect.description).split())


def match_score(a: Defect, b: Defect) -> float:
    ia, ib = explicit_id(a), explicit_id(b)
    if ia and ib:
        return 1.0 if ia == ib else 0.0
    if ia or ib:
        return 0.0
    aa, bb = _tokens(a), _tokens(b)
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


@dataclass
class RegistryEntry:
    canonical: Defect
    sources: set[str] = field(default_factory=set)
    linked: dict[str, list[Defect]] = field(default_factory=dict)


@dataclass
class RegistryFinding:
    code: str
    source: str
    message: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class DefectRegistry:
    entries: list[RegistryEntry] = field(default_factory=list)

    def add_source(self, source: str, defects: list[Defect]) -> None:
        for defect in defects:
            best: RegistryEntry | None = None
            best_score = 0.0
            for entry in self.entries:
                score = match_score(entry.canonical, defect)
                if score > best_score:
                    best, best_score = entry, score
            if best is not None and best_score >= 0.60:
                best.sources.add(source)
                best.linked.setdefault(source, []).append(defect)
            else:
                self.entries.append(
                    RegistryEntry(
                        canonical=defect,
                        sources={source},
                        linked={source: [defect]},
                    )
                )

    def missing(self, source: str, target: str) -> list[RegistryEntry]:
        return [e for e in self.entries if source in e.sources and target not in e.sources]


def build_registry(report: InspectionReport) -> DefectRegistry:
    registry = DefectRegistry()
    registry.add_source("report", report.defects)
    registry.add_source("summary", report.defect_summary)
    registry.add_source("characteristics", report.defect_characteristics)
    registry.add_source("drawing", report.drawing_defects)
    registry.add_source("photo", report.photo_defects)
    return registry


def validate_registry(report: InspectionReport) -> list[RegistryFinding]:
    registry = build_registry(report)
    findings: list[RegistryFinding] = []
    required = (
        ("report", "summary", "DEFECT_MISSING_FROM_SUMMARY"),
        ("report", "characteristics", "DEFECT_MISSING_FROM_CHARACTERISTICS"),
        ("summary", "report", "DEFECT_MISSING_FROM_REPORT"),
        ("characteristics", "report", "DEFECT_MISSING_FROM_REPORT"),
    )
    for source, target, code in required:
        for entry in registry.missing(source, target):
            findings.append(RegistryFinding(
                code=code,
                source=source,
                message=f"Defect present in {source} has no conservative match in {target}",
                evidence=[entry.canonical.description],
            ))
    return findings
