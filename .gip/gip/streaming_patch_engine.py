"""ZIP/XML based DOCX patching for very large reports.

Only XML parts are rewritten; the whole document is never loaded by python-docx.
Address/date replacements are blue and carry no explanatory text.
"""
from __future__ import annotations
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile, ZIP_DEFLATED
import re
import xml.etree.ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
ET.register_namespace("w", W_NS)

class StreamingDocxPatchEngine:
    def apply(self, path: str | Path, patch) -> None:
        path = Path(path)
        old = patch.old
        if not old:
            raise ValueError("Patch.old must not be empty")
        with ZipFile(path, "r") as zin:
            xml_names = [n for n in zin.namelist() if n.startswith("word/") and n.endswith(".xml")]
            occurrences = 0
            matched_parts: dict[str, bytes] = {}
            for name in xml_names:
                raw = zin.read(name)
                if "<w:t" not in raw.decode("utf-8", "ignore"):
                    continue
                changed, count = self._patch_xml(raw, old, patch.new, patch.mark)
                occurrences += count
                if count:
                    matched_parts[name] = changed
            if occurrences != 1:
                raise ValueError(f"Expected exactly one DOCX occurrence, found {occurrences}: {old!r}")
            with NamedTemporaryFile(suffix=".docx", delete=False, dir=path.parent) as tmp:
                temp_path = Path(tmp.name)
            try:
                with ZipFile(temp_path, "w", ZIP_DEFLATED) as zout:
                    for item in zin.infolist():
                        data = matched_parts.get(item.filename)
                        if data is None:
                            data = zin.read(item.filename)
                        zout.writestr(item, data)
                temp_path.replace(path)
            finally:
                if temp_path.exists():
                    temp_path.unlink()

    @staticmethod
    def _patch_xml(raw: bytes, old: str, new: str, mark: str):
        root = ET.fromstring(raw)
        count = 0
        parents = {child: parent for parent in root.iter() for child in parent}
        for paragraph in root.findall(".//w:p", NS):
            texts = paragraph.findall(".//w:t", NS)
            if not texts:
                continue
            joined = "".join(t.text or "" for t in texts)
            start = joined.find(old)
            if start < 0:
                continue
            # Keep this conservative: replacement must fit one contiguous text span.
            pos = 0
            for t in texts:
                value = t.text or ""
                end = pos + len(value)
                if pos <= start and start + len(old) <= end:
                    local = start - pos
                    t.text = value[:local] + new + value[local + len(old):]
                    _set_color(t, mark, parents)
                    count += 1
                    break
                pos = end
        return ET.tostring(root, encoding="utf-8", xml_declaration=True), count

def _set_color(text_node, mark: str, parents) -> None:
    node = text_node
    while node in parents and parents[node].tag != f"{{{W_NS}}}r":
        node = parents[node]
    if node not in parents:
        return
    run = parents[node]
    rpr = run.find("w:rPr", NS)
    if rpr is None:
        rpr = ET.Element(f"{{{W_NS}}}rPr")
        run.insert(0, rpr)
    color = rpr.find("w:color", NS)
    if color is None:
        color = ET.SubElement(rpr, f"{{{W_NS}}}color")
    color.set(f"{{{W_NS}}}val", "0000FF" if mark == "blue" else "008000")
