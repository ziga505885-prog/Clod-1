"""Safe deterministic DOCX patching with run-aware replacement.

The engine preserves paragraph order and supports matches spanning multiple
runs. It never patches an ambiguous occurrence.
"""
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
        p = Path(path)
        if p.suffix.lower() != ".docx":
            raise ValueError("patch engine accepts .docx files only")
        doc = Document(p)
        matches = 0
        for paragraph in self._paragraphs(doc):
            matches += self._patch_paragraph(paragraph, patch)
        if matches != 1:
            raise ValueError(f"Expected exactly one editable match, found {matches}")
        doc.save(p)
        return AppliedPatch(patch, matches)

    @staticmethod
    def _paragraphs(doc):
        # Main document body.
        for paragraph in doc.paragraphs:
            yield paragraph
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        yield paragraph
        # Headers/footers are part of the report and are explicitly included
        # in GIP address/date checking. This catches stale hidden title blocks.
        for section in doc.sections:
            for container in (
                section.header, section.first_page_header, section.even_page_header,
                section.footer, section.first_page_footer, section.even_page_footer,
            ):
                for paragraph in container.paragraphs:
                    yield paragraph
                for table in container.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for paragraph in cell.paragraphs:
                                yield paragraph

    def _patch_paragraph(self, paragraph, patch: Patch) -> int:
        runs = paragraph.runs
        if not runs:
            return 0
        full = "".join(run.text for run in runs)
        start = full.find(patch.old)
        if start < 0:
            return 0
        end = start + len(patch.old)
        starts, cursor = [], 0
        for run in runs:
            starts.append((cursor, cursor + len(run.text)))
            cursor += len(run.text)
        touched = [i for i, (a, z) in enumerate(starts) if a < end and z > start]
        if not touched:
            return 0
        first, last = touched[0], touched[-1]
        prefix = full[starts[first][0]:start]
        suffix = full[end:starts[last][1]]
        source = runs[first]
        source.text = prefix + patch.new + suffix
        self._color(source, patch)
        for i in range(first + 1, last + 1):
            runs[i].text = ""
        return 1

    @staticmethod
    def _color(run, patch: Patch) -> None:
        if patch.kind in (PatchKind.ADDRESS, PatchKind.DATE):
            run.font.color.rgb = RGBColor(0, 0, 255)
        else:
            run.font.color.rgb = RGBColor(0, 128, 0)
