from gip.calculation_trace import CalculationResultEvidence
from gip.calculation_reconciliation import reconcile

def ev(value, section="Секция 1", limit=37.2):
    return CalculationResultEvidence(value, "мм", "прогиб", section, None, "Лира САПР", limit, "мм", str(value))

def test_same_context_matches():
    r = reconcile(ev(25.9), ev(25.9))
    assert r.status == "MATCHED_CONTEXT"

def test_context_mismatch_is_not_comparable():
    r = reconcile(ev(25.9, "Секция 1"), ev(25.9, "Секция 2"))
    assert r.status == "NOT_COMPARABLE"

def test_limit_exceedance_requires_review():
    r = reconcile(ev(42.0), ev(42.0))
    assert r.status == "REVIEW"
