from dataclasses import dataclass
from enum import Enum

class PatchKind(str,Enum):
    NORMAL="normal"; ADDRESS="address"; DATE="date"
@dataclass(frozen=True)
class Patch:
    kind: PatchKind; location:str; old:str; new:str; mark:str; reason:str

def validate_patch(p:Patch):
    if p.kind is PatchKind.NORMAL and p.mark not in {"red-green","green"}: raise ValueError("Normal patches require RED/GREEN marking")
    if p.kind in {PatchKind.ADDRESS,PatchKind.DATE} and p.mark!="blue": raise ValueError("Address/date patches must use blue marking")
    if p.kind in {PatchKind.ADDRESS,PatchKind.DATE} and p.reason: raise ValueError("Address/date patches must not carry explanatory text")
