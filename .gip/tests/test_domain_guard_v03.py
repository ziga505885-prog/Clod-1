from gip.domain_analyzer import _extract_id


def test_bare_numbers_are_not_defect_ids():
    assert _extract_id("Плита 1 этажа, отметка +5,219") is None
    assert _extract_id("дефект 7") is None
    assert _extract_id("ДКР-7") == "ДКР-7"
    assert _extract_id("Тр-7") == "Тр-7"
