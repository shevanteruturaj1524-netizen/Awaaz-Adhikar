import os
import sys
import json
import time
import uuid
import urllib.request
import urllib.error

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def http_req(path, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    url = f"{BASE_URL}{path}"
    req_data = None
    if data is not None:
        if isinstance(data, (dict, list)):
            req_data = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif isinstance(data, bytes):
            req_data = data
        else:
            req_data = str(data).encode("utf-8")
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            body = res.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = body
            return res.status, parsed, dict(res.headers)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = err_body
        return e.code, parsed, dict(e.headers)

def run_security_tests():
    print("=" * 70)
    print("  AWAAZ ADHIKAR - COMPREHENSIVE SECURITY VERIFICATION SUITE")
    print("=" * 70)

    passed = 0
    total = 0

    def check(name, condition, details=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] Test {total:02d}: {name}")
        else:
            print(f"  [FAIL] Test {total:02d}: {name} - {details}")
            assert False, f"Test failed: {name} - {details}"

    # 1. Unauthenticated access to /api/cases
    status, _, _ = http_req("/api/cases")
    check("Unauthenticated Access to Cases Rejected (401)", status == 401)

    # 2. Unauthenticated access to /api/stats
    status, _, _ = http_req("/api/stats")
    check("Unauthenticated Access to Stats Rejected (401)", status == 401)

    # 3. Unauthenticated access to /document/{case_id}
    status, _, _ = http_req("/document/CASE-DEMO-1")
    check("Unauthenticated Access to Document Rejected (401)", status == 401)

    # 4. Authenticate as Demo Operator (OP-4102)
    status, data, _ = http_req("/api/auth/demo-login", method="POST")
    check("Demo Operator Login Success", status == 200 and "token" in data)
    token_op1 = data["token"]

    # 5. Check Password Hash is NEVER returned in response
    check("No Password Hash in Operator Payload", "password_hash" not in data.get("operator", {}) and "password" not in data.get("operator", {}))

    # 6. Authenticated access to /api/cases with Token
    status, cases, _ = http_req("/api/cases", headers={"Authorization": f"Bearer {token_op1}"})
    check("Authenticated Operator Access to Cases (200)", status == 200 and isinstance(cases, list))

    # 7. Authenticated access to /api/stats with Token
    status, stats, _ = http_req("/api/stats", headers={"Authorization": f"Bearer {token_op1}"})
    check("Authenticated Operator Access to Stats (200)", status == 200 and "total_cases" in stats)

    # 8. Create a private case for Operator 2
    from database import get_connection, hash_password
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM operators WHERE email = 'other.op@test.gov.in'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO operators (id, name, email, password_hash, role, center_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("OP-9999", "Other Operator", "other.op@test.gov.in", hash_password("secretpass123"), "Field Operator", "CSC-DIST-99", "2026-01-01"))
        conn.commit()
    conn.close()

    # Login as Operator 2
    status, data_op2, _ = http_req("/api/auth/login", method="POST", data={"email": "other.op@test.gov.in", "password": "secretpass123"})
    check("Operator 2 Login Success", status == 200 and "token" in data_op2)
    token_op2 = data_op2["token"]

    # Operator 2 creates a private case
    case_op2 = {
        "id": "CASE-PRIVATE-OP2",
        "citizen_name": "Private Citizen X",
        "language": "hi",
        "extracted_fields": {"citizen_name": "Private Citizen X", "village": "Confidential Village", "district": "Patna", "state": "Bihar"},
        "template_type": "general"
    }
    status, saved_c2, _ = http_req("/api/cases", method="POST", data=case_op2, headers={"Authorization": f"Bearer {token_op2}"})
    check("Operator 2 Saves Private Case", status == 200)

    # 9. Cross-Operator Isolation: Operator 2 cannot access cases of another operator
    status, _, _ = http_req("/api/cases/CASE-PRIVATE-OP2", headers={"Authorization": f"Bearer {token_op2}"})
    check("Operator 2 Can Access Own Case", status == 200)

    # 10. Document Authorization: Accessing document without token fails
    status, _, _ = http_req("/document/CASE-PRIVATE-OP2")
    check("Document Access without Token Blocked (401)", status == 401)

    # 11. Document Authorization: Accessing with query token parameter succeeds for owner
    status, doc_html, _ = http_req(f"/document/CASE-PRIVATE-OP2?token={token_op2}")
    check("Document Access with Valid Token Query Param (200)", status == 200 and "Private Citizen X" in doc_html)

    # 12. Cross-Operator Deletion Blocked: Another regular operator cannot delete someone else's case
    # Create Operator 3
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM operators WHERE email = 'intruder@test.gov.in'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO operators (id, name, email, password_hash, role, center_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("OP-7777", "Intruder Op", "intruder@test.gov.in", hash_password("pass123"), "Field Operator", "CSC-77", "2026-01-01"))
        conn.commit()
    conn.close()

    status, data_op3, _ = http_req("/api/auth/login", method="POST", data={"email": "intruder@test.gov.in", "password": "pass123"})
    token_op3 = data_op3["token"]

    status, _, _ = http_req("/api/cases/CASE-PRIVATE-OP2", method="DELETE", headers={"Authorization": f"Bearer {token_op3}"})
    check("Cross-Operator Case Deletion Forbidden (403)", status == 403)

    # 13. Cross-Operator Case View Blocked: Operator 3 cannot fetch Operator 2's case
    status, _, _ = http_req("/api/cases/CASE-PRIVATE-OP2", headers={"Authorization": f"Bearer {token_op3}"})
    check("Cross-Operator Case Retrieval Forbidden (403)", status == 403)

    # 14. Cross-Operator Document View Blocked: Operator 3 cannot view Operator 2's document
    status, _, _ = http_req(f"/document/CASE-PRIVATE-OP2?token={token_op3}")
    check("Cross-Operator Document View Forbidden (403)", status == 403)

    # 15. Audio Endpoint Protection: Unauthenticated cannot read audio
    status, _, _ = http_req("/api/audio/secret_audio.webm")
    check("Unauthenticated Audio Access Blocked (401)", status == 401)

    # 16. Audio Upload: Rejects non-audio MIME type
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    payload = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="malicious.exe"\r\n'
        f"Content-Type: application/x-dosexec\r\n\r\n"
        f"MZ9000fakeexecutablecontent\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Authorization": f"Bearer {token_op1}"
    }
    status, _, _ = http_req("/api/upload-audio", method="POST", data=payload, headers=headers)
    check("Malicious / Non-Audio File Upload Blocked (400)", status == 400)

    # 17. Security Headers Verification
    status, _, resp_headers = http_req("/")
    check("Security Header: X-Content-Type-Options: nosniff", resp_headers.get("x-content-type-options") == "nosniff")
    check("Security Header: X-Frame-Options: SAMEORIGIN", resp_headers.get("x-frame-options") == "SAMEORIGIN")
    check("Security Header: Referrer-Policy", resp_headers.get("referrer-policy") == "strict-origin-when-cross-origin")
    check("Security Header: Content-Security-Policy Present", "content-security-policy" in resp_headers)

    # 18. Rate Limiting: Rapid consecutive login attempts trigger 429
    status_codes = []
    for _ in range(12):
        s, _, _ = http_req("/api/auth/login", method="POST", data={"email": "wrong@test.com", "password": "wrong"}, headers={"X-Forwarded-For": "198.51.100.99"})
        status_codes.append(s)
    check("Rate Limiter Triggers HTTP 429 on Abuse", 429 in status_codes)

    # 19. Session Expiry & Invalidation on Logout
    status, _, _ = http_req("/api/auth/logout", method="POST", headers={"Authorization": f"Bearer {token_op3}"})
    check("Operator Logout Endpoint (200)", status == 200)
    status, me_data, _ = http_req("/api/auth/me", headers={"Authorization": f"Bearer {token_op3}"})
    check("Logged Out Token Rejected", status == 200 and me_data.get("authenticated") is False)

    # 20. Secrets Exposure Verification in Frontend Source
    status, js_content, _ = http_req("/static/app.js")
    check("No Hardcoded Private Keys in JavaScript", "private_key" not in js_content and "sk-" not in js_content)

    print("=" * 70)
    print(f"  SECURITY SUMMARY: {passed}/{total} SECURITY TESTS PASSED! ")
    print("=" * 70)

if __name__ == "__main__":
    run_security_tests()
