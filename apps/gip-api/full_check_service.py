"""Service for deterministic DOCX metadata patching and post-patch recheck."""
from __future__ import annotations
from pathlib import Path
import sys

CORE = Path(__file__).resolve().parents[2] / ".gip"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from gip.analyzer import DocxReportAnalyzer
from gip.patch_planner import PatchPlanBuilder
from gip.streaming_patch_engine import StreamingDocxPatchEngine
from gip.streaming_verify import StreamingDocxVerifier
from gip.full_inspection import inspect_document

TARGETED_RECHECK_CODES = {
    "ADDRESS_INCONSISTENT", "ADDRESS_MISMATCH", "DATE_MISMATCH", "CONTRACT_MISMATCH"
}

def _finding_dict(f):
    return {"code": f.code, "message": f.message, "source": f.source,
            "evidence": list(f.evidence), "patch_kind": f.patch_kind}

def patch_and_verify_report(path: Path, expected_contract=None, expected_address=None, expected_date=None):
    precheck = inspect_document(path, expected_contract=expected_contract,
                                expected_address=expected_address, expected_date=expected_date)
    patches = PatchPlanBuilder().build_metadata(
        precheck.analysis, expected_contract=expected_contract,
        expected_address=expected_address, expected_date=expected_date)
    applied, verification = [], []
    engine = StreamingDocxPatchEngine()
    verifier = StreamingDocxVerifier()

    for patch in patches:
        engine.apply(path, patch)
        passed, errors = verifier.verify(path, patch)
        verification.append({
            "passed": passed,
            "findings": [{"code": code} for code in errors],
            "kind": patch.kind.value,
            "location": patch.location,
        })
        if not passed:
            raise ValueError("Post-patch verification failed: " + ", ".join(errors))
        applied.append({"kind": patch.kind.value, "location": patch.location,
                        "old": patch.old, "new": patch.new, "mark": patch.mark})

    postcheck = inspect_document(path, expected_contract=expected_contract,
                                 expected_address=expected_address, expected_date=expected_date)
    remaining = [f for f in postcheck.findings if f.code in TARGETED_RECHECK_CODES]
    recheck = {
        "passed": not remaining,
        "findings": [_finding_dict(f) for f in remaining],
        "all_findings": [_finding_dict(f) for f in postcheck.findings],
    }
    if remaining:
        raise ValueError("Повторная проверка выявила незакрытые адресные/дата/договорные нарушения")
    return applied, verification, recheck, precheck, postcheck
