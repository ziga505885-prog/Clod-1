"""Deterministic DOCX report analyzer for GIP."""
from __future__ import annotations
from dataclasses import dataclass, field
import re
from pathlib import Path
from docx import Document
from .model import Defect, InspectionReport, ReportMetadata

_CONTRACT_RE=re.compile(r"(?:договор(?:а|у)?|контракт(?:а|у)?)[^\d№]{0,20}(?:№\s*)?([A-Za-zА-Яа-я0-9./_-]+)",re.I)
_DATE_RE=re.compile(r"\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2})\b")
_DEFECT_HINTS=("трещин","трещина","разруш","корроз","отсутств","повреж","замач","вымыва","обруш","деформац","прогиб","скол","ослаб")

@dataclass(frozen=True)
class AnalysisResult:
    report: InspectionReport
    paragraphs: list[str]=field(default_factory=list)
    tables: list[list[list[str]]]=field(default_factory=list)
    candidate_defect_paragraphs: list[str]=field(default_factory=list)

class DocxReportAnalyzer:
    def analyze(self,path:str|Path)->AnalysisResult:
        p=Path(path)
        if p.suffix.lower()!=".docx": raise ValueError("analyzer accepts .docx files only")
        doc=Document(p)
        paragraphs=[x.text.strip() for x in doc.paragraphs if x.text.strip()]
        tables=[[[c.text.strip() for c in row.cells] for row in t.rows] for t in doc.tables]
        text="\n".join(paragraphs)
        contracts=[m.group(1) for m in _CONTRACT_RE.finditer(text)]
        dates=_DATE_RE.findall(text)
        address=self._address(paragraphs)
        candidates=[x for x in paragraphs if any(h in x.lower() for h in _DEFECT_HINTS)]
        defects=[Defect(id=None,structure="",description=x) for x in candidates]
        return AnalysisResult(InspectionReport(metadata=ReportMetadata(contract_number=contracts[0] if contracts else None,address=address,dates=dates),defects=defects),paragraphs,tables,candidates)

    @staticmethod
    def _address(paragraphs:list[str])->str|None:
        for text in paragraphs:
            low=text.lower()
            if "адрес" in low and ":" in text:
                return text.split(":",1)[1].strip()
        return None
