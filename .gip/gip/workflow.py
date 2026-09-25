from enum import Enum

class Stage(str, Enum):
    INTAKE="INTAKE"; PARSE="PARSE"; MODEL="MODEL"; VALIDATE="VALIDATE"
    PLAN="PLAN"; PATCH="PATCH"; VERIFY="VERIFY"; COMPLETE="COMPLETE"

_ALLOWED={
 Stage.INTAKE:{Stage.PARSE}, Stage.PARSE:{Stage.MODEL}, Stage.MODEL:{Stage.VALIDATE},
 Stage.VALIDATE:{Stage.PLAN,Stage.COMPLETE}, Stage.PLAN:{Stage.PATCH},
 Stage.PATCH:{Stage.VERIFY}, Stage.VERIFY:{Stage.COMPLETE,Stage.PLAN}, Stage.COMPLETE:set(),
}
class WorkflowError(RuntimeError): pass
class Workflow:
    def __init__(self): self.stage=Stage.INTAKE
    def advance(self,next_stage:Stage):
        if next_stage not in _ALLOWED[self.stage]: raise WorkflowError(f"Invalid transition: {self.stage} -> {next_stage}")
        self.stage=next_stage; return self.stage
