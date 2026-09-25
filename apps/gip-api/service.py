from pathlib import Path
from .gip_adapter import analyze_uploaded_calculations

UPLOAD_ROOT = Path("data/uploads")
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

def analyze_paths(paths: list[str], expected_address: str | None = None):
    return analyze_uploaded_calculations([Path(p) for p in paths], expected_address)
