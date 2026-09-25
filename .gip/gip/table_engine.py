"""DOCX table extraction and deterministic category validation."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from docx import Document
from .rules import ALLOWED_CATEGORIES

@dataclass(frozen=True)
class TableData:
    index: int
    headers: list[str]
    rows: list[list[str]]

@dataclass(frozen=True)
class CategoryFinding:
    table_index: int
    row_index: int
    value: str

class DocxTableEngine:
    def read_tables(self, path: str | Path) -> list[TableData]:
        p=Path(path)
        if p.suffix.lower() != ".docx":
            raise ValueError("table engine accepts .docx files only")
        doc=Document(p)
        result=[]
        for i, table in enumerate(doc.tables):
            rows=[[cell.text.strip() for cell in row.cells] for row in table.rows]
            result.append(TableData(i, rows[0] if rows else [], rows[1:] if rows else []))
        return result

    def validate_categories(self, path: str | Path) -> list[CategoryFinding]:
        findings=[]
        for table in self.read_tables(path):
            cols=[i for i,h in enumerate(table.headers) if h.lower()=="категория состояния"]
            for ri,row in enumerate(table.rows):
                for col in cols:
                    value=row[col].strip() if col < len(row) else ""
                    if value not in ALLOWED_CATEGORIES:
                        findings.append(CategoryFinding(table.index,ri+1,value))
        return findings
