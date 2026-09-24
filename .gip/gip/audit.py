from dataclasses import dataclass,field
from datetime import datetime,timezone
@dataclass
class AuditEvent:
    action:str; details:dict=field(default_factory=dict); timestamp:str=field(default_factory=lambda:datetime.now(timezone.utc).isoformat())
@dataclass
class AuditLog:
    events:list[AuditEvent]=field(default_factory=list)
    def record(self,action:str,**details): self.events.append(AuditEvent(action,details))
