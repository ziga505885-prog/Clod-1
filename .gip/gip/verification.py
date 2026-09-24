from dataclasses import dataclass
from .model import InspectionReport
from .validation import validate_report, ValidationResult

@dataclass
class VerificationLoop:
    max_attempts: int = 3

    def run(self, report: InspectionReport) -> ValidationResult:
        last = validate_report(report)
        for _ in range(self.max_attempts - 1):
            if last.passed:
                return last
            last = validate_report(report)
        return last
