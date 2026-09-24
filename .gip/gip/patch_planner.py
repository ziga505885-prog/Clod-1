"""Conservative metadata patch-plan builder."""
from __future__ import annotations
from dataclasses import dataclass
from .patches import Patch,PatchKind
from .analyzer import AnalysisResult

@dataclass(frozen=True)
class PatchPlanBuilder:
    def build_metadata(self,analysis:AnalysisResult,expected_contract:str|None=None,expected_address:str|None=None,expected_date:str|None=None)->list[Patch]:
        patches=[]
        if expected_contract and analysis.report.metadata.contract_number and analysis.report.metadata.contract_number!=expected_contract:
            patches.append(Patch(PatchKind.NORMAL,"metadata",analysis.report.metadata.contract_number,expected_contract,"green",""))
        if expected_address and analysis.report.metadata.address and analysis.report.metadata.address!=expected_address:
            patches.append(Patch(PatchKind.ADDRESS,"metadata",analysis.report.metadata.address,expected_address,"blue",""))
        if expected_date:
            for d in analysis.report.metadata.dates:
                if d!=expected_date:
                    patches.append(Patch(PatchKind.DATE,"metadata",d,expected_date,"blue",""))
        return patches
