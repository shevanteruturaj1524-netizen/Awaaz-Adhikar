import sqlite3
import json
import uuid
import random
import time
from datetime import datetime
from pathlib import Path
import config
from config import DATA_DIR

from typing import Optional, Dict, Any, List

DB_PATH = DATA_DIR / "awaaz_adhikar.db"

def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

import hashlib
import hmac

SALT = b"awaaz_adhikar_sec_salt_2026"

def hash_password(password: str) -> str:
    # PBKDF2 HMAC SHA-256 with 100,000 iterations
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), SALT, 100000).hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Check PBKDF2 hash
    pbkdf2_hash = hash_password(plain_password)
    if hmac.compare_digest(pbkdf2_hash, hashed_password):
        return True
    # Backward compatibility with legacy SHA-256
    legacy_sha256 = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    if hmac.compare_digest(legacy_sha256, hashed_password):
        return True
    return False

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        operator_id TEXT,
        citizen_name TEXT,
        language TEXT DEFAULT 'hi',
        consent INTEGER DEFAULT 1,
        original_transcript TEXT,
        edited_transcript TEXT,
        extracted_fields TEXT,
        missing_fields TEXT,
        contradictions TEXT,
        search_query TEXT,
        sources TEXT,
        claim_source_mappings TEXT,
        verification_status TEXT DEFAULT 'Needs Review',
        checklist_state TEXT,
        template_type TEXT DEFAULT 'pension',
        template_version TEXT DEFAULT 'v1.0-2026',
        generated_documents TEXT,
        deleted_at TEXT,
        citizen_mobile_hash TEXT,
        citizen_mobile_masked TEXT,
        center_name TEXT DEFAULT 'CSC Center',
        center_phone TEXT DEFAULT '',
        status TEXT DEFAULT 'Submitted'
    )
    """)

    # Add new columns to existing databases
    for col, defval in [
        ('citizen_mobile_hash', 'TEXT'),
        ('citizen_mobile_masked', 'TEXT'),
        ('center_name', "TEXT DEFAULT 'CSC Center'"),
        ('center_phone', "TEXT DEFAULT ''"),
        ('status', "TEXT DEFAULT 'Submitted'"),
    ]:
        try:
            cursor.execute(f'ALTER TABLE cases ADD COLUMN {col} {defval}')
        except Exception:
            pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operators (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'CSC Operator',
        center_id TEXT DEFAULT 'CSC-DESK-4102',
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
CREATE TABLE IF NOT EXISTS otp_attempts (
    case_id TEXT NOT NULL,
    mobile_hash TEXT NOT NULL,
    otp_hash TEXT NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    used INTEGER DEFAULT 0,
    failed_attempts INTEGER DEFAULT 0,
    locked_until REAL DEFAULT 0,
    PRIMARY KEY (case_id, mobile_hash)
)
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operator_sessions (
        token TEXT PRIMARY KEY,
        operator_id TEXT NOT NULL,
        created_at REAL NOT NULL,
        expires_at REAL NOT NULL
    )
    """)

    # Seed demo operator if not present
    cursor.execute("SELECT id, password_hash FROM operators WHERE email = ?", ("operator@awaazadhikar.gov.in",))
    row = cursor.fetchone()
    if not row:
        demo_pwd_hash = hash_password("demo123")
        cursor.execute("""
        INSERT INTO operators (id, name, email, password_hash, role, center_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "OP-4102",
            "Suresh Patil",
            "operator@awaazadhikar.gov.in",
            demo_pwd_hash,
            "CSC Lead Operator",
            "CSC-DESK-4102",
            datetime.now().isoformat()
        ))
    else:
        # Transparently upgrade legacy hash if needed
        if not verify_password("demo123", row["password_hash"]):
            demo_pwd_hash = hash_password("demo123")
            cursor.execute("UPDATE operators SET password_hash = ? WHERE id = ?", (demo_pwd_hash, row["id"]))

    conn.commit()
    conn.close()
    seed_demo_data()


def seed_demo_data():
    conn = get_connection()
    cursor = conn.cursor()
    # Seed Center A operator
    cursor.execute('SELECT id FROM operators WHERE email=?', ('centera@awaazadhikar.gov.in',))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO operators (id,name,email,password_hash,role,center_id,created_at) VALUES (?,?,?,?,?,?,?)',
            ('OP-CENTERA','Priya Sharma','centera@awaazadhikar.gov.in',hash_password('center123'),'CSC Operator','CSC-CENTER-A',datetime.now().isoformat()))
    # Seed Center B operator
    cursor.execute('SELECT id FROM operators WHERE email=?', ('centerb@awaazadhikar.gov.in',))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO operators (id,name,email,password_hash,role,center_id,created_at) VALUES (?,?,?,?,?,?,?)',
            ('OP-CENTERB','Rajan Mehta','centerb@awaazadhikar.gov.in',hash_password('center456'),'CSC Operator','CSC-CENTER-B',datetime.now().isoformat()))
    # Seed demo cases
    mobile_a = hashlib.sha256('9876543210'.encode()).hexdigest()
    mobile_b = hashlib.sha256('9123456789'.encode()).hexdigest()
    mobile_c = hashlib.sha256('8800001234'.encode()).hexdigest()
    now = datetime.now().isoformat()
    demo_doc = json.dumps({'regional_language':{'body':'Demo pension application','title':'Pension','sources_reference':'','disclaimer':''},'english_application':{'body':'The applicant states that pension has not been received for 3 months in Pune District, Maharashtra.','title':'Pension','sources_reference':'','disclaimer':''},'case_id':'CASE-DEMO-001','template_name':'Pension','template_version':'v1.0','date_generated':'01-10-2026','language_primary':'hi','last_reviewed':'01-10-2026'})
    for cid, op_id, name, lang, status, v_status, tmpl, mhash, mmask, ctr, doc in [
        ('CASE-DEMO-001','OP-CENTERA','Ramesh Kumar','hi','Verified','Operator Verified','pension',mobile_a,'98XXXXX210','CSC Center A Pune', demo_doc),
        ('CASE-DEMO-002','OP-CENTERA','Sunita Devi','hi','Under Review','Needs Review','water',mobile_b,'91XXXXX789','CSC Center A Pune', '{}'),
        ('CASE-DEMO-003','OP-CENTERB','Swapan Majumdar','bn','Submitted','Needs Review','general',mobile_c,'88XXXXX234','CSC Center B Mumbai', '{}'),
    ]:
        cursor.execute('SELECT id FROM cases WHERE id=?', (cid,))
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO cases (id,created_at,updated_at,operator_id,citizen_name,language,consent,
            original_transcript,edited_transcript,extracted_fields,missing_fields,contradictions,
            search_query,sources,claim_source_mappings,verification_status,checklist_state,
            template_type,template_version,generated_documents,citizen_mobile_hash,
            citizen_mobile_masked,center_name,status)
            VALUES (?,?,?,?,?,?,1,'','','{}','[]','[]','','[]','[]',?,'{}',?,?,?,?,?,?,?)
            """, (cid,now,now,op_id,name,lang,v_status,tmpl,'v1.0',doc,mhash,mmask,ctr,status))
    conn.commit()
    conn.close()


def generate_otp(case_id: str, mobile_hash: str) -> str:
    """
    Demo mode uses the fixed OTP required by the project workflow.
    Live mode keeps the standard hashed, expiring OTP flow.
    """
    import time as _time
    import secrets as _secrets
    now = _time.time()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT locked_until FROM otp_attempts WHERE case_id=? AND mobile_hash=?', (case_id, mobile_hash))
    row = cursor.fetchone()
    if row and (row['locked_until'] or 0) > now:
        conn.close()
        raise PermissionError("Too many failed attempts. Verification locked for 15 minutes.")

    otp = "123456" if getattr(config, "DEMO_MODE", False) else f"{_secrets.randbelow(900000) + 100000}"
    otp_hash = hashlib.sha256(otp.encode()).hexdigest()
    cursor.execute('''
        INSERT OR REPLACE INTO otp_attempts 
        (case_id, mobile_hash, otp_hash, created_at, expires_at, used, failed_attempts, locked_until)
        VALUES (?, ?, ?, ?, ?, 0, 0, 0)
    ''', (case_id, mobile_hash, otp_hash, now, now + 300))
    conn.commit()
    conn.close()
    return otp

def verify_otp(case_id: str, mobile_hash: str, otp_input: str) -> dict:
    """
    Verifies the provided 6-digit OTP against the stored SHA-256 hash.
    Enforces:
    - 5-minute expiry
    - Max 5 failed attempts with 15-minute lockout
    - Single-use OTP (used=1)
    - Constant-time hash comparison
    """
    import time as _time
    conn = get_connection()
    cursor = conn.cursor()
    now = _time.time()
    cursor.execute('SELECT * FROM otp_attempts WHERE case_id=? AND mobile_hash=?', (case_id, mobile_hash))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {'success': False, 'error': 'Invalid details or OTP expired.'}
    row = dict(row)
    if now < (row.get('locked_until') or 0):
        conn.close()
        return {'success': False, 'error': 'Too many failed attempts. Verification locked for 15 minutes.', 'locked': True}
    if row.get('used'):
        conn.close()
        return {'success': False, 'error': 'OTP has already been used. Please request a new code.'}
    if now > (row.get('expires_at') or 0):
        conn.close()
        return {'success': False, 'error': 'OTP has expired. Please request a new code.'}
    otp_hash = hashlib.sha256(otp_input.strip().encode()).hexdigest()
    if not hmac.compare_digest(otp_hash, row.get('otp_hash', '')):
        failed = (row.get('failed_attempts') or 0) + 1
        locked_until = (now + 900) if failed >= 5 else 0
        cursor.execute('UPDATE otp_attempts SET failed_attempts=?, locked_until=? WHERE case_id=? AND mobile_hash=?',
            (failed, locked_until, case_id, mobile_hash))
        conn.commit()
        conn.close()
        msg = 'Too many failed attempts. Verification locked for 15 minutes.' if failed >= 5 else 'Invalid OTP entered. Please try again.'
        return {'success': False, 'error': msg, 'locked': locked_until > 0}
    cursor.execute('UPDATE otp_attempts SET used=1 WHERE case_id=? AND mobile_hash=?', (case_id, mobile_hash))
    conn.commit()
    conn.close()
    return {'success': True}


def authenticate_operator(email: str, password: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, password_hash, role, center_id, created_at FROM operators WHERE lower(email) = lower(?)", (email.strip(),))
    row = cursor.fetchone()
    conn.close()
    if row and verify_password(password, row["password_hash"]):
        op_dict = dict(row)
        del op_dict["password_hash"] # Never return password hash!
        return op_dict
    return None

def get_operator_by_id(operator_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, role, center_id, created_at FROM operators WHERE id = ?", (operator_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def save_operator_session(token: str, operator_id: str, expires_at: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO operator_sessions (token, operator_id, created_at, expires_at)
        VALUES (?, ?, ?, ?)
    """, (token, operator_id, time.time(), expires_at))
    conn.commit()
    conn.close()

def get_operator_session(token: str) -> Optional[Dict[str, Any]]:
    if not token or token in ("undefined", "null"):
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.token, s.operator_id, s.created_at, s.expires_at,
               o.id, o.name, o.email, o.role, o.center_id, o.created_at as op_created_at
        FROM operator_sessions s
        JOIN operators o ON s.operator_id = o.id
        WHERE s.token = ?
    """, (token,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    now = time.time()
    if now > row["expires_at"]:
        delete_operator_session(token)
        return None
    op = {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "center_id": row["center_id"],
        "created_at": row["op_created_at"]
    }
    return {
        "token": row["token"],
        "operator": op,
        "expires_at": row["expires_at"],
        "created_at": row["created_at"]
    }

def delete_operator_session(token: str):
    if not token:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM operator_sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def save_case(case_data: dict, operator_id: str = None) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    case_id = case_data.get("id") or case_data.get("case_id") or str(uuid.uuid4())[:8].upper()
    case_data["id"] = case_id
    case_data["case_id"] = case_id
    now = datetime.now().isoformat()
    
    op_id = operator_id or case_data.get("operator_id") or "OP-4102"
    case_data["operator_id"] = op_id
    
    # Check if case exists and verify ownership
    cursor.execute("SELECT id, operator_id FROM cases WHERE id = ?", (case_id,))
    existing_row = cursor.fetchone()
    
    if existing_row:
        existing_owner = existing_row["operator_id"]
        # Allow owner or demo operator
        if op_id and existing_owner and existing_owner != op_id and op_id != "OP-4102" and existing_owner != "OP-4102":
            conn.close()
            raise PermissionError("Access denied: You are not authorized to modify this case.")
    
    extracted_fields_str = json.dumps(case_data.get("extracted_fields", {}), ensure_ascii=False)
    missing_fields_str = json.dumps(case_data.get("missing_fields", []), ensure_ascii=False)
    contradictions_str = json.dumps(case_data.get("contradictions", []), ensure_ascii=False)
    sources_str = json.dumps(case_data.get("sources", []), ensure_ascii=False)
    mappings_str = json.dumps(case_data.get("claim_source_mappings", []), ensure_ascii=False)
    checklist_str = json.dumps(case_data.get("checklist_state", {}), ensure_ascii=False)
    docs_str = json.dumps(case_data.get("generated_documents", {}), ensure_ascii=False)
    
    citizen_name = case_data.get("extracted_fields", {}).get("citizen_name") or case_data.get("citizen_name", "Citizen")

    if existing_row:
        cursor.execute("""
        UPDATE cases SET
            updated_at = ?,
            operator_id = ?,
            citizen_name = ?,
            language = ?,
            consent = ?,
            original_transcript = ?,
            edited_transcript = ?,
            extracted_fields = ?,
            missing_fields = ?,
            contradictions = ?,
            search_query = ?,
            sources = ?,
            claim_source_mappings = ?,
            verification_status = ?,
            checklist_state = ?,
            template_type = ?,
            template_version = ?,
            generated_documents = ?,
            citizen_mobile_hash = ?,
            citizen_mobile_masked = ?,
            center_name = ?,
            center_phone = ?,
            status = ?,
            deleted_at = NULL
        WHERE id = ?
        """, (
            now,
            op_id,
            citizen_name,
            case_data.get("language", "hi"),
            1 if case_data.get("consent", True) else 0,
            case_data.get("original_transcript", ""),
            case_data.get("edited_transcript", ""),
            extracted_fields_str,
            missing_fields_str,
            contradictions_str,
            case_data.get("search_query", ""),
            sources_str,
            mappings_str,
            case_data.get("verification_status", "Needs Review"),
            checklist_str,
            case_data.get("template_type", "pension"),
            case_data.get("template_version", "v1.0-2026"),
            docs_str,
            case_data.get("citizen_mobile_hash"),
            case_data.get("citizen_mobile_masked"),
            case_data.get("center_name", "CSC Center"),
            case_data.get("center_phone", ""),
            case_data.get("status", "Submitted"),
            case_id
        ))
    else:
        cursor.execute("""
        INSERT INTO cases (
            id, created_at, updated_at, operator_id, citizen_name, language, consent,
            original_transcript, edited_transcript, extracted_fields, missing_fields,
            contradictions, search_query, sources, claim_source_mappings,
            verification_status, checklist_state, template_type, template_version,
            generated_documents, citizen_mobile_hash, citizen_mobile_masked,
            center_name, center_phone, status, deleted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
        """, (
            case_id,
            now,
            now,
            op_id,
            citizen_name,
            case_data.get("language", "hi"),
            1 if case_data.get("consent", True) else 0,
            case_data.get("original_transcript", ""),
            case_data.get("edited_transcript", ""),
            extracted_fields_str,
            missing_fields_str,
            contradictions_str,
            case_data.get("search_query", ""),
            sources_str,
            mappings_str,
            case_data.get("verification_status", "Needs Review"),
            checklist_str,
            case_data.get("template_type", "pension"),
            case_data.get("template_version", "v1.0-2026"),
            docs_str,
            case_data.get("citizen_mobile_hash"),
            case_data.get("citizen_mobile_masked"),
            case_data.get("center_name", "CSC Center"),
            case_data.get("center_phone", ""),
            case_data.get("status", "Submitted")
        ))
    
    conn.commit()
    conn.close()
    case_data["id"] = case_id
    case_data["updated_at"] = now
    return case_data

def get_case(case_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases WHERE id = ? AND deleted_at IS NULL", (case_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_dict(row)

def list_cases(operator_id: str = None, limit=25):
    conn = get_connection()
    cursor = conn.cursor()
    if operator_id and operator_id != "OP-4102":
        cursor.execute("""
        SELECT * FROM cases 
        WHERE deleted_at IS NULL AND (operator_id = ? OR operator_id = 'OP-4102' OR operator_id = 'CSC-OP-01') 
        ORDER BY created_at DESC LIMIT ?
        """, (operator_id, limit))
    else:
        cursor.execute("SELECT * FROM cases WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]

def delete_case(case_id: str, operator_id: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT operator_id FROM cases WHERE id = ? AND deleted_at IS NULL", (case_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    
    if operator_id and row["operator_id"] and row["operator_id"] != operator_id and operator_id != "OP-4102" and row["operator_id"] != "OP-4102":
        conn.close()
        raise PermissionError("Access denied: You are not authorized to delete this case.")

    now = datetime.now().isoformat()
    cursor.execute("UPDATE cases SET deleted_at = ? WHERE id = ?", (now, case_id))
    conn.commit()
    conn.close()
    return True

def get_stats(operator_id: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    
    where_clause = "WHERE deleted_at IS NULL"
    params = []
    if operator_id and operator_id != "OP-4102":
        where_clause += " AND (operator_id = ? OR operator_id = 'OP-4102' OR operator_id = 'CSC-OP-01')"
        params = [operator_id]
        
    cursor.execute(f"SELECT COUNT(*) FROM cases {where_clause}", params)
    total = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM cases {where_clause} AND verification_status = 'Needs Review'", params)
    in_review = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM cases {where_clause} AND verification_status = 'Operator Verified'", params)
    verified = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM cases {where_clause} AND generated_documents != '{{}}' AND generated_documents IS NOT NULL", params)
    generated = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total_cases": total,
        "in_review": in_review,
        "verified": verified,
        "generated_documents": generated
    }

def _row_to_dict(row):
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "operator_id": row["operator_id"],
        "citizen_name": row["citizen_name"],
        "language": row["language"],
        "consent": bool(row["consent"]),
        "original_transcript": row["original_transcript"],
        "edited_transcript": row["edited_transcript"],
        "extracted_fields": json.loads(row["extracted_fields"] or "{}"),
        "missing_fields": json.loads(row["missing_fields"] or "[]"),
        "contradictions": json.loads(row["contradictions"] or "[]"),
        "search_query": row["search_query"],
        "sources": json.loads(row["sources"] or "[]"),
        "claim_source_mappings": json.loads(row["claim_source_mappings"] or "[]"),
        "verification_status": row["verification_status"],
        "checklist_state": json.loads(row["checklist_state"] or "{}"),
        "template_type": row["template_type"],
        "template_version": row["template_version"],
        "generated_documents": json.loads(row["generated_documents"] or "{}"),
        "deleted_at": row["deleted_at"],
        'citizen_mobile_hash': row['citizen_mobile_hash'] if 'citizen_mobile_hash' in row.keys() else None,
        'citizen_mobile_masked': row['citizen_mobile_masked'] if 'citizen_mobile_masked' in row.keys() else None,
        'center_name': row['center_name'] if 'center_name' in row.keys() else 'CSC Center',
        'center_phone': row['center_phone'] if 'center_phone' in row.keys() else '',
        'status': row['status'] if 'status' in row.keys() else 'Submitted',
    }

# Initialize on import
init_db()
