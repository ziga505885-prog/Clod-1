from pathlib import Path
import sys

CORE = Path(__file__).resolve().parents[2] / ".gip"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from gip.calculation_analysis import analyze_calculations

def analyze_uploaded_calculations(paths: list[Path], expected_address: str | None = None):
    return analyze_calculations(paths, expected_address=expected_address)
