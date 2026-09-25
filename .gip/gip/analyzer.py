"""Deterministic DOCX report analyzer for GIP."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re

from .large_docx import StreamingDocxReader
from .model import Defect, InspectionReport, ReportMetadata

_CONTRACT_RE = re.compile(
    r"(?:договор(?:а|у)?|контракт(?:а|у)?)[^\d№]{0,20}"
    r"(?:№\s*)?([A-Za-zА-Яа-я0-9./_-]+)",
    re.I,
)
_DATE_RE = re.compile(
    r"\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2})\b"
)
_DEFECT_HINTS = (
    "трещин", "трещина", "разруш", "корроз", "отсутств", "повреж",
    "замач", "вымыва", "обруш", "деформац", "прогиб", "скол", "ослаб",
)


@dataclass(frozen=True)
class AnalysisResult:
    report: InspectionReport
    paragraphs: list[str] = field(default_factory=list)
    tables: list[list[list[str]]] = field(default_factory=list)
    candidate_defect_paragraphs: list[str] = field(default_factory=list)
    contract_candidates: list[str] = field(default_factory=list)
    address_candidates: list[str] = field(default_factory=list)
    date_candidates: list[str] = field(default_factory=list)
    document_part_text: list[tuple[str, str]] = field(default_factory=list)


class DocxReportAnalyzer:
    """Analyze DOCX through the streaming ZIP/XML reader.

    This avoids python-docx's whole-document object graph and is suitable for
    large reports containing many embedded photographs.
    """

    def analyze(self, path: str | Path) -> AnalysisResult:
        p = Path(path)
        if p.suffix.lower() != ".docx":
            raise ValueError("analyzer accepts .docx files only")

        parsed = StreamingDocxReader().read(p)
        paragraphs = parsed.paragraphs
        tables = [parsed.table_rows] if parsed.table_rows else []

        part_text = [
            (name, "\n".join(values))
            for name, values in parsed.paragraphs_by_part.items()
            if values
        ]
        all_text = "\n".join(text for _, text in part_text)

        contracts = _unique(m.group(1) for m in _CONTRACT_RE.finditer(all_text))
        dates = _unique(_DATE_RE.findall(all_text))
        addresses = _address_candidates(part_text)

        body_paragraphs = parsed.paragraphs_by_part.get("word/document.xml", [])
        address = self._address(body_paragraphs)

        candidates = [
            x for x in body_paragraphs
            if any(h in x.lower() for h in _DEFECT_HINTS)
        ]
        defects = [Defect(id=None, structure="", description=x) for x in candidates]

        return AnalysisResult(
            InspectionReport(
                metadata=ReportMetadata(
                    contract_number=contracts[0] if contracts else None,
                    address=address,
                    dates=dates,
                ),
                defects=defects,
            ),
            paragraphs,
            tables,
            candidates,
            contracts,
            addresses,
            dates,
            part_text,
        )

    @staticmethod
    def _address(paragraphs: list[str]) -> str | None:
        for text in paragraphs:
            if "адрес" in text.lower() and ":" in text:
                return text.split(":", 1)[1].strip()
        return None


def _unique(values) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = " ".join(
            re.findall(
                r"[a-zа-я0-9]+",
                (value or "").lower().replace("ё", "е"),
            )
        )
        if key and key not in seen:
            seen.add(key)
            out.append(value)
    return out


def _address_candidates(parts: list[tuple[str, str]]) -> list[str]:
    values: list[str] = []
    pattern = re.compile(
        r"(?:адрес|место\s+расположения)\s*[:№-]?\s*"
        r"((?:Россия\s*,?\s*)?"
        r"(?:[А-ЯЁа-яёA-Za-z-]+\s+область\s*,?\s*)?"
        r"(?:г\.?\s*)?[А-ЯЁа-яёA-Za-z-]+\s*,\s*"
        r"(?:ул\.?\s*)?[А-ЯЁа-яё0-9 .-]+,\s*\d+[А-Яа-яA-Za-z]?)",
        re.I,
    )
    for _, text in parts:
        for match in pattern.finditer(text):
            value = match.group(1).strip(" .;,:»\"")
            if value:
                values.append(value)
    return _unique(values)
