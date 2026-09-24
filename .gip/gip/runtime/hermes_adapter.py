"""Optional adapter boundary for Hermes Agent."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Mapping
from .interfaces import ToolHandler

@dataclass
class HermesAdapter:
    """Thin integration boundary; no GIP domain logic belongs here."""
    runtime: Any | None = None
    tools: dict[str, ToolHandler] = field(default_factory=dict)

    def register_tool(self, name: str, handler: ToolHandler) -> None:
        if not name or not name.strip():
            raise ValueError("tool name must not be empty")
        self.tools[name] = handler
        if self.runtime is not None:
            registrar = getattr(self.runtime, "register_tool", None)
            if callable(registrar):
                registrar(name, handler)

    def run(self, task: str, context: Mapping[str, Any]) -> dict[str, Any]:
        if self.runtime is None:
            raise RuntimeError("Hermes runtime is not configured")
        runner = getattr(self.runtime, "run", None)
        if not callable(runner):
            raise TypeError("configured Hermes runtime does not expose run(task, context)")
        result = runner(task, dict(context))
        return result if isinstance(result, dict) else {"result": result}

    @classmethod
    def from_runtime(cls, runtime: Any) -> "HermesAdapter":
        if runtime is None:
            raise ValueError("runtime must not be None")
        return cls(runtime=runtime)
