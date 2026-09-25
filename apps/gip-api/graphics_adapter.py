from pathlib import Path
from dataclasses import dataclass

@dataclass(frozen=True)
class GraphicsMaterial:
    filename: str
    pages: int | None
    text_chars: int
    text_layer_available: bool
    status: str
    note: str

def inspect_graphics(path: Path) -> GraphicsMaterial:
    suffix = path.suffix.lower()
    if suffix != ".pdf":
        return GraphicsMaterial(path.name, None, 0, False, "UNSUPPORTED", "Автоматический анализ графического материала поддерживает PDF.")
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        text = "".join((page.extract_text() or "") for page in reader.pages)
        chars = len(text.strip())
        if chars == 0:
            return GraphicsMaterial(path.name, len(reader.pages), 0, False, "VISUAL_REVIEW_REQUIRED", "Текстовый слой отсутствует; отсутствие дефектов по тексту не определяется.")
        return GraphicsMaterial(path.name, len(reader.pages), chars, True, "TEXT_LAYER_AVAILABLE", "Текстовый слой доступен для последующего сопоставления обозначений.")
    except Exception as exc:
        return GraphicsMaterial(path.name, None, 0, False, "READ_ERROR", f"Не удалось безопасно извлечь текст: {type(exc).__name__}")
