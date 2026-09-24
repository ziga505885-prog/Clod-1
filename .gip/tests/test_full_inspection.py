from docx import Document
from gip.full_inspection import inspect_document

def make_doc(path):
    d=Document(); d.add_paragraph("Адрес: Ростовская область, г. Ростов-на-Дону"); d.add_paragraph("Договор №123"); d.add_paragraph("Дата 01.09.2026"); d.add_paragraph("ДКР-1. Трещина в стене.")
    t=d.add_table(rows=3,cols=2); t.cell(0,0).text="№ дефекта"; t.cell(0,1).text="Категория состояния"; t.cell(1,0).text="ДКР-1"; t.cell(1,1).text="аварийное"; t.cell(2,0).text="ДКР-2"; t.cell(2,1).text="аварийное — пояснение"
    g=d.add_table(rows=2,cols=2); g.cell(0,0).text="Условные обозначения"; g.cell(0,1).text="Описание"; g.cell(1,0).text="ДКР-9"; g.cell(1,1).text="Трещина"
    d.save(path)

def test_full_checks_categories_and_graphics(tmp_path):
    p=tmp_path/"r.docx"; make_doc(p); codes={x.code for x in inspect_document(p).findings}
    assert "INVALID_CATEGORY" in codes and "DRAWING_DEFECT_MISSING_FROM_REPORT" in codes

def test_address_keeps_special_semantics(tmp_path):
    p=tmp_path/"r.docx"; make_doc(p); x=next(x for x in inspect_document(p,expected_address="Другой").findings if x.code=="ADDRESS_MISMATCH")
    assert x.patch_kind=="address"
