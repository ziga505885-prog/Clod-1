import pytest
from pathlib import Path
from gip.docx_engine import DocxEngine

def test_rejects_non_docx():
    with pytest.raises(ValueError):
        DocxEngine().read_text(Path("report.pdf"))
