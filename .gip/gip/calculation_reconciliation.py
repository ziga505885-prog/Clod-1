"""Conservative reconciliation of trusted calculation results.

A mismatch is reported only when both results are proven to share the same
engineering context. Otherwise the result is explicitly marked uncomparable.
"""
from __future__ import annotations

from dataclasses import dataclass
from .calculation_trace import CalculationResultEvidence, match_results

@dataclass(frozen=True)
class Reconciliation:
    status: str
    reason: str
    actual: CalculationResultEvidence
    reference: CalculationResultEvidence

def reconcile(actual: CalculationResultEvidence, reference: CalculationResultEvidence) -> Reconciliation:
    match = match_results(actual, reference)
    if not match.comparable:
        return Reconciliation("NOT_COMPARABLE", match.reason, actual, reference)
    if actual.limit is not None and actual.value > actual.limit:
        return Reconciliation("REVIEW", "actual_exceeds_declared_limit", actual, reference)
    if reference.limit is not None and reference.value > reference.limit:
        return Reconciliation("REFERENCE_CONTEXT_REQUIRES_REVIEW", "trusted_reference_contains_limit_exceedance", actual, reference)
    return Reconciliation("MATCHED_CONTEXT", "same_context_no_limit_exceedance", actual, reference)
