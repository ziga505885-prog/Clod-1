from dataclasses import dataclass,field
from .workflow import Workflow
@dataclass
class Session:
    id:str; workflow:Workflow=field(default_factory=Workflow); context:dict=field(default_factory=dict); attempts:int=0
    def fail_and_retry(self):
        self.attempts+=1
        if self.attempts>3: raise RuntimeError("Verification retry limit exceeded")
