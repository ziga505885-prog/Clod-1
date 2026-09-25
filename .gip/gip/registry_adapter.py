"""Bridge deterministic DOCX analysis into the unified defect registry."""
from __future__ import annotations
import re
from .analyzer import AnalysisResult
from .defect_registry import DefectRegistry
from .model import Defect

_ID_RE = re.compile(r"\b[ДдПпКкСсЛлГгТт]\s*\d+\b")


def build_registry_from_analysis(analysis: AnalysisResult) -> DefectRegistry:
    registry = DefectRegistry()
    registry.add_source("report", analysis.report.defects)
    for table in analysis.tables:
        source, defects = _classify_table(table)
        if source and defects:
            registry.add_source(source, defects)
    return registry


def _classify_table(table: list[list[str]]) -> tuple[str | None, list[Defect]]:
    if not table:
        return None, []
    blob = " ".join(" ".join(row) for row in table[:4]).lower()
    if "условный номер" in blob and "описание" in blob:
        return "characteristics", _key_value_defect(table)
    if "сводная ведомость" in blob or "ведомость дефектов" in blob:
        return "summary", _rows(table[1:])
    return None, []


def _key_value_defect(table: list[list[str]]) -> list[Defect]:
    values = {}
    for row in table:
        if len(row) >= 2:
            values[row[0].strip().lower()] = " | ".join(x.strip() for x in row[1:] if x.strip())
    raw_id = values.get("условный номер", "")
    match = _ID_RE.search(raw_id)
    defect_id = match.group(0).replace(" ", "").upper() if match else None
    description = values.get("описание", "").strip()
    if not description:
        return []
    return [Defect(id=defect_id, structure="", description=description)]


def _rows(rows: list[list[str]]) -> list[Defect]:
    return [
        Defect(id=None, structure="", description=" | ".join(x for x in row if x).strip())
        for row in rows if any(x.strip() for x in row)
    ]
