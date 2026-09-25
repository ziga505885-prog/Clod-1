"""Separate deterministic analyzer for trusted engineering calculation appendices."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re, zipfile, xml.etree.ElementTree as ET

@dataclass(frozen=True)
class CalculationFinding:
    code: str
    message: str
    source: str
    evidence: tuple[str, ...] = ()

@dataclass(frozen=True)
class CalculationTrace:
    section: str | None
    block: str | None
    model: str | None
    software: str | None
    load_context: str | None
    evidence: tuple[str, ...] = ()

@dataclass(frozen=True)
class CalculationResult:
    files: tuple[str, ...]
    standards: tuple[str, ...]
    addresses: tuple[str, ...]
    formulas: tuple[str, ...]
    results: tuple[str, ...]
    traces: tuple[CalculationTrace, ...]
    findings: tuple[CalculationFinding, ...]

_STD_RE = re.compile(r"(?i)\b(?:СП|ГОСТ)\s*[0-9.]+(?:-[0-9]+)?")
_ADDR_RE = re.compile(r"(?i)(?:Республика\s+Крым,\s*)?г\.\s*Симферополь,\s*(?:ул\.|улица)\s+[^,.;\n]{2,80},\s*\d+[А-Яа-яA-Za-z]?")
_SECTION_RE = re.compile(r"(?i)\b(?:секция|блок)\s*№?\s*([0-9]+)")
_LIRA_RE = re.compile(r"(?i)\b(?:ПК\s*)?Лира(?:\s+САПР)?\s*([0-9]{4})")
_LOAD_RE = re.compile(r"(?i)(?:расчетн(?:ое|ая)|сочетани[ея]|загружени[ея]|нагрузк[аи]).{0,120}")
_RESULT_RE = re.compile(r"(?i)(?:прогиб\s+составил|максимальный\s+расчетный\s+прогиб|предельн(?:ый|ого)\s+прогиб|фактическое\s+армирование|расчетное\s+армирование|несущая\s+способность|вывод:).{0,220}")

def _xml_text(path: Path) -> str:
    chunks=[]
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if name.startswith("word/") and name.endswith(".xml"):
                root=ET.fromstring(z.read(name))
                texts=[x.text or "" for x in root.iter() if x.tag.endswith("}t")]
                if texts: chunks.append(" ".join(texts))
    return "\n".join(chunks)

def _read_text(path: Path) -> str:
    s=path.suffix.lower()
    if s==".docx": return _xml_text(path)
    if s in {".txt",".md"}: return path.read_text(encoding="utf-8",errors="replace")
    if s==".doc": return ""
    if s==".xlsx":
        try:
            from openpyxl import load_workbook
        except ImportError: return ""
        wb=load_workbook(path,read_only=True,data_only=False); out=[]
        for ws in wb.worksheets:
            out.append(f"[SHEET:{ws.title}]")
            for row in ws.iter_rows(values_only=True):
                out.append(" ".join(str(v) for v in row if v is not None))
        return "\n".join(out)
    return ""

def _unique(values):
    seen=set(); out=[]
    for v in values:
        k=" ".join(v.lower().split())
        if k and k not in seen: seen.add(k); out.append(v.strip())
    return tuple(out)

def _trace(text):
    sections=_unique([f"Секция {m.group(1)}" for m in _SECTION_RE.finditer(text)])
    blocks=_unique(re.findall(r"(?i)\bБлок\s*№?\s*[0-9]+",text))
    software=_unique([m.group(0) for m in _LIRA_RE.finditer(text)])
    loads=_unique([m.group(0).strip() for m in _LOAD_RE.finditer(text)])
    if not (sections or blocks or software or loads): return ()
    return tuple(CalculationTrace(s,None, "Лира САПР" if software else None,
        software[0] if software else None, loads[0] if loads else None,
        tuple(x for x in (*sections,*blocks,*software) if x)) for s in (sections or (None,)))

def analyze_calculations(paths, *, expected_address=None):
    texts=[(Path(p),_read_text(Path(p))) for p in paths]
    standards=_unique([m.group(0) for _,t in texts for m in _STD_RE.finditer(t)])
    addresses=_unique([m.group(0) for _,t in texts for m in _ADDR_RE.finditer(t)])
    formulas=_unique([line.strip() for _,t in texts for line in t.splitlines() if any(x in line for x in ("=","∑","φ","γ","Ka","Кa="))])
    results=_unique([m.group(0).strip() for _,t in texts for m in _RESULT_RE.finditer(t)])
    traces=tuple(x for _,t in texts for x in _trace(t))
    findings=[]
    if len(addresses)>1: findings.append(CalculationFinding("CALC_ADDRESS_INCONSISTENT","Calculation materials contain more than one distinct extracted address.","calculations",addresses))
    if expected_address and addresses and expected_address.lower() not in {x.lower() for x in addresses}: findings.append(CalculationFinding("CALC_ADDRESS_MISMATCH","Calculation address does not contain the explicitly supplied canonical address.","calculations",addresses))
    versions=_unique([m.group(0) for _,t in texts for m in _LIRA_RE.finditer(t)])
    if len(versions)>1: findings.append(CalculationFinding("CALC_SOFTWARE_VERSION_MISMATCH","More than one explicit LIRA-SAPR version is present; verify which model each result belongs to.","calculations",versions))
    if not results: findings.append(CalculationFinding("CALC_RESULTS_NOT_EXTRACTED","No deterministic calculation-result statements were extracted; graphical result sheets require visual review.","calculations"))
    return CalculationResult(tuple(str(p) for p,_ in texts),standards,addresses,formulas,results,traces,tuple(findings))
