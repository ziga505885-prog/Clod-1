from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="GIP API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "gip-api", "stage": "foundation"}

@app.get("/api/v1/capabilities")
def capabilities():
    return {"report_qa": True, "calculations": True, "graphics": True, "document_patch": False}
