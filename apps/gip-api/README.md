# GIP API

Run locally from the repository root:

```bash
python -m pip install -r apps/gip-api/requirements.txt
uvicorn main:app --app-dir apps/gip-api --reload --port 8000
```

Health check:

```
GET /health
```

Main endpoints:

- `POST /api/v1/reports/analyze` — report analysis.
- `POST /api/v1/calculations/analyze` — calculation analysis.
- `POST /api/v1/full-check` — combined analysis.
- `POST /api/v1/full-check-and-fix` — DOCX patch, verification and recheck.

The correction endpoint returns a DOCX only after patch verification and a second full inspection pass succeeds.
