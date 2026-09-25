"""Bridge deterministic DOCX analysis into the unified defect registry."""
from __future__ import annotations
from .analyzer import AnalysisResult
from .defect_registry import DefectRegistry
from .model import Defect


def build_registry_from_analysis(analysis: AnalysisResult) -> DefectRegistry:
    registry = DefectRegistry()
    registry.add_source("report", analysis.report.defects)
    # Table classification is intentionally conservative and header-driven.
    # No table row is promoted to a defect until the table is recognized.
    for table in analysis.tables:
        if not table:
            continue
        header_blob = " ".join(table[0]).lower()
        rows = table[1:]
        if "сводная ведомость" in header_blob or "ведомость дефектов" in header_blob:
            registry.add_source("summary", _rows(rows))
        elif "характеристик дефектов" in header_blob or ("характеристика" in header_blob and "дефект" in header_blob):
            registry.add_source("characteristics", _rows(rows))
    return registry


def _rows(rows: list[list[str]]) -> list[Defect]:
    return [
        Defect(id=None, structure="", description=" | ".join(x for x in row if x).strip())
        for row in rows
        if any(x.strip() for x in row)
    ]
