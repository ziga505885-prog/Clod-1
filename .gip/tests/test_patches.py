import pytest
from gip.patches import Patch,PatchKind,validate_patch
def test_address_is_blue_and_no_reason(): validate_patch(Patch(PatchKind.ADDRESS,"heading","old","new","blue",""))
def test_address_cannot_have_explanation():
    with pytest.raises(ValueError): validate_patch(Patch(PatchKind.ADDRESS,"heading","old","new","blue","why"))
