"""Deterministic DOCX patch engine with GIP color semantics."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from docx import Document
from docx.shared import RGBColor
from .patches import Patch, PatchKind, validate_patch

@dataclass(frozen=True)
class AppliedPatch:
    patch: Patch
    matches: int

class DocxPatchEngine:
    def apply(self, path: str | Path, patch: Patch) -> AppliedPatch:
        validate_patch(patch)
        p=Path(path)
        if p.suffix.lower() != ".docx":
            raise ValueError("patch engine accepts .docx files only")
        doc=Document(p)
        hits=0
        for paragraph in doc.paragraphs:
            hits += self._paragraph(paragraph, patch)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        hits += self._paragraph(paragraph, patch)
        if hits != 1:
            raise ValueError(f"Expected exactly one editable match, found {hits}")
        doc.save(p)
        return AppliedPatch(patch, hits)

    def _paragraph(self, paragraph, patch: Patch) -> int:
        for run in paragraph.runs:
            if patch.old in run.text:
                before, after = run.text.split(patch.old, 1)
                run.text = before
                replacement=paragraph.add_run(patch.new)
                self._color(replacement, patch)
                tail=paragraph.add_run(after)
                self._copy_basic_format(run, replacement)
                self._copy_basic_format(run, tail)
                return 1
        return 0

    @staticmethod
    def _color(run, patch: Patch) -> None:
        if patch.kind in (PatchKind.ADDRESS, PatchKind.DATE):
            run.font.color.rgb=RGBColor(0,0,255)
        else:
            run.font.color.rgb=RGBColor(0,128,0)

    @staticmethod
    def _copy_basic_format(source, target) -> None:
        target.bold=source.bold
        target.italic=source.italic
        target.underline=source.underline
        target.font.name=source.font.name
        target.font.size=source.font.size
