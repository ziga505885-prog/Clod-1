"""Reference-profile rules for trusted calculation sets.

A trusted calculation set is training/reference material for GIP. It is not
treated as a document to correct. Its values and methodology are preserved as
source evidence and used to learn the structure of valid calculation outputs.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

@dataclass(frozen=True)
class CalculationReference:
    name: str
    files: tuple[str, ...]
    trusted: bool = True
    role: str = "reference"
    notes: tuple[str, ...] = ()

    def contains(self, path: str | Path) -> bool:
        p = str(Path(path))
        return any(p == str(Path(x)) or Path(p).name == Path(x).name for x in self.files)

    def policy(self) -> tuple[str, ...]:
        return (
            "preserve_source_values",
            "do_not_auto_correct_calculation",
            "do_not_flag_numeric_difference_without_context",
            "resolve_section_model_units_combination_before_comparison",
            "treat_source_methodology_as_reference_evidence",
        )

def make_reference(name: str, files: Iterable[str | Path], *, notes: Iterable[str] = ()) -> CalculationReference:
    return CalculationReference(
        name=name,
        files=tuple(str(Path(x)) for x in files),
        notes=tuple(notes),
    )
