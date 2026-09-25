from dataclasses import dataclass, field
from .model import InspectionReport
from .rules import ALLOWED_CATEGORIES
from .defect_graph import validate_defect_consistency

@dataclass
class Finding:
    code: str
    message: str
    evidence: list[str] = field(default_factory=list)

@dataclass
class ValidationResult:
    passed: bool
    findings: list[Finding] = field(default_factory=list)

def validate_report(report: InspectionReport) -> ValidationResult:
    findings=[]
    for d in report.defects:
        if d.category and d.category.value not in ALLOWED_CATEGORIES:
            findings.append(Finding("INVALID_CATEGORY",f"Invalid category for defect {d.id}",[d.description]))
    # Cross-source completeness is meaningful only when at least one target
    # registry is actually present. An isolated report model is not incomplete
    # merely because summary/characteristics were not loaded.
    if report.defect_summary or report.defect_characteristics or report.drawing_defects or report.photo_defects:
        for finding in validate_defect_consistency(report):
            findings.append(Finding(finding.code,finding.message,finding.evidence))
    return ValidationResult(not findings,findings)
