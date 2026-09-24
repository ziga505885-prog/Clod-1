from dataclasses import dataclass
from .patches import Patch, validate_patch

@dataclass(frozen=True)
class PatchPlan:
    patches: tuple[Patch, ...]

    def validate(self) -> None:
        for patch in self.patches:
            validate_patch(patch)

    @property
    def count(self) -> int:
        return len(self.patches)
