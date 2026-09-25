from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .gip_adapter import analyze_uploaded_calculations

app = FastAPI(title="GIP API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "gip-api", "stage": "foundation"}

@app.get("/api/v1/capabilities")
def capabilities():
    return {"report_qa": True, "calculations": True, "graphics": True, "document_patch": False}

@app.post("/api/v1/calculations/analyze")
async def calculations_analyze(files: list[UploadFile] = File(...), expected_address: str | None = Form(None)):
    if not files:
        raise HTTPException(400, "Не загружены расчётные файлы")
    with TemporaryDirectory() as tmp:
        paths = []
        for upload in files:
            if not upload.filename:
                continue
            path = Path(tmp) / Path(upload.filename).name
            path.write_bytes(await upload.read())
            paths.append(path)
        if not paths:
            raise HTTPException(400, "Не удалось получить имена файлов")
        result = analyze_uploaded_calculations(paths, expected_address)
        return {"findings": [f.__dict__ for f in result.findings], "traces": [t.__dict__ for t in result.traces], "sources": [p.name for p in paths]}
