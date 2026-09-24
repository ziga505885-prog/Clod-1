# DOCX Patch Engine

The engine applies one validated GIP patch at a time to paragraphs and table cells.

- NORMAL: replacement is marked green.
- ADDRESS: replacement is marked blue and carries no explanation.
- DATE: replacement is marked blue and carries no explanation.
- Every patch must have exactly one editable match.

The engine is deliberately deterministic. The LLM proposes a Patch; this
component decides whether and how that patch can be applied.
