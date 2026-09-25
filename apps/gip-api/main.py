from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.background import BackgroundTasks
import shutil
import tempfile
from fastapi.middleware.cors import CORSMiddleware
from gip_adapter import analyze_uploaded_calculations
from report_adapter import inspect_uploaded_report
from full_check_service import patch_and_verify_report
from graphics_adapter import inspect_graphics

app = FastAPI(title="GIP API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "gip-api", "stage": "foundation"}

@app.get("/api/v1/capabilities")
def capabilities():
    return {"report_qa": True, "calculations": True, "graphics": True, "document_patch": True, "recheck": True, "reconciliation": True}

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
    graphics_files: list[UploadFile] = File(default=[]),
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

        graphics_result = []
        for upload in graphics_files:
            if upload.filename:
                path = Path(tmp) / Path(upload.filename).name
                path.write_bytes(await upload.read())
                graphics_result.append(inspect_graphics(path).__dict__)

        return {
            "stage": "analysis_only",
            "document_patch": False,
            "reconciliation": {"enabled": True},
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
            "graphics": graphics_result,
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
    tmp = Path(tempfile.mkdtemp(prefix="gip-fixed-"))
    source = tmp / Path(report.filename).name
    source.write_bytes(await report.read())
    try:
        applied, verification, recheck, precheck, postcheck = patch_and_verify_report(
            source, expected_contract, expected_address, expected_date
        )
    except ValueError as exc:
        shutil.rmtree(tmp, ignore_errors=True)
        raise HTTPException(422, str(exc)) from exc

    def cleanup():
        shutil.rmtree(tmp, ignore_errors=True)

    response = FileResponse(
        path=source,
        filename="GIP_CORRECTED_" + Path(report.filename).name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "X-GIP-Stage": "patched-verified-rechecked",
            "X-GIP-Patches": str(len(applied)),
            "X-GIP-Recheck": "passed",
            "X-GIP-NonTarget-Findings": str(len(postcheck.findings) - len(recheck["findings"])),
        },
        background=BackgroundTasks(),
    )
    response.background.add_task(cleanup)
    return response


@app.post("/api/v1/graphics/analyze")
async def graphics_analyze(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(400, "Не загружены графические материалы")
    with TemporaryDirectory() as tmp:
        results = []
        for upload in files:
            if not upload.filename:
                continue
            path = Path(tmp) / Path(upload.filename).name
            path.write_bytes(await upload.read())
            results.append(inspect_graphics(path).__dict__)
        if not results:
            raise HTTPException(400, "Не удалось получить графические файлы")
        return {"materials": results, "policy": "text-extraction-is-not-proof-of-absence-of-defects"}
