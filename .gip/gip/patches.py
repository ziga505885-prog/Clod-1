from enum import Enum

class PatchKind(str, Enum):
    NORMAL = "normal"
    ADDRESS = "address"
    DATE = "date"

class Patch:
    __slots__ = ("kind","location","old","new","mark","reason")

    def __init__(self, kind, *args, **kwargs):
        self.kind = kind
        if kwargs:
            self.location = kwargs.get("location", "")
            self.old = kwargs.get("old", "")
            self.new = kwargs.get("new", "")
            self.mark = kwargs.get("mark", "")
            self.reason = kwargs.get("reason", "")
            return
        if len(args) == 3:
            # Current compact form: kind, old, new, mark.
            self.location = ""
            self.old, self.new, self.mark = args
            self.reason = ""
        elif len(args) == 5:
            # Legacy form: kind, location, old, new, mark, reason.
            self.location, self.old, self.new, self.mark, self.reason = args
        else:
            raise TypeError("Patch expects (kind, old, new, mark) or (kind, location, old, new, mark, reason)")

    def __repr__(self):
        return f"Patch(kind={self.kind!r}, location={self.location!r}, old={self.old!r}, new={self.new!r}, mark={self.mark!r}, reason={self.reason!r})"

def validate_patch(p: Patch):
    if p.kind is PatchKind.NORMAL and p.mark not in {"red-green", "green"}:
        raise ValueError("Normal patches require RED/GREEN marking")
    if p.kind in {PatchKind.ADDRESS, PatchKind.DATE} and p.mark != "blue":
        raise ValueError("Address/date patches must use blue marking")
    if p.kind in {PatchKind.ADDRESS, PatchKind.DATE} and p.reason:
        raise ValueError("Address/date patches must not carry explanatory text")
