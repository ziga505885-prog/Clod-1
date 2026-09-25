"""Full deterministic inspection-report consistency analyzer."""
from __future__ import annotations
from dataclasses import dataclass
import re
from pathlib import Path
from .analyzer import AnalysisResult, DocxReportAnalyzer
from .domain_analyzer import DomainAnalysisResult, analyze_domain
from .rules import ALLOWED_CATEGORIES

@dataclass(frozen=True)
class InspectionFinding:
    code:str
    message:str
    source:str
    evidence:tuple[str,...]=()
    patch_kind:str|None=None

@dataclass(frozen=True)
class FullInspectionResult:
    analysis:AnalysisResult
    domain:DomainAnalysisResult
    findings:tuple[InspectionFinding,...]

def _norm(v:str)->str:
    return " ".join(re.findall(r"[a-zа-я0-9]+",(v or "").lower().replace("ё","е")))

def _unique(values:list[str])->list[str]:
    out=[]; seen=set()
    for v in values:
        k=_norm(v)
        if k and k not in seen: seen.add(k); out.append(v)
    return out

def _contract_values(a:AnalysisResult)->list[str]:
    return _unique(a.contract_candidates)

def _date_values(a:AnalysisResult)->list[str]:
    # Dates are evidence, not an inconsistency signal by themselves.
    # Reports legitimately contain dates for inspections, standards, calibration,
    # archives, drawings, measurements, etc.
    return _unique(a.date_candidates)

def _address_values(a:AnalysisResult)->list[str]:
    return _unique(a.address_candidates)

def _categories(a:AnalysisResult)->list[InspectionFinding]:
    out=[]; allowed=set(ALLOWED_CATEGORIES)
    for ti,t in enumerate(a.tables):
        if not t: continue
        headers=[x.strip().lower() for x in t[0]]
        for ci,h in enumerate(headers):
            # Do not confuse "степень значимости" with "категория состояния".
            if h!="категория состояния":
                continue
            for ri,row in enumerate(t[1:],1):
                v=row[ci].strip() if ci<len(row) else ""
                if v not in allowed:
                    out.append(InspectionFinding("INVALID_CATEGORY","Category must contain exactly one allowed value.",f"table:{ti}:row:{ri}",(v,)))
    return out

def inspect_document(path:str|Path,*,expected_contract:str|None=None,expected_address:str|None=None,expected_date:str|None=None)->FullInspectionResult:
    analysis=DocxReportAnalyzer().analyze(path)
    domain=analyze_domain(analysis)
    findings=[]
    contracts=_contract_values(analysis); addresses=_address_values(analysis); dates=_date_values(analysis)

    # A report may contain several date values for valid technical reasons.
    # Never mark DATE_INCONSISTENT merely because multiple dates were found.
    # A date mismatch is actionable only when a canonical expected date is supplied.
    if expected_date and dates and _norm(expected_date) not in {_norm(x) for x in dates}:
        findings.append(InspectionFinding("DATE_MISMATCH","Date differs from explicitly supplied canonical value.","document",tuple(dates),"date"))

    # Likewise, do not infer contract inconsistency from harmless references.
    # If a canonical contract is supplied, verify that it occurs in all extracted
    # contract references; otherwise leave the finding for contextual review.
    if expected_contract and contracts and any(_norm(x)!=_norm(expected_contract) for x in contracts):
        findings.append(InspectionFinding("CONTRACT_MISMATCH","A contract reference differs from the explicitly supplied canonical value.","document",tuple(contracts)))

    # Address is a document-wide consistency field, including headers/footers/textboxes.
    # Multiple distinct addresses are actionable because an old address can survive in
    # a Word header even when the body is correct.
    if len(addresses)>1:
        findings.append(InspectionFinding("ADDRESS_INCONSISTENT","More than one distinct address occurs across document parts.","document",tuple(addresses),"address"))
    if expected_address and addresses and _norm(expected_address) not in {_norm(x) for x in addresses}:
        findings.append(InspectionFinding("ADDRESS_MISMATCH","Address differs from explicitly supplied canonical value.","document",tuple(addresses),"address"))

    findings.extend(_categories(analysis))
    findings.extend(InspectionFinding(x.code,x.message,x.source,x.evidence) for x in domain.findings)
    known={x.id.casefold() for x in (*domain.report,*domain.summary) if x.id}
    for x in domain.drawings:
        if x.id and x.id.casefold() not in known:
            findings.append(InspectionFinding("DRAWING_DEFECT_MISSING_FROM_REPORT","Drawing defect identifier has no matching report or summary defect.","drawing",(x.id,x.description)))
    return FullInspectionResult(analysis,domain,tuple(findings))
