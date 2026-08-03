import os
import shutil
import tempfile
import zipfile
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from appaveli_codemind.core.agent import CodeMindAgent
from appaveli_codemind.core.models import (
    AnalysisResult,
    RefactorType,
    SecuritySeverity,
)

app = FastAPI(
    title="Appaveli CodeMind API",
    version="1.0.0",
    description="Web API for Appaveli CodeMind – analysis, refactoring, security.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = CodeMindAgent()


class SecurityIssueOut(BaseModel):
    type: str
    severity: str
    line: int
    column: Optional[int] = None
    description: str
    fix_suggestion: str
    file_path: Optional[str] = None


class AnalysisResponse(BaseModel):
    file_path: str
    language: str
    line_count: int
    summary: Optional[str] = None
    security_issues: List[SecurityIssueOut]


class RefactorResponse(BaseModel):
    file_path: str
    language: str
    refactor_type: str
    original_line_count: int
    refactored_line_count: int
    cost_estimate: float
    refactored_code: str


class SecurityScanResponse(BaseModel):
    project_root: str
    total_issues: int
    high_or_critical: int
    summary: Dict[str, int]
    recommendations: List[str]
    issues: List[SecurityIssueOut]


@app.get("/health")
def health():
    return {"status": "ok", "service": "appaveli-codemind", "version": "1.0.0"}


@app.post("/analyze/upload", response_model=AnalysisResponse)
async def analyze_upload(
    file: UploadFile = File(...),
    summary_only: bool = Form(False),
):
    """
    Analyze an uploaded code file for security + summary.
    Accepts: multipart/form-data with 'file' and optional 'summary_only'.
    """
    suffix = os.path.splitext(file.filename or "")[1]
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        shutil.copyfileobj(file.file, tmp)

    try:
        result: AnalysisResult = agent.analyze_file(tmp_path)

        issues_out: List[SecurityIssueOut] = []
        for issue in result.security_issues:
            sev = (
                issue.severity.value
                if isinstance(issue.severity, SecuritySeverity)
                else str(issue.severity)
            )
            issues_out.append(
                SecurityIssueOut(
                    type=issue.type,
                    severity=sev,
                    line=issue.line,
                    column=issue.column,
                    description=issue.description,
                    fix_suggestion=issue.fix_suggestion,
                    file_path=issue.file_path,
                )
            )

        return AnalysisResponse(
            file_path=file.filename or tmp_path,
            language=result.language.value,
            line_count=result.line_count,
            summary=None if summary_only else result.summary,
            security_issues=issues_out,
        )
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


@app.post("/refactor/upload", response_model=RefactorResponse)
async def refactor_upload(
    file: UploadFile = File(...),
    refactor_type: str = Form("general_cleanup"),
):
    """
    Refactor an uploaded code file using CodeMind.
    Accepts: multipart/form-data with 'file' and 'refactor_type'.
    """
    suffix = os.path.splitext(file.filename or "")[1]
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        shutil.copyfileobj(file.file, tmp)

    try:
        rt_enum = RefactorType(refactor_type)
    except ValueError:
        # Fallback to GENERAL_CLEANUP if something unexpected comes in
        rt_enum = RefactorType.GENERAL_CLEANUP

    try:
        result = agent.refactor_file(tmp_path, rt_enum)
    finally:
        # we may still want to keep the temp file around if we later diff; for now, clean
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    original_lines = len(result.original_code.splitlines())
    refactored_lines = len(result.refactored_code.splitlines())

    return RefactorResponse(
        file_path=file.filename or "(uploaded file)",
        language=result.language.value,
        refactor_type=result.refactor_type.value,
        original_line_count=original_lines,
        refactored_line_count=refactored_lines,
        cost_estimate=result.cost_estimate,
        refactored_code=result.refactored_code,
    )


@app.post("/security/upload", response_model=SecurityScanResponse)
async def security_upload(
    file: UploadFile = File(...),
):
    """
    Run a security scan on:
      - a single code file, or
      - a ZIP archive of a project.

    If a ZIP is uploaded, it is extracted and the entire project is scanned.
    If a single file is uploaded, it is placed in a temp dir and that dir is scanned.
    """
    # Create a temp root directory for this scan
    temp_root = tempfile.mkdtemp(prefix="codemind-sec-")
    original_name = file.filename or "upload"

    try:
        uploaded_path = os.path.join(temp_root, original_name)

        # Save uploaded file
        with open(uploaded_path, "wb") as out:
            shutil.copyfileobj(file.file, out)

        project_root = temp_root

        # If ZIP, extract to a subfolder and scan that
        if original_name.lower().endswith(".zip"):
            extract_dir = os.path.join(temp_root, "unzipped")
            os.makedirs(extract_dir, exist_ok=True)

            with zipfile.ZipFile(uploaded_path, "r") as z:
                z.extractall(extract_dir)

            project_root = extract_dir

        # Run CodeMind's project security scan
        scan_result = agent.scan_project_security(project_root)

        issues_out: List[SecurityIssueOut] = []
        for issue in scan_result.code_issues:
            sev = (
                issue.severity.value
                if isinstance(issue.severity, SecuritySeverity)
                else str(issue.severity)
            )
            issues_out.append(
                SecurityIssueOut(
                    type=issue.type,
                    severity=sev,
                    line=issue.line,
                    column=issue.column,
                    description=issue.description,
                    fix_suggestion=issue.fix_suggestion,
                    file_path=issue.file_path,
                )
            )

        total_issues = len(scan_result.code_issues)
        high_or_critical = scan_result.summary.get("high_severity_issues", 0)

        return SecurityScanResponse(
            project_root=original_name,
            total_issues=total_issues,
            high_or_critical=high_or_critical,
            summary=scan_result.summary,
            recommendations=scan_result.recommendations,
            issues=issues_out,
        )

    finally:
        # Clean up entire temp directory (uploaded file & unzipped project)
        shutil.rmtree(temp_root, ignore_errors=True)
