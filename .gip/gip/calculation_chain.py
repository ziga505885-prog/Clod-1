"""Context-aware calculation chain.

The chain is descriptive: it records relationships without changing trusted
source values or declaring a mismatch unless context is explicitly known.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class CalculationChainNode:
    kind: str
    name: str
    value: Optional[float] = None
    unit: Optional[str] = None
    context: Optional[str] = None

@dataclass(frozen=True)
class CalculationChain:
    section: str
    nodes: tuple[CalculationChainNode, ...]

    def find(self, kind: str) -> tuple[CalculationChainNode, ...]:
        return tuple(n for n in self.nodes if n.kind == kind)

def build_chain(
    section: str,
    *,
    soil: str | None = None,
    load_cases: tuple[str, ...] = (),
    model: str | None = None,
    element: str | None = None,
    result: CalculationChainNode | None = None,
    limit: CalculationChainNode | None = None,
    conclusion: str | None = None,
) -> CalculationChain:
    nodes: list[CalculationChainNode] = []
    if soil:
        nodes.append(CalculationChainNode("soil", soil, context=section))
    for case in load_cases:
        nodes.append(CalculationChainNode("load_case", case, context=section))
    if model:
        nodes.append(CalculationChainNode("model", model, context=section))
    if element:
        nodes.append(CalculationChainNode("element", element, context=section))
    if result:
        nodes.append(result)
    if limit:
        nodes.append(limit)
    if conclusion:
        nodes.append(CalculationChainNode("conclusion", conclusion, context=section))
    return CalculationChain(section, tuple(nodes))
