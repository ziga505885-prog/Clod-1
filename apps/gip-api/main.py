from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from gip_adapter import analyze_uploaded_calculations
from report_adapter import inspect_uploaded_report
from full_check_service import patch_and_verify_report

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


@app.post("/api/v1/reports/analyze")
async def reports_analyze(file: UploadFile = File(...), expected_contract: str | None = Form(None), expected_address: str | None = Form(None), expected_date: str | None = Form(None)):
    if not file.filename:
        raise HTTPException(400, "Не выбран отчёт")
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / Path(file.filename).name
        path.write_bytes(await file.read())
        result = inspect_uploaded_report(path, expected_contract, expected_address, expected_date)
        return {
            "findings": [f.__dict__ for f in result.findings],
            "contracts": result.analysis.contract_candidates,
            "addresses": result.analysis.address_candidates,
            "dates": result.analysis.date_candidates,
            "defects": len(result.domain.report),
            "summary_defects": len(result.domain.summary),
        }


@app.post("/api/v1/full-check")
async def full_check(
    report: UploadFile = File(...),
    calculation_files: list[UploadFile] = File(default=[]),
    expected_contract: str | None = Form(None),
    expected_address: str | None = Form(None),
    expected_date: str | None = Form(None),
):
    if not report.filename:
        raise HTTPException(400, "Не выбран основной отчёт")
    with TemporaryDirectory() as tmp:
        report_path = Path(tmp) / Path(report.filename).name
        report_path.write_bytes(await report.read())
        report_result = inspect_uploaded_report(report_path, expected_contract, expected_address, expected_date)

        calc_result = None
        calc_paths = []
        for upload in calculation_files:
            if upload.filename:
                path = Path(tmp) / Path(upload.filename).name
                path.write_bytes(await upload.read())
                calc_paths.append(path)
        if calc_paths:
            calc_result = analyze_uploaded_calculations(calc_paths, expected_address)

        return {
            "stage": "analysis_only",
            "document_patch": False,
            "report": {
                "findings": [f.__dict__ for f in report_result.findings],
                "contracts": report_result.analysis.contract_candidates,
                "addresses": report_result.analysis.address_candidates,
                "dates": report_result.analysis.date_candidates,
                "defects": len(report_result.domain.report),
                "summary_defects": len(report_result.domain.summary),
            },
            "calculations": None if calc_result is None else {
                "findings": [f.__dict__ for f in calc_result.findings],
                "traces": [t.__dict__ for t in calc_result.traces],
                "sources": [p.name for p in calc_paths],
            },
        }


@app.post("/api/v1/full-check-and-fix")
async def full_check_and_fix(
    report: UploadFile = File(...),
    expected_contract: str | None = Form(None),
    expected_address: str | None = Form(None),
    expected_date: str | None = Form(None),
):
    if not report.filename or not report.filename.lower().endswith(".docx"):
        raise HTTPException(400, "Для исправления требуется DOCX")
    with TemporaryDirectory() as tmp:
        source = Path(tmp) / Path(report.filename).name
        source.write_bytes(await report.read())
        try:
            applied, verification, final, recheck = patch_and_verify_report(source, expected_contract, expected_address, expected_date)
            if recheck is not None and recheck.findings:
                raise ValueError("Повторная проверка выявила оставшиеся нарушения")
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        return {
            "stage": "patched_and_verified",
            "document_patch": True,
            "source": report.filename,
            "applied_patches": applied,
            "patch_verification": verification,
            "final_verification": {"passed": final.passed, "findings": [f.__dict__ for f in final.findings]},
        }
