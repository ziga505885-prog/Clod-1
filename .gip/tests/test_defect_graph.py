from gip.defect_graph import build_defect_graph, validate_defect_consistency
from gip.model import Defect, InspectionReport

def d(desc, **kw):
    return Defect(id=None, structure="стена", description=desc, **kw)

def test_detects_defect_missing_from_summary():
    report=InspectionReport(defects=[d("вертикальная трещина в кладке")])
    findings=validate_defect_consistency(report)
    assert any(f.code=="DEFECT_MISSING_FROM_SUMMARY" for f in findings)

def test_matching_summary_is_not_flagged():
    x=d("вертикальная трещина в кладке")
    report=InspectionReport(defects=[x], defect_summary=[d("вертикальная трещина в кладке")],
                            defect_characteristics=[d("вертикальная трещина в кладке")])
    assert validate_defect_consistency(report)==[]

def test_graph_records_sources():
    x=d("разрушение отделочного слоя", source_drawings=["Лист 2"], source_photos=["Фото 5"])
    g=build_defect_graph(InspectionReport(defects=[x]))
    node=next(iter(g.nodes.values()))
    assert node.sources == {"report","drawing","photo"}
