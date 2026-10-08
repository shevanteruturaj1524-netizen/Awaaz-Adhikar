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

def run_phase1_tests():
    print("=" * 75)
    print("  AWAAZ ADHIKAR - PHASE 1 VERIFICATION TEST SUITE")
    print("  Scope: Landing, 4-Step Navigation, Auth, Dashboard, API Security")
    print("=" * 75)

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

    # Use distinct test IP header to avoid triggering brute-force rate limits during test run
    ip_counter = 100

    def get_test_headers(token=None):
        nonlocal ip_counter
        ip_counter += 1
        h = {"X-Forwarded-For": f"198.51.100.{ip_counter}"}
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    # 1. Public Landing Page
    status, body, headers = http_req("/", headers=get_test_headers())
    check("Public landing page returns HTTP 200", status == 200, f"Got status {status}")
    check("Landing page contains brand and hero CTA buttons", 
          "Awaaz Adhikar" in str(body) and "Try Interactive Demo" in str(body) and "Operator Login" in str(body), 
          "Missing brand or CTA in landing HTML")
    check("Landing page outlines 4-step workflow", 
          "step-panel-1" in str(body) and "step-panel-2" in str(body) and "step-panel-3" in str(body) and "step-panel-4" in str(body),
          "Missing 4-step workflow panels")

    # 2. Unauthenticated Access Protection
    status, body, _ = http_req("/api/cases", headers=get_test_headers())
    check("Unauthenticated /api/cases returns 401 Unauthorized", status == 401, f"Got status {status}")

    status, body, _ = http_req("/api/stats", headers=get_test_headers())
    check("Unauthenticated /api/stats returns 401 Unauthorized", status == 401, f"Got status {status}")

    status, body, _ = http_req("/document/NONEXISTENT", headers=get_test_headers())
    check("Unauthenticated /document/{id} returns 401 Unauthorized", status == 401, f"Got status {status}")

    # 3. Invalid Login Attempts
    status, body, _ = http_req("/api/auth/login", method="POST",
                               data={"email": "operator@awaazadhikar.gov.in", "password": "WRONG_PASSWORD_XYZ"},
                               headers=get_test_headers())
    check("Login with incorrect password rejected with 401", status == 401, f"Got status {status}")

    status, body, _ = http_req("/api/auth/login", method="POST",
                               data={"email": "attacker@unknown.domain", "password": "anypassword"},
                               headers=get_test_headers())
    check("Login with unknown email rejected with 401", status == 401, f"Got status {status}")

    # 4. Valid Operator Login
    status, body, _ = http_req("/api/auth/login", method="POST",
                               data={"email": "operator@awaazadhikar.gov.in", "password": "demo123"},
                               headers=get_test_headers())
    check("Operator login with valid credentials returns 200 and token", 
          status == 200 and isinstance(body, dict) and body.get("success") and "token" in body, 
          f"Got {status}, body={body}")
    op_token = body.get("token") if isinstance(body, dict) else None

    # 5. Authenticated Profile & Dashboard Stats
    status, body, _ = http_req("/api/auth/me", headers=get_test_headers(op_token))
    check("Authenticated /api/auth/me returns valid operator identity", 
          status == 200 and body.get("authenticated") is True and body.get("operator", {}).get("id") == "OP-4102",
          f"Got body={body}")

    status, body, _ = http_req("/api/stats", headers=get_test_headers(op_token))
    check("Authenticated /api/stats returns dashboard analytics", 
          status == 200 and "total_cases" in body, f"Got body={body}")

    # 6. Demo Login Endpoint
    status, body, _ = http_req("/api/auth/demo-login", method="POST", headers=get_test_headers())
    check("One-Click Demo login endpoint returns 200 with demo session", 
          status == 200 and isinstance(body, dict) and "token" in body and body.get("operator", {}).get("id") == "OP-4102",
          f"Got status {status}")
    demo_token = body.get("token") if isinstance(body, dict) else None

    # 7. Create New Case in Workspace
    test_case_id = f"CASE-TEST-{uuid.uuid4().hex[:6]}"
    test_case_payload = {
        "id": test_case_id,
        "language": "hi",
        "citizen_name": "Ramesh Kumar Sharma",
        "original_transcript": "मेरी वृद्धावस्था पेंशन पिछले 6 महीने से बंद है। कृपया सहायता करें।",
        "extracted_fields": {
            "citizen_name": "Ramesh Kumar Sharma",
            "village": "Pipra",
            "state": "Uttar Pradesh",
            "district": "Varanasi",
            "duration": "6 months",
            "issue_type": "Pension stoppage",
            "scheme": "NSAP Old Age Pension",
            "department": "Social Welfare"
        },
        "verification_status": "Needs Review"
    }

    status, body, _ = http_req("/api/cases", method="POST", data=test_case_payload, headers=get_test_headers(demo_token))
    check("Create new citizen case returns 200 and persists case", 
          status == 200 and isinstance(body, dict) and body.get("id") == test_case_id,
          f"Got {status}, body={body}")

    # 8. Retrieve Case via Workspace
    status, body, _ = http_req(f"/api/cases/{test_case_id}", headers=get_test_headers(demo_token))
    check("Retrieve existing case returns 200 with saved facts", 
          status == 200 and isinstance(body, dict) and body.get("citizen_name") == "Ramesh Kumar Sharma",
          f"Got {status}, body={body}")

    # 9. List Cases for Dashboard
    status, body, _ = http_req("/api/cases", headers=get_test_headers(demo_token))
    check("List cases returns array containing newly created case", 
          status == 200 and isinstance(body, list) and any(c.get("id") == test_case_id for c in body),
          f"Case {test_case_id} not found in case list")

    # 10. Logout and Invalidate Session
    status, body, _ = http_req("/api/auth/logout", method="POST", headers=get_test_headers(demo_token))
    check("Logout endpoint invalidates session", status == 200 and body.get("success"), f"Got body={body}")

    # 11. Verify Invalidation
    status, body, _ = http_req("/api/cases", headers=get_test_headers(demo_token))
    check("Subsequent request with logged-out token returns 401 Unauthorized", status == 401, f"Got status {status}")

    # 12. Security Headers
    _, _, sec_headers = http_req("/", headers=get_test_headers())
    check("X-Content-Type-Options: nosniff header present", 
          sec_headers.get("x-content-type-options") == "nosniff", f"Got {sec_headers.get('x-content-type-options')}")
    check("X-Frame-Options: SAMEORIGIN header present", 
          sec_headers.get("x-frame-options") == "SAMEORIGIN", f"Got {sec_headers.get('x-frame-options')}")
    check("Referrer-Policy header present", 
          sec_headers.get("referrer-policy") == "strict-origin-when-cross-origin", f"Got {sec_headers.get('referrer-policy')}")

    # 13. Clean up test case using valid op_token
    status, body, _ = http_req(f"/api/cases/{test_case_id}", method="DELETE", headers=get_test_headers(op_token))
    check("Clean up test case returns 200", status == 200, f"Got status {status}")

    print("=" * 75)
    print(f"  PHASE 1 TEST SUMMARY: {passed} / {total} tests passed")
    print("=" * 75)
    return passed == total

if __name__ == "__main__":
    success = run_phase1_tests()
    sys.exit(0 if success else 1)
