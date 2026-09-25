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
        import copy

        root = ET.fromstring(raw)
        count = 0
        parents = {child: parent for parent in root.iter() for child in parent}

        for paragraph in root.findall(".//w:p", NS):
            local = 0
            while True:
                texts = paragraph.findall(".//w:t", NS)
                joined = "".join(t.text or "" for t in texts)
                start = joined.find(old)
                if start < 0:
                    break

                if mark != "blue" and joined.find(old, start + len(old)) >= 0:
                    count += joined.count(old)
                    break

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
                    break

                first = touched[0][0]
                first_value = touched[0][1]
                first_run = first
                while first_run in parents and parents[first_run].tag != f"{{{W_NS}}}r":
                    first_run = parents[first_run]
                if first_run not in parents:
                    break
                run_parent = parents[first_run]
                run_index = list(run_parent).index(first_run)

                first_start = max(0, start - touched[0][2])
                first_end = min(len(first_value), end - touched[0][2])
                prefix = first_value[:first_start]
                suffix = first_value[first_end:]

                if mark == "red-green":
                    first.text = prefix
                    red_run = copy.deepcopy(first_run)
                    green_run = copy.deepcopy(first_run)
                    red_text = red_run.find(".//w:t", NS)
                    green_text = green_run.find(".//w:t", NS)
                    red_text.text = old
                    green_text.text = new
                    _set_run_color(red_run, "red")
                    _set_run_color(green_run, "green")
                    run_parent.insert(run_index + 1, red_run)
                    run_parent.insert(run_index + 2, green_run)
                    if suffix:
                        suffix_run = copy.deepcopy(first_run)
                        suffix_run.find(".//w:t", NS).text = suffix
                        run_parent.insert(run_index + 3, suffix_run)
                    first.text = None
                    for t, value, seg_start, seg_end in touched[1:]:
                        local_start = max(0, start - seg_start)
                        local_end = min(len(value), end - seg_start)
                        t.text = value[:local_start] + value[local_end:] or None
                else:
                    first.text = prefix + new + suffix
                    _set_color(first, mark, parents)
                    for t, value, seg_start, seg_end in touched[1:]:
                        local_start = max(0, start - seg_start)
                        local_end = min(len(value), end - seg_start)
                        t.text = value[:local_start] + value[local_end:] or None

                count += 1
                local += 1
                if mark != "blue" or local > 1000:
                    break

        return ET.tostring(root, encoding="utf-8", xml_declaration=True), count

def _set_run_color(run, mark: str) -> None:
    rpr = run.find("w:rPr", NS)
    if rpr is None:
        rpr = ET.Element(f"{{{W_NS}}}rPr")
        run.insert(0, rpr)
    color = rpr.find("w:color", NS)
    if color is None:
        color = ET.SubElement(rpr, f"{{{W_NS}}}color")
    colors = {"blue": "0000FF", "green": "008000", "red": "FF0000"}
    color.set(f"{{{W_NS}}}val", colors.get(mark, "008000"))

def _set_color(text_node, mark: str, parents) -> None:
    node = text_node
    while node in parents and parents[node].tag != f"{{{W_NS}}}r":
        node = parents[node]
    if node not in parents:
        return
    _set_run_color(parents[node], mark)

