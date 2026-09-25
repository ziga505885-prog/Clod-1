"""Streaming DOCX reader for reports that exceed normal in-memory limits.

The reader opens each Word XML member through ZipExtFile and parses it with
iterparse. It never materializes the complete DOCX archive.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W_P = f"{{{_W_NS}}}p"
_W_T = f"{{{_W_NS}}}t"
_W_TC = f"{{{_W_NS}}}tc"
_W_TR = f"{{{_W_NS}}}tr"


@dataclass(frozen=True)
class DocxPart:
    name: str
    paragraphs: int = 0
    tables: int = 0
    text_chars: int = 0


@dataclass
class StreamingDocxResult:
    parts: list[DocxPart] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    table_rows: list[list[str]] = field(default_factory=list)

    @property
    def text_chars(self) -> int:
        return sum(p.text_chars for p in self.parts)


class StreamingDocxReader:
    """Incrementally read DOCX XML without loading the archive into memory."""

    def read(
        self,
        path: str | Path,
        *,
        collect_paragraphs: bool = True,
        collect_tables: bool = True,
    ) -> StreamingDocxResult:
        p = Path(path)
        if p.suffix.lower() != ".docx":
            raise ValueError("streaming DOCX reader accepts .docx files only")

        result = StreamingDocxResult()
        with ZipFile(p) as archive:
            for name in archive.namelist():
                if not self._is_word_xml(name):
                    continue
                result.parts.append(
                    self._read_part(
                        archive,
                        name,
                        result,
                        collect_paragraphs=collect_paragraphs,
                        collect_tables=collect_tables,
                    )
                )
        return result

    @staticmethod
    def _is_word_xml(name: str) -> bool:
        return name.startswith("word/") and name.endswith(".xml")

    def _read_part(
        self,
        archive: ZipFile,
        name: str,
        result: StreamingDocxResult,
        *,
        collect_paragraphs: bool,
        collect_tables: bool,
    ) -> DocxPart:
        paragraph_count = 0
        table_count = 0
        chars = 0
        current_row: list[str] | None = None
        current_cell: list[str] | None = None

        with archive.open(name, "r") as stream:
            for event, elem in ET.iterparse(stream, events=("start", "end")):
                if event == "start":
                    if elem.tag == _W_TR:
                        current_row = []
                    elif elem.tag == _W_TC:
                        current_cell = []
                    continue

                if elem.tag == _W_T:
                    if elem.text:
                        chars += len(elem.text)
                        if current_cell is not None:
                            current_cell.append(elem.text)
                    elem.clear()
                    continue

                if elem.tag == _W_TC:
                    if current_cell is not None and current_row is not None:
                        current_row.append("".join(current_cell).strip())
                    current_cell = None
                    elem.clear()
                    continue

                if elem.tag == _W_TR:
                    table_count += 1
                    if collect_tables and current_row:
                        result.table_rows.append(current_row)
                    current_row = None
                    elem.clear()
                    continue

                if elem.tag == _W_P:
                    text = "".join(elem.itertext()).strip()
                    if text:
                        paragraph_count += 1
                        if collect_paragraphs:
                            result.paragraphs.append(text)
                    elem.clear()

        return DocxPart(
            name=name,
            paragraphs=paragraph_count,
            tables=table_count,
            text_chars=chars,
        )
