from __future__ import annotations
from pathlib import Path
from zipfile import ZipFile
import re

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

class StreamingDocxVerifier:
    def _parts(self, path: Path):
        with ZipFile(path, "r") as z:
            for name in z.namelist():
                if name.startswith("word/") and name.endswith(".xml"):
                    yield name, z.read(name).decode("utf-8", "ignore")

    def count_text(self, path: str | Path, text: str) -> int:
        if not text:
            return 0
        return sum(part.count(text) for _, part in self._parts(Path(path)))

    def color_present(self, path: str | Path, text: str, color: str) -> bool:
        if not text:
            return False
        wanted = f'<w:color w:val="{color}"'
        for _, xml in self._parts(Path(path)):
            for match in re.finditer(re.escape(text), xml):
                left = max(0, match.start() - 1200)
                right = min(len(xml), match.end() + 1200)
                if wanted in xml[left:right]:
                    return True
        return False

    def verify(self, path: str | Path, patch) -> tuple[bool, list[str]]:
        errors = []
        old_count = self.count_text(path, patch.old)
        new_count = self.count_text(path, patch.new)

        if patch.mark == "red-green":
            if old_count != 1:
                errors.append("RED_OLD_TEXT_COUNT_IS_NOT_ONE")
            if new_count != 1:
                errors.append("GREEN_NEW_TEXT_COUNT_IS_NOT_ONE")
            if not self.color_present(path, patch.old, "FF0000"):
                errors.append("RED_OLD_TEXT_NOT_MARKED")
            if not self.color_present(path, patch.new, "008000"):
                errors.append("GREEN_NEW_TEXT_NOT_MARKED")
            return not errors, errors

        if old_count:
            errors.append("OLD_TEXT_STILL_PRESENT")
        if new_count != 1:
            errors.append("NEW_TEXT_COUNT_IS_NOT_ONE")
        expected = "0000FF" if patch.mark == "blue" else "008000"
        if not self.color_present(path, patch.new, expected):
            errors.append("EXPECTED_COLOR_NOT_FOUND")
        return not errors, errors
