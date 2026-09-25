"""Boundary-preserving streaming DOCX reader for large reports."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
T, P, TBL, TR, TC = (f"{{{W}}}{x}" for x in ("t", "p", "tbl", "tr", "tc"))


@dataclass
class StreamingReport:
    paragraphs_by_part: dict[str, list[str]] = field(default_factory=dict)
    tables: list[list[list[str]]] = field(default_factory=list)
    text_chars: int = 0

    @property
    def paragraphs(self) -> list[str]:
        return self.paragraphs_by_part.get("word/document.xml", [])


class StreamingReportReader:
    def read(self, path: str | Path) -> StreamingReport:
        result = StreamingReport()
        with ZipFile(path) as archive:
            for name in archive.namelist():
                if not (name.startswith("word/") and name.endswith(".xml")):
                    continue
                with archive.open(name) as stream:
                    paragraphs: list[str] = []
                    in_table = False
                    with_cell = False
                    current: list[str] = []
                    tables: list[list[list[str]]] = []
                    table: list[list[str]] = []
                    row: list[str] = []
                    cell: list[str] = []
                    paragraph: list[str] = []

                    for event, elem in ET.iterparse(stream, events=("start", "end")):
                        if event == "start":
                            if elem.tag == TBL:
                                in_table = True
                                table = []
                            elif elem.tag == TR and in_table:
                                row = []
                            elif elem.tag == TC and in_table:
                                with_cell = True
                                cell = []
                            elif elem.tag == P:
                                paragraph = []
                            continue

                        if elem.tag == T:
                            text = elem.text or ""
                            result.text_chars += len(text)
                            paragraph.append(text)
                            if with_cell:
                                cell.append(text)
                        elif elem.tag == P:
                            text = "".join(paragraph).strip()
                            if text and not with_cell:
                                paragraphs.append(text)
                            paragraph = []
                        elif elem.tag == TC and in_table:
                            value = " ".join("".join(cell).split())
                            row.append(value)
                            cell = []
                            with_cell = False
                        elif elem.tag == TR and in_table:
                            if row:
                                table.append(row)
                            row = []
                        elif elem.tag == TBL:
                            if table:
                                tables.append(table)
                            table = []
                            in_table = False
                        elem.clear()

                result.paragraphs_by_part[name] = paragraphs
                if name == "word/document.xml":
                    result.tables = tables
        return result
