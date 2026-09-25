from pathlib import Path

from gip.calculation_workbooks import read_calculation_workbooks

ROOT = Path(__file__).resolve().parents[2]
BINDINGS = Path("/mnt/data/привязки секций к модулю грунт.xlsx")
LOADS = Path("/mnt/data/Таблицы.xlsx")


def test_reference_workbooks_are_structured():
    if not (BINDINGS.exists() and LOADS.exists()):
        return
    profile = read_calculation_workbooks(BINDINGS, LOADS)
    assert [x.section for x in profile.bindings] == ["1", "2", "3"]
    assert profile.bindings[0].azimuth == 77.25
    assert profile.bindings[2].height == -4.45
    assert len(profile.load_cases) == 24
    assert profile.load_cases[1].reliability_factor == 1.15
    assert profile.load_cases[7].reliability_factor == 1.4
