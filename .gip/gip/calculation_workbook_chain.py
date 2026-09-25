"""Build a conservative calculation input chain from the supplied workbooks."""
from __future__ import annotations
from dataclasses import dataclass
from .calculation_workbooks import CalculationWorkbookProfile

@dataclass(frozen=True)
class CalculationInputChain:
    section: str
    azimuth: float | None
    height: float | None
    soil_binding: str | None
    load_cases: tuple[str, ...]

def build_input_chains(profile: CalculationWorkbookProfile) -> list[CalculationInputChain]:
    loads = tuple(str(x.number) for x in profile.load_cases if x.number is not None)
    return [
        CalculationInputChain(
            section=s.section,
            azimuth=s.azimuth,
            height=s.height,
            soil_binding=s.lira_point,
            load_cases=loads,
        )
        for s in profile.sections
    ]
