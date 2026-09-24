"""Deterministic defect consistency graph for GIP.

The graph links the same engineering defect across report text, summary,
characteristics, drawings and photos without letting the matcher invent defects.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import re
from typing import Iterable
from .model import Defect, InspectionReport

_WORD_RE = re.compile(r"[a-zа-яё0-9]+", re.IGNORECASE)

def normalize(text: str) -> str:
    return " ".join(_WORD_RE.findall((text or "").lower()))

def defect_key(defect: Defect) -> str:
    base = " ".join(
        x for x in (defect.structure, defect.location or "", defect.description)
        if x
    )
    return normalize(base)

def similarity(a: Defect, b: Defect) -> float:
    aa, bb = set(normalize(a.description).split()), set(normalize(b.description).split())
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)

@dataclass
class DefectNode:
    key: str
    defect: Defect
    sources: set[str] = field(default_factory=set)

@dataclass
class DefectFinding:
    code: str
    defect_key: str
    message: str
    source: str
    evidence: list[str] = field(default_factory=list)

@dataclass
class DefectGraph:
    nodes: dict[str, DefectNode] = field(default_factory=dict)

    def add(self, source: str, defect: Defect) -> str:
        key = defect_key(defect)
        node = self.nodes.get(key)
        if node is None:
            node = DefectNode(key=key, defect=defect)
            self.nodes[key] = node
        node.sources.add(source)
        return key

    def missing(self, required_source: str, present_source: str) -> list[DefectNode]:
        return [
            n for n in self.nodes.values()
            if required_source in n.sources and present_source not in n.sources
        ]

def build_defect_graph(report: InspectionReport) -> DefectGraph:
    graph = DefectGraph()
    for d in report.defects:
        graph.add("report", d)
    for d in report.defect_summary:
        graph.add("summary", d)
    for d in report.defect_characteristics:
        graph.add("characteristics", d)

    for d in report.drawing_defects:
        graph.add("drawing", d)
    for d in report.photo_defects:
        graph.add("photo", d)

    # A report defect may also carry explicit links to drawing/photo evidence.
    for d in report.defects:
        if d.source_drawings:
            graph.add("drawing", d)
        if d.source_photos:
            graph.add("photo", d)
    return graph

def validate_defect_consistency(report: InspectionReport) -> list[DefectFinding]:
    graph = build_defect_graph(report)
    findings: list[DefectFinding] = []

    for source, target, code in (
        ("report", "summary", "DEFECT_MISSING_FROM_SUMMARY"),
        ("report", "characteristics", "DEFECT_MISSING_FROM_CHARACTERISTICS"),
        ("summary", "report", "DEFECT_MISSING_FROM_REPORT"),
        ("characteristics", "report", "DEFECT_MISSING_FROM_REPORT"),
    ):
        for node in graph.missing(source, target):
            findings.append(DefectFinding(
                code=code,
                defect_key=node.key,
                message=f"Defect present in {source} is missing from {target}",
                source=source,
                evidence=[node.defect.description],
            ))

    return findings
