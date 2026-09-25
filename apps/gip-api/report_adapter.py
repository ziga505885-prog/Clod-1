from pathlib import Path
import sys

CORE = Path(__file__).resolve().parents[2] / ".gip"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from gip.full_inspection import inspect_document

def inspect_uploaded_report(path: Path, expected_contract: str | None = None, expected_address: str | None = None, expected_date: str | None = None):
    return inspect_document(path, expected_contract=expected_contract, expected_address=expected_address, expected_date=expected_date)
