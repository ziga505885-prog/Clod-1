# Hermes integration

GIP treats Hermes Agent as an optional runtime, not as the source of engineering rules.

- Hermes: agent loop, provider/model routing, runtime tool execution and session concerns.
- GIP: inspection-report model, engineering QA rules, defect cross-checks, patch semantics, document mutation and post-patch verification.

The adapter accepts an already-created runtime object, keeping provider credentials and Hermes configuration outside GIP.

Planned GIP-owned tools:
gip_read_docx, gip_read_pdf, gip_extract_tables, gip_extract_drawings, gip_extract_photos,
gip_find_defects, gip_compare_defects, gip_check_address, gip_check_dates, gip_check_contract,
gip_check_categories, gip_apply_patch, gip_verify_document.
