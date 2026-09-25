"""Runtime-neutral interfaces used by GIP."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol

ToolHandler = Callable[[dict[str, Any]], Any]

class AgentRuntime(Protocol):
    def run(self, task: str, context: Mapping[str, Any]) -> dict[str, Any]: ...
    def register_tool(self, name: str, handler: ToolHandler) -> None: ...

@dataclass
class RuntimeContext:
    values: dict[str, Any] = field(default_factory=dict)
    def as_dict(self) -> dict[str, Any]:
        return dict(self.values)
