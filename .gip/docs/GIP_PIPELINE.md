# GIP Pipeline v0.1

Unified deterministic DOCX lifecycle:

INTAKE -> PARSE -> MODEL -> VALIDATE -> PLAN -> PATCH -> VERIFY -> COMPLETE

An upstream LLM or skill layer supplies validated Patch objects. The pipeline
copies the source, validates tables, applies patches sequentially, verifies
each patch, validates the final document, and returns PipelineResult.

Current scope:
- DOCX input/output
- table category validation
- deterministic patch application
- post-patch verification
- final completion status

The next domain layer will populate patches from report defects, address/date
checks, drawings, photos and the strict GIP report template.
