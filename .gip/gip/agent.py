from .audit import AuditLog
from .session import Session
from .workflow import Stage
class GIPAgent:
    def __init__(self,session_id="local"): self.session=Session(session_id); self.audit=AuditLog()
    def advance(self,stage:Stage):
        current=self.session.workflow.stage; result=self.session.workflow.advance(stage)
        self.audit.record("workflow_transition",from_stage=current.value,to_stage=result.value); return result
