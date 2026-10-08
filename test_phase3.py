import os
import sys
import json
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

def run_phase3_tests():
    print("=" * 75)
    print("  AWAAZ ADHIKAR - PHASE 3 VERIFICATION TEST SUITE")
    print("  Scope: SerpApi / Official Gov Sources, Validation,")
    print("         Claim ↔ Source Mapping, Operator Verification Checklist")
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

    ip_counter = 300
    def get_test_headers(token=None):
        nonlocal ip_counter
        ip_counter += 1
        h = {"X-Forwarded-For": f"198.51.100.{ip_counter}"}
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    # 1. Official Gov Domain Validator Unit Check
    from services.serp_service import is_official_gov_domain, generate_gov_search_query
    check("is_official_gov_domain validates pgportal.gov.in", is_official_gov_domain("https://pgportal.gov.in/pension/") is True)
    check("is_official_gov_domain validates nsap.nic.in", is_official_gov_domain("https://nsap.nic.in/index.html") is True)
    check("is_official_gov_domain validates pmkisan.gov.in", is_official_gov_domain("https://pmkisan.gov.in/") is True)
    check("is_official_gov_domain validates nfsa.gov.in", is_official_gov_domain("https://nfsa.gov.in/portal") is True)
    check("is_official_gov_domain validates dilrmp.gov.in", is_official_gov_domain("https://dilrmp.gov.in/") is True)
    check("is_official_gov_domain validates state gov portal (jansunwai.up.nic.in)", is_official_gov_domain("https://jansunwai.up.nic.in/") is True)
    check("is_official_gov_domain rejects third-party/commercial domains", 
          is_official_gov_domain("https://fake-scheme-consultancy.com/") is False and
          is_official_gov_domain("https://random-news-portal.org/") is False)

    # 2. Query Generation Check
    sample_fields = {
        "issue_type": "Old age pension stoppage",
        "scheme": "NSAP Pension",
        "state": "Uttar Pradesh",
        "district": "Sitapur"
    }
    q = generate_gov_search_query(sample_fields)
    check("generate_gov_search_query includes site:gov.in constraint", "site:gov.in" in q, f"Query: {q}")
    check("generate_gov_search_query includes State name and Scheme", "Uttar Pradesh" in q and "NSAP Pension" in q, f"Query: {q}")

    # 3. Search Official Gov Sources: Pension
    status, res, _ = http_req("/api/search-sources", method="POST",
                              data={"query": "site:gov.in pension grievance Uttar Pradesh", "extracted_fields": {"scheme": "pension"}},
                              headers=get_test_headers())
    check("Search endpoint returns HTTP 200 for Pension", status == 200, f"Got {status}")
    sources = res.get("sources", []) if isinstance(res, dict) else []
    check("Pension search returns official gov sources", len(sources) >= 2, f"Found {len(sources)} sources")
    check("Pension sources include official .gov.in or .nic.in portals",
          any("pgportal.gov.in" in s.get("domain", "") or "nsap.nic.in" in s.get("domain", "") for s in sources),
          f"Sources: {[s.get('domain') for s in sources]}")
    check("All returned sources pass official domain validation",
          all(s.get("is_official") for s in sources),
          "Some sources failed official domain check")

    # 4. Search Official Gov Sources: Ration / Food Distribution
    status, res, _ = http_req("/api/search-sources", method="POST",
                              data={"query": "site:gov.in ration grievance West Bengal", "extracted_fields": {"scheme": "ration"}},
                              headers=get_test_headers())
    check("Search endpoint returns HTTP 200 for Ration", status == 200, f"Got {status}")
    sources = res.get("sources", []) if isinstance(res, dict) else []
    check("Ration search returns NFSA / Annavitran official portals",
          any("nfsa.gov.in" in s.get("domain", "") or "annavitran.nic.in" in s.get("domain", "") for s in sources),
          f"Sources: {[s.get('domain') for s in sources]}")

    # 5. Search Official Gov Sources: PM-Kisan
    status, res, _ = http_req("/api/search-sources", method="POST",
                              data={"query": "site:gov.in pm kisan installment grievance", "extracted_fields": {"scheme": "pmkisan"}},
                              headers=get_test_headers())
    check("Search endpoint returns HTTP 200 for PM-Kisan", status == 200, f"Got {status}")
    sources = res.get("sources", []) if isinstance(res, dict) else []
    check("PM-Kisan search returns pmkisan.gov.in or pgportal.gov.in",
          any("pmkisan.gov.in" in s.get("domain", "") or "pgportal.gov.in" in s.get("domain", "") for s in sources),
          f"Sources: {[s.get('domain') for s in sources]}")

    # 6. Search Official Gov Sources: Land Boundary & Encroachment
    status, res, _ = http_req("/api/search-sources", method="POST",
                              data={"query": "site:gov.in land boundary dispute demarcation", "extracted_fields": {"scheme": "land"}},
                              headers=get_test_headers())
    check("Search endpoint returns HTTP 200 for Land dispute", status == 200, f"Got {status}")
    sources = res.get("sources", []) if isinstance(res, dict) else []
    check("Land dispute search returns DILRMP / Revenue official portals",
          any("dilrmp.gov.in" in s.get("domain", "") or "pgportal.gov.in" in s.get("domain", "") for s in sources),
          f"Sources: {[s.get('domain') for s in sources]}")

    # 7. Claim ↔ Source Mapping Endpoint (/api/mappings)
    mapping_payload = {
        "extracted_fields": {
            "citizen_name": "Tukaram Patil",
            "village": "Mohol",
            "district": "Solapur",
            "state": "Maharashtra",
            "duration": "3 months",
            "issue_type": "Land Boundary Dispute",
            "scheme": "Revenue Land Demarcation"
        },
        "sources": sources
    }
    status, mappings, _ = http_req("/api/mappings", method="POST", data=mapping_payload, headers=get_test_headers())
    check("Mappings endpoint returns HTTP 200", status == 200, f"Got {status}")
    check("Mappings array contains at least 3 structured entries", isinstance(mappings, list) and len(mappings) >= 3, f"Got {len(mappings) if isinstance(mappings, list) else 0}")
    check("Mappings separate Citizen Declarations from Statutory Procedures",
          any(m.get("claim_type") == "Citizen-Provided Information" for m in mappings) and
          any(m.get("claim_type") == "Statutory Entitlement / Procedure" for m in mappings),
          "Missing clear separation between citizen claim and statutory rule")

    # 8. Demo Operator Login & Case State Verification Status
    status, login_res, _ = http_req("/api/auth/demo-login", method="POST", headers=get_test_headers())
    token = login_res.get("token")

    case_payload = {
        "id": "CASE-PHASE3-TEST",
        "language": "mr",
        "citizen_name": "Tukaram Patil",
        "original_transcript": "माझ्या जमिनीवर अतिक्रमण झाले आहे.",
        "extracted_fields": mapping_payload["extracted_fields"],
        "sources": sources,
        "claim_source_mappings": mappings,
        "verification_status": "Operator Verified"
    }
    status, saved_case, _ = http_req("/api/cases", method="POST", data=case_payload, headers=get_test_headers(token))
    check("Persist case with sources, mappings, and Operator Verified status",
          status == 200 and saved_case.get("verification_status") == "Operator Verified" and len(saved_case.get("sources", [])) > 0,
          f"Got {status}, case={saved_case}")

    # Clean up test case
    http_req("/api/cases/CASE-PHASE3-TEST", method="DELETE", headers=get_test_headers(token))

    print("=" * 75)
    print(f"  PHASE 3 TEST SUMMARY: {passed} / {total} tests passed")
    print("=" * 75)
    return passed == total

if __name__ == "__main__":
    success = run_phase3_tests()
    sys.exit(0 if success else 1)
