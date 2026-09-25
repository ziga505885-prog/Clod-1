from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET

from gip.streaming_patch_engine import StreamingDocxPatchEngine
from gip.patches import Patch, PatchKind

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

def _xml(text):
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W}"><w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>'''.encode()

def _docx(path: Path, parts):
    with ZipFile(path, "w", ZIP_DEFLATED) as z:
        for name, data in parts.items():
            z.writestr(name, data)

def test_streaming_patch_header_address(tmp_path):
    path = tmp_path / "report.docx"
    _docx(path, {
        "word/document.xml": _xml("Основной текст"),
        "word/header2.xml": _xml("Адрес: Пушкинская, 53А"),
        "word/footer1.xml": _xml("footer"),
    })
    patch = Patch(PatchKind.ADDRESS, "Пушкинская, 53А", "Республика Крым, г. Симферополь, ул. Набережная, 28А", "blue")
    StreamingDocxPatchEngine().apply(path, patch)
    with ZipFile(path) as z:
        header = z.read("word/header2.xml").decode()
        footer = z.read("word/footer1.xml").decode()
    assert "Пушкинская, 53А" not in header
    assert "Набережная, 28А" in header
    assert "footer" in footer
    root = ET.fromstring(header)
    color = root.find(".//{"+W+"}color")
    assert color is not None and color.attrib.get("{"+W+"}val") == "0000FF"

def test_streaming_patch_address_replaces_all_matches(tmp_path):
    path = tmp_path / "report.docx"
    _docx(path, {"word/document.xml": _xml("Ошибка Ошибка")})
    patch = Patch(PatchKind.ADDRESS, "Ошибка", "Исправлено", "blue")
    StreamingDocxPatchEngine().apply(path, patch)
    with ZipFile(path) as z:
        data = z.read("word/document.xml").decode()
    assert data.count("Исправлено") == 2
    assert "Ошибка" not in data
    assert data.count('w:val="0000FF"') == 2


def test_streaming_patch_normal_is_green(tmp_path):
    path = tmp_path / "report.docx"
    _docx(path, {"word/document.xml": _xml("старый текст")})
    patch = Patch(PatchKind.NORMAL, "старый текст", "новый текст", "green")
    StreamingDocxPatchEngine().apply(path, patch)
    with ZipFile(path) as z:
        data = z.read("word/document.xml")
    assert "новый текст" in data.decode()
    assert "старый текст" not in data.decode()
    root = ET.fromstring(data)
    color = root.find(".//{"+W+"}color")
    assert color is not None and color.attrib.get("{"+W+"}val") == "008000"


def test_streaming_patch_across_word_runs(tmp_path):
    path = tmp_path / "split.docx"
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W}"><w:body><w:p>
<w:r><w:t>Адрес: Пушки</w:t></w:r><w:r><w:t>нская, 53А</w:t></w:r>
</w:p></w:body></w:document>'''.encode()
    _docx(path, {"word/document.xml": xml})
    patch = Patch(PatchKind.ADDRESS, "Пушкинская, 53А", "Набережная, 28А", "blue")
    StreamingDocxPatchEngine().apply(path, patch)
    with ZipFile(path) as z:
        data = z.read("word/document.xml").decode()
    assert "Пушкинская, 53А" not in data
    assert "Набережная, 28А" in data
    assert "Адрес: " in data


def test_streaming_patch_red_green_keeps_old_and_adds_green(tmp_path):
    path = tmp_path / "audit.docx"
    _docx(path, {"word/document.xml": _xml("старый текст")})
    patch = Patch(PatchKind.NORMAL, "старый текст", "новый текст", "red-green")
    StreamingDocxPatchEngine().apply(path, patch)
    with ZipFile(path) as z:
        data = z.read("word/document.xml").decode()
    assert "старый текст" in data
    assert "новый текст" in data
    assert 'w:val="FF0000"' in data
    assert 'w:val="008000"' in data
