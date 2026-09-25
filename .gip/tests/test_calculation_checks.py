from gip.calculation_checks import check_comparison, check_limit

def test_actual_below_required_is_review():
    r = check_comparison("5,66", "8,55", label="Вертикальное армирование")
    assert r.code == "REQUIRED_EXCEEDS_ACTUAL"
    assert r.status == "REVIEW"

def test_value_above_limit_is_fail():
    r = check_limit("42", "30", label="Прогиб")
    assert r.code == "VALUE_EXCEEDS_LIMIT"
    assert r.status == "FAIL"

def test_value_within_limit_passes():
    r = check_limit("25,9", "37,2", label="Прогиб")
    assert r.status == "PASS"
