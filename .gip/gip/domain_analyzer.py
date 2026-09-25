"""Domain-level analyzer for engineering inspection report consistency."""
from __future__ import annotations
from dataclasses import dataclass
import re
from .analyzer import AnalysisResult

_ID_RE = re.compile(r"\b(ДКР|Деф|Дефект|Тр|Т|П|К|С|Л|Г)\s*[-№]?\s*(\d+)\b", re.I)
_SECTION4_RE = re.compile(r"^\s*4(?:[.\s]|$).*характеристик", re.I)
_SUMMARY_HINTS = ("сводная ведомость", "ведомость дефектов", "сводная таблица", "дефектов")
_CHARACTERISTIC_HINTS = ("характеристик дефектов", "характеристика дефектов")
_DRAWING_HINTS = ("условные обозначения", "графика", "схема", "чертеж")

@dataclass(frozen=True)
class DomainFinding:
    code: str; message: str; source: str; evidence: tuple[str,...]=()

@dataclass(frozen=True)
class DomainDefect:
    id: str|None; description: str; source: str; row_index: int|None=None

@dataclass(frozen=True)
class DomainAnalysisResult:
    summary: tuple[DomainDefect,...]=()
    characteristics: tuple[DomainDefect,...]=()
    report: tuple[DomainDefect,...]=()
    drawings: tuple[DomainDefect,...]=()
    findings: tuple[DomainFinding,...]=()

def _norm(value:str)->str:
    return " ".join(re.findall(r"[a-zа-я0-9]+",(value or "").lower().replace("ё","е")))

def _extract_id(value:str)->str|None:
    m=_ID_RE.search(value or "")
    if not m: return None
    prefix,num=m.group(1).casefold(),m.group(2)
    if prefix=="дкр": return f"ДКР-{num}"
    if prefix=="тр": return f"Тр-{num}"
    if prefix in {"п","к","с","л","г","т"}: return f"{prefix.upper()}-{num}"
    # Generic words such as "дефект 7" are not IDs.
    return None

def _looks_like_summary(headers,rows):
    blob=_norm(" ".join(headers)+" "+" ".join(" ".join(r) for r in rows[:3]))
    return any(_norm(x) in blob for x in _SUMMARY_HINTS)

def _looks_like_characteristics(headers,rows):
    blob=_norm(" ".join(headers)+" "+" ".join(" ".join(r) for r in rows[:3]))
    return any(_norm(x) in blob for x in _CHARACTERISTIC_HINTS) or ("характеристика" in blob and "дефект" in blob)

def _looks_like_drawing(headers,rows):
    blob=_norm(" ".join(headers)+" "+" ".join(" ".join(r) for r in rows[:3]))
    return any(_norm(x) in blob for x in _DRAWING_HINTS)

def _row_defect(row,headers,source,row_index):
    text=" | ".join(x for x in row if x).strip()
    if not text: return None
    id_value=None
    for i,h in enumerate(headers):
        if any(k in _norm(h) for k in ("номер","обознач","дефект")) and i<len(row):
            id_value=_extract_id(row[i])
            if id_value: break
    if id_value is None and row:
        # For compact keyed tables, inspect all cells, but never bare numbers.
        for cell in row[:2]:
            id_value=_extract_id(cell)
            if id_value: break
    return DomainDefect(id_value,text,source,row_index)

def _find_section4_paragraphs(paragraphs):
    indexes=set(); active=False
    for i,p in enumerate(paragraphs):
        if _SECTION4_RE.search(p): active=True; indexes.add(i); continue
        if active and re.match(r"^\s*5(?:[.\s]|$)",p,re.I): active=False
        elif active: indexes.add(i)
    return indexes

def analyze_domain(analysis):
    summary=[]; characteristics=[]; drawings=[]
    for table in analysis.tables:
        if not table: continue
        headers,rows=table[0],table[1:]
        if _looks_like_summary(headers,rows):
            summary += [x for ri,row in enumerate(rows,1) if (x:=_row_defect(row,headers,"summary",ri))]
        elif _looks_like_characteristics(headers,rows):
            characteristics += [x for ri,row in enumerate(rows,1) if (x:=_row_defect(row,headers,"characteristics",ri))]
        elif _looks_like_drawing(headers,rows):
            drawings += [x for ri,row in enumerate(rows,1) if (x:=_row_defect(row,headers,"drawing",ri))]
    report=[DomainDefect(_extract_id(p),p,"report",i) for i,p in enumerate(analysis.candidate_defect_paragraphs)]
    findings=[]
    _compare_sources(summary,"summary",characteristics,"characteristics",findings)
    _compare_sources(report,"report",summary,"summary",findings)
    _compare_sources(report,"report",characteristics,"characteristics",findings)
    _duplicates(summary,"summary",findings); _duplicates(characteristics,"characteristics",findings); _duplicates(drawings,"drawing",findings)
    if not _find_section4_paragraphs(analysis.paragraphs) and characteristics:
        findings.append(DomainFinding("SECTION4_NOT_FOUND","A characteristics table was found, but a textual section 4 heading was not detected.","characteristics"))
    return DomainAnalysisResult(tuple(summary),tuple(characteristics),tuple(report),tuple(drawings),tuple(findings))

def _same(a,b):
    if a.id and b.id: return a.id.casefold()==b.id.casefold()
    na,nb=_norm(a.description),_norm(b.description); sa,sb=set(na.split()),set(nb.split())
    common=len(sa&sb)
    return bool(na and nb and common>=3 and (sa<=sb or sb<=sa or common/max(len(sa),len(sb))>=.6))

def _compare_sources(left,left_name,right,right_name,findings):
    for item in left:
        if not any(_same(item,o) for o in right):
            findings.append(DomainFinding(f"DEFECT_MISSING_FROM_{right_name.upper()}",f"Defect from {left_name} has no conservative match in {right_name}.",left_name,(item.description,)))

def _duplicates(items,source,findings):
    seen={}
    for item in items:
        key=item.id.casefold() if item.id else _norm(item.description)
        if key and key in seen:
            findings.append(DomainFinding("DUPLICATE_DEFECT",f"Duplicate defect identity detected in {source}.",source,(seen[key].description,item.description)))
        elif key: seen[key]=item
