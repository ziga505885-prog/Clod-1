from gip.calculation_reference import make_reference

def test_trusted_calculation_reference_preserves_source():
    ref = make_reference(
        "БЦ Набережная 28А — эталонный расчет",
        ["Расчет  .doc", "Расчет  .docx", "Таблицы.xlsx", "привязки секций к модулю грунт.xlsx"],
    )
    assert ref.trusted
    assert "preserve_source_values" in ref.policy()
    assert "do_not_flag_numeric_difference_without_context" in ref.policy()
    assert ref.contains("Расчет  .docx")
