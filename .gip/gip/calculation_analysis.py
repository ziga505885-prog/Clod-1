"""Separate deterministic analyzer for engineering calculation appendices.

The calculation analyzer is intentionally independent from the main report
defect QA pipeline. It extracts calculation evidence and flags only explicit,
deterministic inconsistencies; it does not silently recalculate or invent
engineering assumptions.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

@dataclass(frozen=True)
class CalculationFinding:
    code: str
    message: str
    source: str
    evidence: tuple[str, ...] = ()

@dataclass(frozen=True)
class CalculationResult:
    files: tuple[str, ...]
    standards: tuple[str, ...]
    addresses: tuple[str, ...]
    formulas: tuple[str, ...]
    results: tuple[str, ...]
    findings: tuple[CalculationFinding, ...]

_STD_RE = re.compile(r"(?i)\\b(?:СП|ГОСТ)\\s*[0-9.]+(?:-[0-9]+)?")
_ADDR_RE = re.compile(
    r"(?i)(?:Республика\\s+Крым,\\s*)?г\\.\\s*Симферополь,\\s*"
    r"(?:ул\\.|улица)\\s+[^,.;\\n]{2,80},\\s*\\d+[А-Яа-яA-Za-z]?"
)
_RESULT_RE = re.compile(
    r"(?i)(?:прогиб\\s+составил|крен\\s+составил|предельн(?:ый|ого)\\s+прогиб|"
    r"фактическое\\s+армирование|расчетное\\s+армирование|вывод:).{0,180}"
)

def _docx_text(path: Path) -> str:
    chunks: list[str] = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not (name.startswith("word/") and name.endswith(".xml")):
                continue
            root = ET.fromstring(z.read(name))
            texts = [x.text or "" for x in root.iter() if x.tag.endswith("}t")]
            if texts:
                chunks.append(" ".join(texts))
    return "\n".join(chunks)

def _read_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        return _docx_text(path)
    if path.suffix.lower() in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".doc":
        return ""
    if path.suffix.lower() == ".xlsx":
        try:
            from openpyxl import load_workbook
        except ImportError:
            return ""
        wb = load_workbook(path, read_only=True, data_only=False)
        parts = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                parts.append(" ".join(str(v) for v in row if v is not None))
        return "\n".join(parts)
    return ""

def _unique(values: list[str]) -> tuple[str, ...]:
    seen = set()
    out = []
    for value in values:
        key = " ".join(value.lower().split())
        if key and key not in seen:
            seen.add(key)
            out.append(value.strip())
    return tuple(out)

def analyze_calculations(paths: list[str | Path], *, expected_address: str | None = None) -> CalculationResult:
    texts = []
    for raw in paths:
        path = Path(raw)
        text = _read_text(path)
        texts.append((path, text))

    standards = _unique([m.group(0) for _, text in texts for m in _STD_RE.finditer(text)])
    addresses = _unique([m.group(0) for _, text in texts for m in _ADDR_RE.finditer(text)])
    formulas = _unique([
        line.strip() for _, text in texts for line in text.splitlines()
        if any(token in line for token in ("=", "∑", "φ", "γ", "Ka", "Кa="))
    ])
    results = _unique([m.group(0).strip() for _, text in texts for m in _RESULT_RE.finditer(text)])

    findings: list[CalculationFinding] = []
    if len(addresses) > 1:
        findings.append(CalculationFinding(
            "CALC_ADDRESS_INCONSISTENT",
            "Calculation materials contain more than one distinct extracted address.",
            "calculations", addresses
        ))
    if expected_address and addresses and expected_address.lower() not in {x.lower() for x in addresses}:
        findings.append(CalculationFinding(
            "CALC_ADDRESS_MISMATCH",
            "Calculation address does not contain the explicitly supplied canonical address.",
            "calculations", addresses
        ))

    if any("Лира САПР 2020" in text for _, text in texts) and any("Лира САПР 2022" in text for _, text in texts):
        findings.append(CalculationFinding(
            "CALC_SOFTWARE_VERSION_MISMATCH",
            "Calculation materials explicitly mention both LIRA-SAPR 2020 and 2022; this requires source verification.",
            "calculations", ("ПК Лира САПР 2020", "ПК Лира САПР 2022")
        ))

    if not results:
        findings.append(CalculationFinding(
            "CALC_RESULTS_NOT_EXTRACTED",
            "No deterministic calculation-result statements were extracted; graphical result sheets require visual review.",
            "calculations"
        ))

    return CalculationResult(
        tuple(str(Path(p)) for p, _ in texts),
        standards, addresses, formulas, results, tuple(findings)
    )
