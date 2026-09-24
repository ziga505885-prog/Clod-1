from gip.model import ConditionCategory,InspectionReport,Defect
from gip.rules import valid_category
from gip.validation import validate_report
def test_categories_are_closed():
    assert {c.value for c in ConditionCategory}=={"аварийное","работоспособное","ограниченно-работоспособное","нормативное"}
    assert valid_category("аварийное"); assert not valid_category("аварийное состояние")
def test_report_validation():
    r=InspectionReport(defects=[Defect("D1","стена","трещина",category=ConditionCategory.EMERGENCY)])
    assert validate_report(r).passed
