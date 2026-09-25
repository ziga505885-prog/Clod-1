"""Streaming metadata scanner and compatibility reader for large DOCX reports."""
from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
import re
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from .streaming_reader import StreamingReportReader

_W_NS="http://schemas.openxmlformats.org/wordprocessingml/2006/main"; _W_T=f"{{{_W_NS}}}t"
CONTRACT_RE=re.compile(r"(?:договор(?:а|у)?|контракт(?:а|у)?)[^\d№]{0,20}(?:№\s*)?([A-Za-zА-Яа-я0-9./_-]+)",re.I)
DATE_RE=re.compile(r"\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}-\d{2}-\d{2})\b")

@dataclass
class LargeDocxMetadata:
    contracts:list[str]=field(default_factory=list); dates:list[str]=field(default_factory=list); address_candidates:list[str]=field(default_factory=list); part_names:list[str]=field(default_factory=list); part_text_chars:dict[str,int]=field(default_factory=dict)

class LargeDocxMetadataScanner:
    def scan(self,path):
        p=Path(path)
        if p.suffix.lower()!=".docx": raise ValueError("metadata scanner accepts .docx files only")
        result=LargeDocxMetadata()
        with ZipFile(p) as archive:
            for name in archive.namelist():
                if not(name.startswith("word/") and name.endswith(".xml")): continue
                result.part_names.append(name); chars=0; chunks=[]
                with archive.open(name,"r") as stream:
                    for _,elem in ET.iterparse(stream,events=("end",)):
                        if elem.tag==_W_T and elem.text:
                            chars+=len(elem.text);chunks.append(elem.text)
                        elem.clear()
                text=" ".join(chunks); result.part_text_chars[name]=chars
                result.contracts.extend(m.group(1) for m in CONTRACT_RE.finditer(text))
                result.dates.extend(DATE_RE.findall(text)); result.address_candidates.extend(_addresses(text))
        result.contracts=_unique(result.contracts);result.dates=_unique(result.dates);result.address_candidates=_unique(result.address_candidates)
        return result

class StreamingDocxReader(StreamingReportReader): pass

def _addresses(text):
    results=[]
    for line in re.split(r"[\n\r]+",text):
        m=re.search(r"(?:адрес|место\s+расположения)\s*[:№-]?\s*(.+)",line,re.I)
        if m:
            value=m.group(1).strip(" .;,:»\"")
            if len(value)>=8: results.append(value)
    return results

def _unique(values):
    result=[];seen=set()
    for value in values:
        key=" ".join(value.lower().replace("ё","е").split())
        if key and key not in seen:seen.add(key);result.append(value)
    return result
