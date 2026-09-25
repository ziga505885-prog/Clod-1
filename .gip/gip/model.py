from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class ConditionCategory(str, Enum):
    EMERGENCY = "аварийное"
    SERVICEABLE = "работоспособное"
    LIMITED = "ограниченно-работоспособное"
    NORMAL = "нормативное"

@dataclass
class ReportMetadata:
    contract_number: Optional[str] = None
    address: Optional[str] = None
    dates: list[str] = field(default_factory=list)

@dataclass
class Defect:
    id: Optional[str]
    structure: str
    description: str
    location: Optional[str] = None
    dimensions: Optional[str] = None
    category: Optional[ConditionCategory] = None
    cause: Optional[str] = None
    recommendation: Optional[str] = None
    source_sections: list[str] = field(default_factory=list)
    source_drawings: list[str] = field(default_factory=list)
    source_photos: list[str] = field(default_factory=list)

@dataclass
class InspectionReport:
    metadata: ReportMetadata = field(default_factory=ReportMetadata)
    structures: list[str] = field(default_factory=list)
    defects: list[Defect] = field(default_factory=list)
    defect_summary: list[Defect] = field(default_factory=list)
    defect_characteristics: list[Defect] = field(default_factory=list)
    drawing_defects: list[Defect] = field(default_factory=list)
    photo_defects: list[Defect] = field(default_factory=list)
    drawings: list[str] = field(default_factory=list)
    photos: list[str] = field(default_factory=list)
    conclusions: list[str] = field(default_factory=list)
