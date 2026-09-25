from gip.defect_reconciliation import reconcile_defects
from gip.model import Defect, InspectionReport

def test_missing_summary_is_reported():
    report = InspectionReport(defects=[Defect(id="ДКР-1", structure="Стена", description="Трещина")])
    findings = reconcile_defects(report)
    assert any(f.code == "DEFECT_MISSING_FROM_SUMMARY" for f in findings)

def test_duplicate_id_is_reported():
    report = InspectionReport(defects=[
        Defect(id="ДКР-1", structure="Стена", description="Трещина"),
        Defect(id="ДКР-1", structure="Стена", description="Отслоение"),
    ])
    findings = reconcile_defects(report)
    assert any(f.code == "DUPLICATE_DEFECT_ID" for f in findings)
