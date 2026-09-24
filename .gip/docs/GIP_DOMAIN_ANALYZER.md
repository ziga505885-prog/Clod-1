# GIP Domain Analyzer v0.1

The domain analyzer is the first engineering-specific consistency layer.

It compares defect identities across:
- the main report text;
- the consolidated defect summary;
- section 4 defect characteristics;
- tables carrying drawing/graphics labels.

Rules:
- explicit defect IDs are matched before text;
- unnumbered/general defects remain unnumbered;
- no new ID, category, cause, severity, or engineering conclusion is invented;
- duplicates and missing cross-references become findings;
- text matching is conservative to reduce false positives.

This layer produces findings. Patch creation remains a separate responsibility.
