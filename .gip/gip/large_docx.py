"""Streaming metadata scanner and compatibility reader for large DOCX reports."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from .streaming_reader import StreamingReportReader

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W_T = f"{{{_W_NS}}}t"

CONTRACT_RE = re.compile(
    r"(?:договор(?:а|у)?|контракт(?:а|у)?)[^\d№]{0,20}"
    r"(?:№\s*)?([A-Za-zА-Яа-я0-9./_-]+)", re.I,
)
DATE_RE = re.compile(
    r"\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2})\b"
)


@dataclass
class LargeDocxMetadata:
    contracts: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    address_candidates: list[str] = field(default_factory=list)
    part_names: list[str] = field(default_factory=list)
    part_text_chars: dict[str, int] = field(default_factory=dict)


class LargeDocxMetadataScanner:
    """Scan Word XML parts one at a time; never materialize the DOCX."""

    def scan(self, path: str | Path) -> LargeDocxMetadata:
        p = Path(path)
        if p.suffix.lower() != ".docx":
            raise ValueError("metadata scanner accepts .docx files only")

        result = LargeDocxMetadata()
        with ZipFile(p) as archive:
            for name in archive.namelist():
                if not (name.startswith("word/") and name.endswith(".xml")):
                    continue
                result.part_names.append(name)
                chars = 0
                text_chunks: list[str] = []
                with archive.open(name, "r") as stream:
                    for _, elem in ET.iterparse(stream, events=("end",)):
                        if elem.tag == _W_T and elem.text:
                            chars += len(elem.text)
                            text_chunks.append(elem.text)
                        elem.clear()
                text = " ".join(text_chunks)
                result.part_text_chars[name] = chars
                result.contracts.extend(match.group(1) for match in CONTRACT_RE.finditer(text))
                result.dates.extend(DATE_RE.findall(text))
                result.address_candidates.extend(_addresses(text))

        result.contracts = _unique(result.contracts)
        result.dates = _unique(result.dates)
        result.address_candidates = _unique(result.address_candidates)
        return result


class StreamingDocxReader(StreamingReportReader):
    """Backward-compatible name for the boundary-preserving streaming reader."""


def _addresses(text: str) -> list[str]:
    pattern = re.compile(
        r"(?:адрес|место\s+расположения)\s*[:№-]?\s*"
        r"((?:Россия\s*,?\s*)?"
        r"(?:[А-ЯЁа-яёA-Za-z-]+\s+область\s*,?\s*)?"
        r"(?:г\.?\s*)?[А-ЯЁа-яёA-Za-z-]+\s*,\s*"
        r"(?:ул\.?\s*)?[А-ЯЁа-яё0-9 .-]+,\s*\d+[А-Яа-яA-Za-z]?)",
        re.I,
    )
    return [match.group(1).strip(" .;,:»\"") for match in pattern.finditer(text)]


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = " ".join(value.lower().replace("ё", "е").split())
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result
