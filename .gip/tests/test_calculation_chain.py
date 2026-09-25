from gip.calculation_chain import build_chain, CalculationChainNode

def test_chain_keeps_engineering_context():
    result = CalculationChainNode("result", "vertical deflection", 16.0, "мм", "Секция 1")
    limit = CalculationChainNode("limit", "vertical deflection", 30.0, "мм", "Секция 1")
    c = build_chain(
        "Секция 1",
        soil="IGE 1-4",
        load_cases=("1", "8"),
        model="Лира САПР 2022",
        element="перекрытие",
        result=result,
        limit=limit,
        conclusion="перемещения не превышают предельных",
    )
    assert c.find("soil")[0].name == "IGE 1-4"
    assert len(c.find("load_case")) == 2
    assert c.find("result")[0].value == 16.0
    assert c.find("limit")[0].value == 30.0
    assert c.find("conclusion")[0].name.startswith("перемещения")
