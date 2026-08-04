import os
import shutil
import tempfile
import zipfile
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile, status

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from appaveli_codemind.core.agent import CodeMindAgent
from appaveli_codemind.core.models import (
    AnalysisResult,
    RefactorType,
    SecuritySeverity,
)
from appaveli_codemind.web_api.auth import get_api_key_manager
from appaveli_codemind.web_api.middleware import APIKeyMiddleware

# Load environment variables
load_dotenv()

# Get admin key from environment
# For testing/CI, use a default key. For production, MUST set CODEMIND_ADMIN_KEY
DEFAULT_TEST_ADMIN_KEY = "test_admin_key_insecure_do_not_use_in_production"
ADMIN_KEY = os.getenv("CODEMIND_ADMIN_KEY") or DEFAULT_TEST_ADMIN_KEY

# Warn if using default key (not in production)
if ADMIN_KEY == DEFAULT_TEST_ADMIN_KEY:
    import warnings
    warnings.warn(
        "Using default admin key! Set CODEMIND_ADMIN_KEY environment variable for production.",
        stacklevel=2
    )

# Get allowed CORS origins from environment
# Default to localhost for development
DEFAULT_ORIGINS = "http://localhost:3000,http://localhost:8000"
allowed_origins = os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",")
# Strip whitespace from each origin
allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

app = FastAPI(
    title="Appaveli CodeMind API",
    version="1.2.0",
    description=(
        "Web API for Appaveli CodeMind – analysis, refactoring, security.\n\n"
        "## Authentication\n"
        "All endpoints (except /health) require API key authentication.\n"
        "Include your API key in the `X-API-Key` header.\n\n"
        "Example:\n"
        "```\n"
        "curl -H 'X-API-Key: your_api_key_here' https://api.example.com/analyze/upload\n"
        "```\n"
    ),
)

# Add API key authentication middleware
app.add_middleware(APIKeyMiddleware)

# CORS configuration - origins are loaded from ALLOWED_ORIGINS env variable
# Defaults to localhost for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Lazy agent initialization (only create when needed, not at import time)
# This allows tests to run without requiring API keys
_agent: Optional[CodeMindAgent] = None


def get_agent() -> CodeMindAgent:
    """Get or create the CodeMind agent instance"""
    global _agent
    if _agent is None:
        _agent = CodeMindAgent()
    return _agent


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


class APIKeyCreateRequest(BaseModel):
    name: str
    rate_limit: int = 100


class APIKeyCreateResponse(BaseModel):
    api_key: str
    key_id: str
    name: str
    rate_limit: int
    message: str


class APIKeyListResponse(BaseModel):
    keys: List[Dict]


@app.get("/health")
def health():
    """Health check endpoint - no authentication required."""
    return {"status": "ok", "service": "appaveli-codemind", "version": "1.2.0"}


@app.post("/api-keys/create", response_model=APIKeyCreateResponse)
def create_api_key(
    request: APIKeyCreateRequest,
    x_admin_key: str = Header(..., alias="X-Admin-Key"),
):
    """
    Create a new API key (admin only).

    Requires X-Admin-Key header with admin credentials.
    The generated API key is only shown once - store it securely.
    """
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin key",
        )

    manager = get_api_key_manager()
    api_key = manager.generate_api_key(
        name=request.name,
        rate_limit=request.rate_limit,
    )

    # Extract key_id from the generated key for response
    import hashlib
    key_id = hashlib.sha256(api_key.encode()).hexdigest()[:16]

    return APIKeyCreateResponse(
        api_key=api_key,
        key_id=key_id,
        name=request.name,
        rate_limit=request.rate_limit,
        message="API key created successfully. Store it securely - it won't be shown again.",
    )


@app.get("/api-keys/list", response_model=APIKeyListResponse)
def list_api_keys(
    x_admin_key: str = Header(..., alias="X-Admin-Key"),
):
    """
    List all API keys (admin only).

    Requires X-Admin-Key header with admin credentials.
    Does not return the actual API keys, only metadata.
    """
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin key",
        )

    manager = get_api_key_manager()
    keys = manager.list_keys()

    return APIKeyListResponse(keys=keys)


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
        result: AnalysisResult = get_agent().analyze_file(tmp_path)

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
        result = get_agent().refactor_file(tmp_path, rt_enum)
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
        scan_result = get_agent().scan_project_security(project_root)

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
