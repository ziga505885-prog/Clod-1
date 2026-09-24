import pytest
from gip.workflow import Workflow,Stage,WorkflowError
def test_happy_path():
    w=Workflow()
    for s in [Stage.PARSE,Stage.MODEL,Stage.VALIDATE,Stage.PLAN,Stage.PATCH,Stage.VERIFY,Stage.COMPLETE]: w.advance(s)
    assert w.stage is Stage.COMPLETE
def test_invalid_transition():
    with pytest.raises(WorkflowError): Workflow().advance(Stage.COMPLETE)
