# DOCX Patch Engine v0.2

Fixes v0.1 correctness issues:
- replacement stays at its original paragraph position;
- text spanning multiple Word runs can be replaced;
- verification uses Patch.reason;
- replacement verification counts exact occurrences.

Ambiguous matches are still rejected.
