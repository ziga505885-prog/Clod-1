"""ZIP/XML DOCX patching with support for text split across Word runs."""
from __future__ import annotations
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
ET.register_namespace("w", W_NS)

class StreamingDocxPatchEngine:
    def apply(self, path: str | Path, patch) -> None:
        path = Path(path)
        if not patch.old:
            raise ValueError("Patch.old must not be empty")
        with ZipFile(path, "r") as zin:
            matched_parts = {}
            occurrences = 0
            for name in zin.namelist():
                if not (name.startswith("word/") and name.endswith(".xml")):
                    continue
                raw = zin.read(name)
                if "<w:t" not in raw.decode("utf-8", "ignore"):
                    continue
                changed, count = self._patch_xml(raw, patch.old, patch.new, patch.mark)
                occurrences += count
                if count:
                    matched_parts[name] = changed
            if occurrences != 1:
                raise ValueError(f"Expected exactly one DOCX occurrence, found {occurrences}: {patch.old!r}")
            with NamedTemporaryFile(suffix=".docx", delete=False, dir=path.parent) as tmp:
                temp_path = Path(tmp.name)
            try:
                with ZipFile(temp_path, "w", ZIP_DEFLATED) as zout:
                    for item in zin.infolist():
                        zout.writestr(item, matched_parts.get(item.filename, zin.read(item.filename)))
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

            end = start + len(old)
            pos = 0
            touched = []
            for t in texts:
                value = t.text or ""
                seg_start, seg_end = pos, pos + len(value)
                if seg_end > start and seg_start < end:
                    touched.append((t, value, seg_start, seg_end))
                pos = seg_end

            if not touched:
                continue

            # Preserve the text outside the match. Put the complete replacement
            # into the first touched run and remove only the matched portions
            # from subsequent runs. This handles addresses/dates split by Word
            # formatting runs without disturbing surrounding text.
            first = touched[0][0]
            first_value = touched[0][1]
            first_start = max(0, start - touched[0][2])
            first_end = min(len(first_value), end - touched[0][2])
            first.text = first_value[:first_start] + new + first_value[first_end:]
            _set_color(first, mark, parents)

            for t, value, seg_start, seg_end in touched[1:]:
                local_start = max(0, start - seg_start)
                local_end = min(len(value), end - seg_start)
                t.text = value[:local_start] + value[local_end:]
                if (t.text or "") == "":
                    t.text = None

            count += 1
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
