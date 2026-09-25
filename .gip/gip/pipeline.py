"""Unified deterministic GIP inspection pipeline."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from .agent import GIPAgent
from .docx_engine import DocxEngine
from .docx_patch_engine import DocxPatchEngine
from .docx_verify_engine import DocxVerificationEngine, VerificationFinding
from .patch_plan import PatchPlan
from .patches import Patch
from .table_engine import DocxTableEngine
from .workflow import Stage

@dataclass
class PipelineResult:
    input_path: Path
    output_path: Path
    completed: bool
    findings: list[VerificationFinding] = field(default_factory=list)
    applied_patches: int = 0

class GIPPipeline:
    """Runs the complete deterministic lifecycle around a DOCX report."""
    def __init__(self, agent: GIPAgent | None = None):
        self.agent = agent or GIPAgent()

    def run(self, input_path: str | Path, patches: list[Patch] | tuple[Patch, ...] = (), output_path: str | Path | None = None) -> PipelineResult:
        source=Path(input_path)
        if source.suffix.lower() != ".docx":
            raise ValueError("GIP pipeline currently accepts .docx reports only")
        target=Path(output_path) if output_path else source.with_name(source.stem+"_GIP_checked.docx")
        target.write_bytes(source.read_bytes())
        self.agent.advance(Stage.PARSE)
        DocxEngine().read_text(target)
        DocxTableEngine().read_tables(target)
        self.agent.advance(Stage.MODEL)
        self.agent.advance(Stage.VALIDATE)
        table_findings=DocxTableEngine().validate_categories(target)
        if table_findings:
            return PipelineResult(source,target,False,[VerificationFinding("INVALID_CATEGORY",f"Table {f.table_index}, row {f.row_index}: {f.value}") for f in table_findings])
        plan=PatchPlan(tuple(patches)); plan.validate()
        self.agent.advance(Stage.PLAN)
        applied=0
        patch_engine=DocxPatchEngine()
        verifier=DocxVerificationEngine()
        for patch in plan.patches:
            self.agent.advance(Stage.PATCH)
            patch_engine.apply(target,patch)
            applied += 1
            self.agent.advance(Stage.VERIFY)
            check=verifier.verify_patch(target,patch)
            if not check.passed:
                return PipelineResult(source,target,False,check.findings,applied)
            if applied < plan.count:
                self.agent.advance(Stage.PLAN)
        final=verifier.verify_document(target)
        if not final.passed:
            return PipelineResult(source,target,False,final.findings,applied)
        if self.agent.session.workflow.stage == Stage.VERIFY:
            self.agent.advance(Stage.COMPLETE)
        return PipelineResult(source,target,True,[],applied)
