import os
import json
import time
import uuid
import logging
from collections import defaultdict
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import STATIC_DIR, DATA_DIR, SERPAPI_API_KEY, SUPPORTED_LANGUAGES, OFFICIAL_GOV_DOMAINS
import config
import hashlib
from database import (
    init_db, save_case, get_case, list_cases, delete_case, get_stats,
    authenticate_operator, get_operator_by_id, generate_otp, verify_otp,
    save_operator_session, get_operator_session, delete_operator_session
)
from services.serp_service import search_government_sources, generate_gov_search_query
from services.extractor_service import extract_structured_facts, generate_claim_source_mappings
from services.template_service import generate_bilingual_application, TEMPLATES_META
from services.pdf_service import generate_printable_html
from services.validator_service import validate_bilingual_document
from services.sms_service import validate_mobile, mask_mobile, is_sms_configured, get_configured_provider_name, send_sms_otp

# Set up clean logging without sensitive personal data
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("awaaz_adhikar")

# Initialize DB on load
init_db()

# In-memory sessions: token -> { "operator": op, "expires_at": float, "created_at": float }
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}
SESSION_TTL_SECONDS = 86400  # 24 hours

# Rate limiting store: "ip:endpoint" -> list of timestamps
RATE_LIMIT_STORE: Dict[str, List[float]] = defaultdict(list)

# Recordings directory (Private, NOT served as open public static files)
RECORDINGS_DIR = DATA_DIR / "recordings"
RECORDINGS_DIR.mkdir(exist_ok=True)

# Initialize FastAPI application
app = FastAPI(
    title="Awaaz Adhikar API",
    description="Civic Grievance Documentation & Verification Workspace",
    version="1.0.0"
)

# CORS configuration - safe for deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount public static assets (HTML, CSS, JS, fonts only - NO recordings)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Security Headers Middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "microphone=(self), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://fonts.googleapis.com https://fonts.gstatic.com data: blob:; "
        "img-src 'self' data: https: blob:; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "media-src 'self' blob:; "
        "connect-src 'self' https:;"
    )
    return response

# Security Helpers
def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def check_rate_limit(request: Request, endpoint: str, max_requests: int, window_seconds: int = 60):
    client_ip = get_client_ip(request)
    now = time.time()
    key = f"{client_ip}:{endpoint}"
    # Prune old timestamps
    RATE_LIMIT_STORE[key] = [t for t in RATE_LIMIT_STORE[key] if now - t < window_seconds]
    if len(RATE_LIMIT_STORE[key]) >= max_requests:
        logger.warning(f"Rate limit exceeded for {endpoint} by IP {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait a moment before trying again."
        )
    RATE_LIMIT_STORE[key].append(now)

def get_authenticated_operator(request: Request) -> Optional[Dict[str, Any]]:
    token = ""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    if not token or token in ("undefined", "null"):
        token = request.cookies.get("awaaz_session", "").strip()
    if not token or token in ("undefined", "null"):
        token = request.query_params.get("token", "").strip()
        
    if not token or token in ("undefined", "null"):
        return None

    # 1. Check in-memory session cache
    if token in ACTIVE_SESSIONS:
        session = ACTIVE_SESSIONS[token]
        if time.time() < session.get("expires_at", 0):
            return session.get("operator")
        else:
            del ACTIVE_SESSIONS[token]
            delete_operator_session(token)
            return None

    # 2. Check persistent database storage
    db_session = get_operator_session(token)
    if db_session:
        ACTIVE_SESSIONS[token] = db_session
        return db_session.get("operator")

    return None

def require_operator(request: Request) -> Dict[str, Any]:
    op = get_authenticated_operator(request)
    if not op:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Valid operator authentication session required."
        )
    return op

# Request Validation Models
class LoginRequest(BaseModel):
    email: str = Field(..., max_length=150)
    password: str = Field(..., max_length=100)

class ExtractRequest(BaseModel):
    transcript: str = Field(..., min_length=1, max_length=10000)
    language: Optional[str] = Field("hi", max_length=10)

class SearchRequest(BaseModel):
    query: Optional[str] = Field("", max_length=300)
    extracted_fields: Optional[Dict[str, Any]] = None

class VerifySourceRequest(BaseModel):
    case_id: str = Field(..., max_length=60)
    source_id: str = Field(..., max_length=60)
    verified: bool

class GenerateDocRequest(BaseModel):
    case_data: Dict[str, Any]

class UpdateConfigKeyRequest(BaseModel):
    serpapi_key: str = Field(..., max_length=200)

# ========================================================
# AUTHENTICATION ROUTES
# ========================================================

@app.post("/api/auth/login")
async def login(req: LoginRequest, request: Request, response: Response):
    check_rate_limit(request, "login", max_requests=10, window_seconds=60)
    op = authenticate_operator(req.email, req.password)
    if not op:
        raise HTTPException(
            status_code=401,
            detail="Invalid operator email or password. Use demo login or check credentials."
        )
    token = f"tok_{uuid.uuid4().hex}"
    expires_at = time.time() + SESSION_TTL_SECONDS
    ACTIVE_SESSIONS[token] = {
        "operator": op,
        "expires_at": expires_at,
        "created_at": time.time()
    }
    save_operator_session(token, op["id"], expires_at)
    response.set_cookie(
        key="awaaz_session",
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )
    logger.info(f"Operator logged in: {op.get('id')} ({op.get('name')})")
    return {"success": True, "token": token, "operator": op}

@app.post("/api/auth/demo-login")
async def demo_login(request: Request, response: Response):
    check_rate_limit(request, "demo_login", max_requests=12, window_seconds=60)
    demo_op = authenticate_operator("operator@awaazadhikar.gov.in", "demo123")
    if not demo_op:
        init_db()
        demo_op = authenticate_operator("operator@awaazadhikar.gov.in", "demo123")
    token = f"tok_demo_{uuid.uuid4().hex[:12]}"
    expires_at = time.time() + SESSION_TTL_SECONDS
    ACTIVE_SESSIONS[token] = {
        "operator": demo_op,
        "expires_at": expires_at,
        "created_at": time.time()
    }
    save_operator_session(token, demo_op["id"], expires_at)
    response.set_cookie(
        key="awaaz_session",
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )
    logger.info("Demo operator login granted for evaluation.")
    return {"success": True, "token": token, "operator": demo_op}

@app.get("/api/auth/me")
async def get_current_user(request: Request):
    op = get_authenticated_operator(request)
    if op:
        return {"authenticated": True, "operator": op}
    return {"authenticated": False, "operator": None}

@app.post("/api/auth/logout")
async def logout(request: Request, response: Response):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    if not token or token in ("undefined", "null"):
        token = request.cookies.get("awaaz_session", "").strip()
    if not token or token in ("undefined", "null"):
        token = request.query_params.get("token", "").strip()
    if token and token in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[token]
    if token:
        delete_operator_session(token)
    response.delete_cookie(key="awaaz_session", path="/")
    return {"success": True, "message": "Successfully logged out"}

# ========================================================
# CORE PUBLIC & DOCUMENT ROUTES
# ========================================================

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found")
    return index_file.read_text(encoding="utf-8")

@app.get("/document/{case_id}", response_class=HTMLResponse)
async def serve_printable_document(case_id: str, request: Request):
    op = require_operator(request)
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # Authorization check: only case owner or demo operator
    if (case.get("operator_id") != op["id"] and 
        case.get("operator_id") not in ["OP-4102", "CSC-OP-01"] and 
        op["id"] != "OP-4102"):
        raise HTTPException(status_code=403, detail="Forbidden: You are not authorized to view this document.")
        
    doc_data = case.get("generated_documents")
    if not doc_data:
        doc_data = generate_bilingual_application(case)
    return generate_printable_html(doc_data, case)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": "Awaaz Adhikar Workspace",
        "serpapi_configured": bool(config.SERPAPI_API_KEY),
        "sms_configured": is_sms_configured(),
        "sms_provider": get_configured_provider_name(),
        "supported_languages": len(SUPPORTED_LANGUAGES)
    }

@app.get("/api/stats")
async def fetch_stats(request: Request):
    op = require_operator(request)
    return get_stats(operator_id=op["id"])

@app.get("/api/languages")
async def fetch_languages():
    return SUPPORTED_LANGUAGES

@app.get("/api/templates")
async def fetch_templates():
    return TEMPLATES_META

@app.get("/api/samples")
async def fetch_samples():
    samples_file = STATIC_DIR / "samples.json"
    if samples_file.exists():
        return json.loads(samples_file.read_text(encoding="utf-8"))
    return []

@app.get("/api/locations")
async def fetch_locations():
    loc_file = DATA_DIR / "india-administrative-divisions.json"
    if loc_file.exists():
        return json.loads(loc_file.read_text(encoding="utf-8"))
    return {}

# ========================================================
# PROTECTED CASE MANAGEMENT ROUTES
# ========================================================

@app.get("/api/cases")
async def fetch_cases(request: Request):
    op = require_operator(request)
    return list_cases(operator_id=op["id"])

@app.post("/api/cases")
async def create_or_update_case(case_data: Dict[str, Any], request: Request):
    op = require_operator(request)
    mobile_raw = case_data.pop('citizen_mobile', '')
    if mobile_raw:
        is_val, mobile_digits = validate_mobile(mobile_raw)
        if is_val:
            case_data['citizen_mobile_hash'] = hashlib.sha256(mobile_digits.encode()).hexdigest()
            case_data['citizen_mobile_masked'] = mask_mobile(mobile_digits)
    if 'center_name' not in case_data or not case_data.get('center_name'):
        case_data['center_name'] = op.get('center_id', 'CSC Center')
    try:
        saved = save_case(case_data, operator_id=op['id'])
        return saved
    except PermissionError:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot modify another operator's case.")

@app.get("/api/cases/{case_id}")
async def fetch_single_case(case_id: str, request: Request):
    op = require_operator(request)
    c = get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
    if (c.get("operator_id") != op["id"] and 
        c.get("operator_id") not in ["OP-4102", "CSC-OP-01"] and 
        op["id"] != "OP-4102"):
        raise HTTPException(status_code=403, detail="Forbidden: You cannot access this case.")
    return c

@app.delete("/api/cases/{case_id}")
async def remove_case(case_id: str, request: Request):
    op = require_operator(request)
    try:
        success = delete_case(case_id, operator_id=op["id"])
        if not success:
            raise HTTPException(status_code=404, detail="Case not found")
        return {"success": True, "message": "Case deleted securely from workspace"}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Forbidden: You cannot delete another operator's case.")

# ========================================================
# AI EXTRACTION & VERIFICATION SERVICES
# ========================================================

@app.post("/api/extract")
async def extract_facts(req: ExtractRequest, request: Request):
    check_rate_limit(request, "extract", max_requests=30, window_seconds=60)
    if not req.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript is empty")
    result = extract_structured_facts(req.transcript, req.language)
    return result

@app.post("/api/search-sources")
async def search_sources(req: SearchRequest, request: Request):
    check_rate_limit(request, "search_sources", max_requests=25, window_seconds=60)
    result = search_government_sources(req.query, req.extracted_fields)
    return result

@app.post("/api/mappings")
async def create_mappings(payload: Dict[str, Any]):
    extracted_fields = payload.get("extracted_fields", {})
    sources = payload.get("sources", [])
    mappings = generate_claim_source_mappings(extracted_fields, sources)
    return mappings

@app.post("/api/generate-document")
async def generate_document(req: GenerateDocRequest, request: Request):
    op = require_operator(request)
    case_data = req.case_data
    doc_result = generate_bilingual_application(case_data)
    # Run validator
    extracted = case_data.get('extracted_fields', {})
    is_valid, validation_errors = validate_bilingual_document(doc_result, extracted)
    doc_result['validation'] = {'valid': is_valid, 'errors': validation_errors}
    if is_valid:
        case_data['generated_documents'] = doc_result
        case_data['verification_status'] = 'Operator Verified'
        save_case(case_data, operator_id=op['id'])
    return doc_result

@app.post("/api/update-config")
async def update_serpapi_key(req: UpdateConfigKeyRequest, request: Request):
    require_operator(request)
    key = req.serpapi_key.strip()
    config.SERPAPI_API_KEY = key
    os.environ["SERPAPI_API_KEY"] = key
    return {"success": True, "message": "SerpApi Key updated successfully", "active": bool(key)}

# ========================================================
# SECURE AUDIO HANDLING (AUTHENTICATED ONLY, NO PUBLIC STATIC)
# ========================================================

@app.post("/api/upload-audio")
async def upload_audio(
    request: Request,
    file: UploadFile = File(...),
    case_id: Optional[str] = Form("TEMP"),
    language: Optional[str] = Form("hi")
):
    require_operator(request)
    check_rate_limit(request, "upload_audio", max_requests=15, window_seconds=60)
    
    # MIME validation
    allowed_mimes = ["audio/webm", "audio/wav", "audio/ogg", "audio/mp3", "audio/mpeg", "audio/mp4", "audio/x-m4a"]
    if file.content_type and file.content_type not in allowed_mimes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Only audio recordings are permitted."
        )

    contents = await file.read()
    # Size limit (10MB)
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Audio file exceeds 10MB limit.")

    clean_id = "".join(c for c in (case_id or "CASE") if c.isalnum() or c in "-_")[:20].upper() or "CASE"
    
    # Preserve original extension
    orig_ext = os.path.splitext(file.filename or "")[1].lower()
    if orig_ext in [".wav", ".webm", ".ogg", ".mp3", ".mp4", ".m4a"]:
        ext = orig_ext
    else:
        ext = ".wav" if "wav" in (file.content_type or "") else ".webm"

    unique_name = f"{clean_id}_{uuid.uuid4().hex[:12]}{ext}"
    file_path = RECORDINGS_DIR / unique_name
    file_path.write_bytes(contents)

    # Perform Speech-to-Text transcription on the audio file
    transcript = ""
    try:
        from services.stt_service import transcribe_audio_file
        transcript = transcribe_audio_file(file_path, language=language or "hi")
    except Exception as e:
        print(f"[Upload Audio STT Warning]: {e}")

    return {
        "success": True,
        "filename": unique_name,
        "url": f"/api/audio/{unique_name}",
        "size": len(contents),
        "transcript": transcript or ""
    }

@app.get("/api/audio/{filename}")
async def get_audio_recording(filename: str, request: Request):
    require_operator(request)
    safe_name = os.path.basename(filename)
    file_path = RECORDINGS_DIR / safe_name
    if not file_path.exists() or not safe_name.endswith((".webm", ".wav", ".ogg", ".mp3", ".mp4")):
        raise HTTPException(status_code=404, detail="Audio recording not found")
    return FileResponse(file_path, media_type="audio/webm")
    
class TTSRequest(BaseModel):
    text: str = Field(..., max_length=3000)
    language: Optional[str] = Field("hi", max_length=15)

@app.post("/api/tts")
async def text_to_speech_endpoint(req: TTSRequest, request: Request):
    check_rate_limit(request, "tts", max_requests=40, window_seconds=60)
    clean_text = req.text.strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    from services.tts_service import synthesize_speech_audio
    audio_bytes = synthesize_speech_audio(clean_text, language=req.language or "hi")
    if not audio_bytes:
        raise HTTPException(status_code=500, detail="Failed to synthesize speech audio")
    return Response(content=audio_bytes, media_type="audio/mpeg")


# ========================================================
# OPERATOR CASE CREATION OTP ROUTES (REAL SMS)
# ========================================================

class OperatorSendOtpRequest(BaseModel):
    case_id: str = Field(..., max_length=60)
    mobile: str = Field(..., max_length=15, min_length=10)

class OperatorVerifyOtpRequest(BaseModel):
    case_id: str = Field(..., max_length=60)
    mobile: str = Field(..., max_length=15, min_length=10)
    otp: str = Field(..., max_length=6, min_length=6)

@app.post("/api/operator/send-case-otp")
async def operator_send_case_otp(req: OperatorSendOtpRequest, request: Request):
    require_operator(request)
    check_rate_limit(request, "operator_send_otp", max_requests=10, window_seconds=60)
    
    is_valid, mobile_digits = validate_mobile(req.mobile)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Please enter a valid 10-digit mobile number.")
        
    if not is_sms_configured():
        raise HTTPException(status_code=400, detail="SMS service is not configured.")
        
    mobile_hash = hashlib.sha256(mobile_digits.encode()).hexdigest()
    case_id = req.case_id.strip().upper()
    
    try:
        otp = generate_otp(case_id, mobile_hash)
    except PermissionError as e:
        raise HTTPException(status_code=429, detail=str(e))
        
    sms_res = send_sms_otp(mobile_digits, otp)
    if not sms_res.get("success"):
        raise HTTPException(status_code=502, detail=sms_res.get("error", "Failed to deliver SMS."))
        
    return {
        "success": True,
        "message": f"Verification OTP sent to {mask_mobile(mobile_digits)} via SMS.",
        "masked_mobile": mask_mobile(mobile_digits)
    }

@app.post("/api/operator/verify-case-otp")
async def operator_verify_case_otp(req: OperatorVerifyOtpRequest, request: Request):
    require_operator(request)
    check_rate_limit(request, "operator_verify_otp", max_requests=10, window_seconds=60)
    
    is_valid, mobile_digits = validate_mobile(req.mobile)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Please enter a valid 10-digit mobile number.")
        
    mobile_hash = hashlib.sha256(mobile_digits.encode()).hexdigest()
    case_id = req.case_id.strip().upper()
    
    otp_res = verify_otp(case_id, mobile_hash, req.otp.strip())
    if not otp_res.get("success"):
        status_code = 429 if otp_res.get("locked") else 400
        raise HTTPException(status_code=status_code, detail=otp_res.get("error", "Invalid OTP entered."))
        
    return {
        "success": True,
        "verified": True,
        "message": f"Mobile number {mask_mobile(mobile_digits)} verified successfully.",
        "masked_mobile": mask_mobile(mobile_digits)
    }

# ========================================================
# CITIZEN TRACKING ROUTES (REAL SMS OTP)
# ========================================================

class CitizenTrackRequest(BaseModel):
    case_id: str = Field(..., max_length=60)
    mobile: str = Field(..., max_length=15, min_length=10)
    otp: str = Field(..., max_length=6, min_length=4)

class RequestOtpRequest(BaseModel):
    case_id: str = Field(..., max_length=60)
    mobile: str = Field(..., max_length=15, min_length=10)

@app.post("/api/citizen/request-otp")
async def citizen_request_otp(req: RequestOtpRequest, request: Request):
    check_rate_limit(request, "citizen_otp", max_requests=5, window_seconds=60)
    is_valid, mobile_digits = validate_mobile(req.mobile)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Please enter a valid 10-digit mobile number.")

    mobile_hash = hashlib.sha256(mobile_digits.encode()).hexdigest()
    case_id = req.case_id.strip().upper()
    case = get_case(case_id)

    # Reject if case does not exist or mobile does not match
    if not case or case.get('citizen_mobile_hash') != mobile_hash:
        if config.DEMO_MODE:
            raise HTTPException(status_code=404, detail="Case ID or mobile number does not match our records.")
        return {
            "success": True,
            "demo_mode": False,
            "message": "If this Case ID and mobile number match our records, a one-time verification code has been sent via SMS."
        }

    try:
        otp = generate_otp(case_id, mobile_hash)
        sms_res = send_sms_otp(mobile_digits, otp)
        if not sms_res.get("success"):
            if sms_res.get("error") == "SMS service is not configured.":
                if config.DEMO_MODE:
                    return {
                        "success": True,
                        "demo_mode": True,
                        "message": "DEMO MODE (SMS Unconfigured): use OTP 123456",
                        "provider": "Demo Mode"
                    }
                raise HTTPException(status_code=400, detail="SMS service is not configured.")
            raise HTTPException(status_code=502, detail="Unable to send OTP. Please try again.")
        if config.DEMO_MODE:
            return {
                "success": True,
                "demo_mode": True,
                "message": "DEMO MODE: use OTP 123456",
                "provider": "Demo Mode"
            }
        return {
            "success": True,
            "demo_mode": False,
            "message": "OTP sent to your mobile number.",
            "provider": sms_res.get("provider", "SMS")
        }
    except PermissionError as e:
        raise HTTPException(status_code=429, detail=str(e))

@app.post("/api/citizen/track")
async def citizen_track(req: CitizenTrackRequest, request: Request):
    check_rate_limit(request, "citizen_track", max_requests=10, window_seconds=60)
    is_valid, mobile_digits = validate_mobile(req.mobile)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Please enter a valid 10-digit mobile number.")
    mobile_hash = hashlib.sha256(mobile_digits.encode()).hexdigest()
    case_id = req.case_id.strip().upper()
    case = get_case(case_id)
    if not case or case.get('citizen_mobile_hash') != mobile_hash:
        raise HTTPException(status_code=401, detail="Invalid details provided.")
    otp_result = verify_otp(case_id, mobile_hash, req.otp.strip())
    if not otp_result['success']:
        raise HTTPException(status_code=401, detail=otp_result['error'])
    extracted = case.get('extracted_fields', {})
    raw_status = case.get('verification_status', 'Application Ready — Not Yet Submitted')
    if raw_status == 'Operator Verified':
        display_status = 'Operator Verified — Ready to Submit'
    elif raw_status == 'Submitted':
        display_status = 'Application Ready — Not Yet Submitted'
    else:
        display_status = f"{raw_status} — Ready to Submit"
    docs = case.get('generated_documents', {})
    has_pdf = bool(docs) and isinstance(docs, dict) and bool(docs.get('english_application')) and case.get('verification_status') == 'Operator Verified'
    return {
        "case_id": case.get('id'),
        "citizen_name": case.get('citizen_name', 'Citizen'),
        "issue_type": extracted.get('issue_type', 'General Grievance'),
        "village": extracted.get('village', ''),
        "district": extracted.get('district', ''),
        "state": extracted.get('state', ''),
        "language": case.get('language', 'hi'),
        "status": display_status,
        "submission_note": "This application has been verified and prepared for submission. Submit this to the competent authority / Gram Panchayat / Jan Seva Kendra / official portal.",
        "created_at": case.get('created_at', ''),
        "center_name": case.get('center_name', 'CSC Center'),
        "center_phone": case.get('center_phone', ''),
        "pdf_available": has_pdf
    }

@app.get("/api/citizen/pdf/{case_id}", response_class=HTMLResponse)
async def citizen_get_pdf(case_id: str, request: Request, mobile: str = "", otp: str = ""):
    """Citizen PDF — only if Operator Verified. Requires re-verification via OTP."""
    mobile_digits = ''.join(c for c in mobile if c.isdigit())[-10:]
    if len(mobile_digits) < 10:
        raise HTTPException(status_code=401, detail="Unauthorized")
    mobile_hash = hashlib.sha256(mobile_digits.encode()).hexdigest()
    case = get_case(case_id.upper())
    if not case or case.get('citizen_mobile_hash') != mobile_hash:
        raise HTTPException(status_code=401, detail="Unauthorized")
    otp_result = verify_otp(case_id.upper(), mobile_hash, otp.strip())
    if not otp_result['success']:
        raise HTTPException(status_code=401, detail="Unauthorized: " + otp_result.get('error', ''))
    if case.get('verification_status') != 'Operator Verified':
        raise HTTPException(status_code=403, detail="Document not yet verified. Please check back later.")
    doc_data = case.get('generated_documents', {})
    if not doc_data:
        raise HTTPException(status_code=404, detail="Document not found")
    return generate_printable_html(doc_data, case)

if __name__ == "__main__":

    import uvicorn
    init_db()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    print("\n=======================================================")
    print("  AWAAZ ADHIKAR - CIVIC GRIEVANCE DOCUMENTATION WORKSPACE")
    print(f"  Running on: http://{host}:{port}")
    print("  SerpApi Configured:", bool(config.SERPAPI_API_KEY))
    print("=======================================================\n")
    uvicorn.run("main:app", host=host, port=port, reload=False)
