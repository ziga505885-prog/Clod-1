from __future__ import annotations
from dataclasses import dataclass
from .model import Defect, InspectionReport
from .defect_registry import build_registry, match_score, explicit_id

@dataclass(frozen=True)
class ReconciliationFinding:
    code: str
    source: str
    target: str
    message: str
    evidence: list[str]

def reconcile_defects(report: InspectionReport) -> list[ReconciliationFinding]:
    registry = build_registry(report)
    findings: list[ReconciliationFinding] = []

    for source, target, missing_code in (
        ("report", "summary", "DEFECT_MISSING_FROM_SUMMARY"),
        ("report", "characteristics", "DEFECT_MISSING_FROM_CHARACTERISTICS"),
        ("summary", "report", "DEFECT_MISSING_FROM_REPORT"),
        ("characteristics", "report", "DEFECT_MISSING_FROM_REPORT"),
    ):
        for entry in registry.missing(source, target):
            findings.append(ReconciliationFinding(
                missing_code, source, target,
                f"Дефект из источника «{source}» не найден в «{target}» по консервативному правилу сопоставления.",
                [entry.canonical.description],
            ))

    # Explicit IDs are checked separately so duplicate IDs remain visible.
    for source, defects in (
        ("report", report.defects),
        ("summary", report.defect_summary),
        ("characteristics", report.defect_characteristics),
        ("drawing", report.drawing_defects),
        ("photo", report.photo_defects),
    ):
        seen: dict[str, int] = {}
        for defect in defects:
            did = explicit_id(defect)
            if did:
                seen[did] = seen.get(did, 0) + 1
        for did, count in seen.items():
            if count > 1:
                findings.append(ReconciliationFinding(
                    "DUPLICATE_DEFECT_ID", source, source,
                    f"Идентификатор {did} встречается {count} раз(а) в одном источнике.",
                    [did],
                ))

    return findings
