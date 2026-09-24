# DOCX Verify Engine

Post-patch verification is deterministic and independent of the LLM.

`verify_patch` checks:
- original text is gone;
- exactly one replacement remains;
- NORMAL replacement is green;
- ADDRESS/DATE replacement is blue;
- ADDRESS/DATE patches contain no explanation.

`verify_document` additionally validates the exact allowed condition-category values in DOCX tables.
