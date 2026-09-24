"""Safe DOCX adapter boundary.

The foundation intentionally keeps document mutation behind this module.
A later implementation can use python-docx while preserving patch semantics.
"""
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DocumentText:
    path: Path
    paragraphs: list[str]

class DocxEngine:
    def read_text(self, path: str | Path) -> DocumentText:
        path = Path(path)
        if path.suffix.lower() != ".docx":
            raise ValueError("DOCX engine accepts .docx files only")
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("Install python-docx to enable DOCX processing") from exc
        doc = Document(path)
        return DocumentText(path, [p.text for p in doc.paragraphs])

    def replace_exact(self, path: str | Path, old: str, new: str) -> None:
        if not old:
            raise ValueError("old text must not be empty")
        path = Path(path)
        if path.suffix.lower() != ".docx":
            raise ValueError("DOCX engine accepts .docx files only")
        from docx import Document
        doc = Document(path)
        hits = 0
        for paragraph in doc.paragraphs:
            if old in paragraph.text:
                for run in paragraph.runs:
                    if old in run.text:
                        run.text = run.text.replace(old, new)
                        hits += 1
        if hits != 1:
            raise ValueError(f"Expected exactly one editable run match, found {hits}")
        doc.save(path)
