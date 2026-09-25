from pathlib import Path
import sys
CORE = Path(__file__).resolve().parents[2] / ".gip"
if str(CORE) not in sys.path: sys.path.insert(0, str(CORE))
from gip.docx_patch_engine import DocxPatchEngine
from gip.docx_verify_engine import DocxVerificationEngine

def apply_and_verify(path: Path, patch):
    applied = DocxPatchEngine().apply(path, patch)
    verification = DocxVerificationEngine().verify_patch(path, patch)
    return applied, verification
