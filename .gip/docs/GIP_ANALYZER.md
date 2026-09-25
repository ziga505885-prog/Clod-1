# GIP Analyzer v0.1

Deterministic extraction layer for DOCX reports.

Extracts contract number candidates, dates, an address candidate, defect-like
paragraphs and raw tables. It deliberately does not infer engineering
severity, causes, condition categories or corrections from a single
occurrence. Canonical values must come from the template/domain layer.

DOCX -> ANALYZE -> CANONICAL VALUES -> PATCH PLAN -> PATCH -> VERIFY
