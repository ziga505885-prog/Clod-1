from gip.calculation_workbooks import CalculationWorkbookProfile, SectionSoilBinding, LoadCase
from gip.calculation_workbook_chain import build_input_chains

def test_builds_section_to_load_chain():
    p = CalculationWorkbookProfile(
        bindings=[SectionSoilBinding("1", lira_point=(77.25, 0.0), azimuth=77.25, height=0.0)],
        load_cases=[LoadCase("2", "snow", "snow", None, 1.15)],
    )
    c = build_input_chains(p)[0]
    assert c.section == "1"
    assert c.azimuth == 77.25
    assert c.soil_binding == (77.25, 0.0)
    assert c.load_cases == ("2",)
