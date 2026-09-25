from gip.calculation_trace import extract_result_evidence, match_results

def test_same_context_is_comparable():
    a = extract_result_evidence("Максимальный расчетный прогиб = 25,9 мм. Величина предельного прогиба: 37,2 мм", section="Секция 1", model="Лира САПР")[0]
    b = extract_result_evidence("Максимальный расчетный прогиб = 25,9 мм. Величина предельного прогиба: 37,2 мм", section="Секция 1", model="Лира САПР")[0]
    assert match_results(a, b).comparable

def test_different_section_is_not_comparable():
    a = extract_result_evidence("Максимальный расчетный прогиб = 25,9 мм.", section="Секция 1", model="Лира САПР")[0]
    b = extract_result_evidence("Максимальный расчетный прогиб = 25,9 мм.", section="Секция 2", model="Лира САПР")[0]
    assert not match_results(a, b).comparable
