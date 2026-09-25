"""Deterministic DOCX report analyzer for GIP."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import re
from .streaming_reader import StreamingReportReader
from .model import Defect, InspectionReport, ReportMetadata

_CONTRACT_RE = re.compile(r"(?:договор(?:а|у)?|контракт(?:а|у)?)[^\d№]{0,20}(?:№\s*)?([A-Za-zА-Яа-я0-9./_-]+)", re.I)
_DATE_RE = re.compile(r"\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2})\b")
_DEFECT_HINTS = ("трещин", "трещина", "разруш", "корроз", "отсутств", "повреж", "замач", "вымыва", "обруш", "деформац", "прогиб", "скол", "ослаб")


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
    def analyze(self, path: str | Path) -> AnalysisResult:
        parsed = StreamingReportReader().read(path)
        part_text = [(n, "\n".join(v)) for n, v in parsed.paragraphs_by_part.items() if v]
        all_text = "\n".join(t for _, t in part_text)
        contracts = _unique(m.group(1) for m in _CONTRACT_RE.finditer(all_text))
        dates = _unique(_DATE_RE.findall(all_text))
        addresses = _address_candidates(part_text)
        body = parsed.paragraphs
        address = self._address(body)
        candidates = [p for p in body if any(h in p.lower() for h in _DEFECT_HINTS)]
        defects = [Defect(id=None, structure="", description=p) for p in candidates]
        return AnalysisResult(
            InspectionReport(metadata=ReportMetadata(
                contract_number=contracts[0] if contracts else None,
                address=address,
                dates=dates,
            ), defects=defects),
            body, parsed.tables, candidates, contracts, addresses, dates, part_text,
        )

    @staticmethod
    def _address(paragraphs: list[str]) -> str | None:
        for text in paragraphs:
            if "адрес" in text.lower() and ":" in text:
                return text.split(":", 1)[1].strip()
        return None


def _unique(values) -> list[str]:
    out, seen = [], set()
    for value in values:
        key = " ".join(re.findall(r"[a-zа-я0-9]+", (value or "").lower().replace("ё", "е")))
        if key and key not in seen:
            seen.add(key)
            out.append(value)
    return out


def _address_candidates(parts):
    pattern = re.compile(r"(?:адрес|место\s+расположения)\s*[:№-]?\s*((?:Россия\s*,?\s*)?(?:[А-ЯЁа-яёA-Za-z-]+\s+область\s*,?\s*)?(?:г\.?\s*)?[А-ЯЁа-яёA-Za-z-]+\s*,\s*(?:ул\.?\s*)?[А-ЯЁа-яё0-9 .-]+,\s*\d+[А-Яа-яA-Za-z]?)", re.I)
    return _unique(match.group(1).strip(" .;,:»\"") for _, text in parts for match in pattern.finditer(text))
