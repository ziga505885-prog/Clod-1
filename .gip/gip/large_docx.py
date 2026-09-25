"""Streaming DOCX reader for reports that exceed normal in-memory limits.

The engine reads DOCX ZIP members directly and never materializes the whole
archive. It is intentionally conservative: it extracts text and structural
metadata, while leaving mutation to the deterministic patch engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator
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
    document_parts: list[tuple[str, str]] = field(default_factory=list)

    @property
    def text_chars(self) -> int:
        return sum(p.text_chars for p in self.parts)


class StreamingDocxReader:
    """Read DOCX XML members incrementally.

    Only one ZIP member is open at a time. The archive itself is never loaded
    into memory as a single byte string.
    """

    def read(self, path: str | Path, *, include_parts: bool = True) -> StreamingDocxResult:
        p = Path(path)
        if p.suffix.lower() != ".docx":
            raise ValueError("streaming DOCX reader accepts .docx files only")

        result = StreamingDocxResult()
        with ZipFile(p) as archive:
            for name in archive.namelist():
                if not self._is_word_xml(name):
                    continue
                part = self._read_part(archive, name, result, include_parts)
                result.parts.append(part)
        return result

    @staticmethod
    def _is_word_xml(name: str) -> bool:
        return name.startswith("word/") and name.endswith(".xml")

    def _read_part(
        self,
        archive: ZipFile,
        name: str,
        result: StreamingDocxResult,
        include_parts: bool,
    ) -> DocxPart:
        paragraph_count = 0
        table_count = 0
        chars = 0
        current_cell: list[str] | None = None
        current_row: list[str] | None = None

        # iterparse works directly on ZipExtFile, so the compressed member is
        # decompressed incrementally instead of being read with archive.read().
        with archive.open(name, "r") as stream:
            for event, elem in ET.iterparse(stream, events=("end",)):
                if elem.tag == _W_T and elem.text:
                    chars += len(elem.text)
                    if current_cell is not None:
                        current_cell.append(elem.text)
                    elem.clear()
                    continue

                if elem.tag == _W_P:
                    text = "".join(elem.itertext()).strip()
                    if text:
                        paragraph_count += 1
                        if include_parts:
                            result.paragraphs.append(text)
                    elem.clear()
                    continue

                if elem.tag == _W_TC:
                    text = "".join(elem.itertext()).strip()
                    if current_row is not None:
                        current_row.append(text)
                    current_cell = None
                    elem.clear()
                    continue

                if elem.tag == _W_TR:
                    if current_row is not None and include_parts:
                        result.table_rows.append(current_row)
                        table_count += 1
                    current_row = []
                    elem.clear()
                    continue

                if elem.tag == _W_TC and current_row is not None:
                    current_cell = []

        # The XML tree is streamed, but table boundaries are not required by
        # the current QA layer. Count table elements separately only when
        # present; exact table semantics remain the responsibility of the
        # table engine.
        return DocxPart(name=name, paragraphs=paragraph_count, tables=table_count, text_chars=chars)
