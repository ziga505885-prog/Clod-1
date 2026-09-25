from __future__ import annotations
from .patches import Patch, PatchKind

def plan_address_patch(old: str, new: str) -> Patch:
    return Patch(PatchKind.ADDRESS, old=old, new=new, mark="blue", reason="")

def plan_date_patch(old: str, new: str) -> Patch:
    return Patch(PatchKind.DATE, old=old, new=new, mark="blue", reason="")

def plan_normal_patch(old: str, new: str, reason: str = "") -> Patch:
    return Patch(PatchKind.NORMAL, old=old, new=new, mark="green", reason=reason)

def plan_patches(*, address: tuple[str, str] | None = None, date: tuple[str, str] | None = None, normal: list[tuple[str, str, str]] | None = None) -> list[Patch]:
    patches = []
    if address:
        patches.append(plan_address_patch(*address))
    if date:
        patches.append(plan_date_patch(*date))
    for old, new, reason in normal or []:
        patches.append(plan_normal_patch(old, new, reason))
    return patches
