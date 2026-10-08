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

def run_phase4_tests():
    print("=" * 75)
    print("  AWAAZ ADHIKAR - PHASE 4 VERIFICATION TEST SUITE")
    print("  Scope: Document Generation, Translation Quality, Bilingual Export,")
    print("         Printable View, All Demo Scenarios, Production Readiness")
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

    ip_counter = 400
    def get_test_headers(token=None):
        nonlocal ip_counter
        ip_counter += 1
        h = {"X-Forwarded-For": f"198.51.100.{ip_counter}"}
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    # 1. Operator Auth Session
    status, login_res, _ = http_req("/api/auth/demo-login", method="POST", headers=get_test_headers())
    check("Operator login succeeds for Phase 4 tests", status == 200 and "token" in login_res, f"Got {status}")
    token = login_res.get("token")

    # 2. Marathi Land Encroachment Translation Quality Check
    from services.translation_service import synthesize_professional_wording
    marathi_raw = (
        "माझ्या जमिनीवर दुसऱ्या व्यक्तीने अतिक्रमण केले आहे. माझ्याकडे जमिनीची कागदपत्रे आहेत. "
        "कृपया माझी तक्रार तपासून योग्य ती कार्यवाही करण्यास मदत करावी."
    )
    extracted_mr = {
        "citizen_name": "Tukaram Patil",
        "village": "Mohol",
        "district": "Solapur",
        "state": "Maharashtra",
        "duration": "3 months",
        "issue_type": "Land Encroachment",
        "scheme": "Revenue Records"
    }
    wording_mr = synthesize_professional_wording(marathi_raw, "mr", extracted_mr)
    en_synth = wording_mr.get("english", "")
    mr_synth = wording_mr.get("regional", "")

    # Verification: English contains zero Devanagari characters
    has_devanagari_in_en = any(0x0900 <= ord(c) <= 0x097F for c in en_synth)
    check("English translation contains NO Devanagari characters", not has_devanagari_in_en, f"Devanagari found in English: {en_synth}")
    check("English synthesis preserves allegation as an allegation", 
          "alleged" in en_synth.lower() or "encroachment" in en_synth.lower(),
          f"Missing formal allegation phrasing: {en_synth}")
    check("Marathi synthesis uses formal administrative wording", 
          "कथित अनधिकृत अतिक्रमण" in mr_synth or "अधिकृत कागदपत्रे" in mr_synth,
          f"Marathi synthesis: {mr_synth}")

    # 3. Bengali PDS Ration Translation Quality Check
    bengali_raw = (
        "আমার নাম স্বপন মজুমদার। আমি গ্রাম বিষ্ণুপুর, জেলা দক্ষিণ ২৪ পরগনা পশ্চিমবঙ্গ থেকে বলছি। "
        "গত ২ মাস ধরে আমাদের রেশন ডিলার চাল ও গম দিতে অস্বীকার করছে।"
    )
    extracted_bn = {
        "citizen_name": "Swapan Majumdar",
        "village": "Bishnupur",
        "district": "South 24 Parganas",
        "state": "West Bengal",
        "duration": "2 months",
        "issue_type": "PDS Ration Denial",
        "scheme": "NFSA Ration"
    }
    wording_bn = synthesize_professional_wording(bengali_raw, "bn", extracted_bn)
    en_synth_bn = wording_bn.get("english", "")
    has_bengali_in_en = any(0x0980 <= ord(c) <= 0x09FF for c in en_synth_bn)
    check("English translation contains NO Bengali characters", not has_bengali_in_en, f"Bengali found in English: {en_synth_bn}")
    check("English synthesis accurately preserves PDS entitlement and duration",
          "public distribution system" in en_synth_bn.lower() or "food grains" in en_synth_bn.lower() or "ration" in en_synth_bn.lower(),
          f"English synthesis: {en_synth_bn}")

    # 4. Bilingual Document Generation Endpoint (/api/generate-document)
    case_mr_payload = {
        "id": "CASE-PHASE4-MR",
        "language": "mr",
        "citizen_name": "Tukaram Patil",
        "original_transcript": marathi_raw,
        "edited_transcript": marathi_raw,
        "template_type": "general",
        "extracted_fields": extracted_mr,
        "sources": [
            {
                "id": "src-1",
                "title": "Digital India Land Records Modernization Programme (DILRMP)",
                "url": "https://dilrmp.gov.in/",
                "domain": "dilrmp.gov.in",
                "is_official": True,
                "operator_verified": True
            }
        ],
        "verification_status": "Operator Verified"
    }
    status, doc_res, _ = http_req("/api/generate-document", method="POST",
                                  data={"case_data": case_mr_payload},
                                  headers=get_test_headers(token))
    check("Document generation endpoint returns HTTP 200", status == 200, f"Got {status}")
    check("Generated package contains regional_language and english_application",
          isinstance(doc_res, dict) and "regional_language" in doc_res and "english_application" in doc_res,
          f"Missing doc keys: {list(doc_res.keys()) if isinstance(doc_res, dict) else doc_res}")
    
    reg_body = doc_res.get("regional_language", {}).get("body", "")
    en_body = doc_res.get("english_application", {}).get("body", "")
    check("Primary document is in Marathi with formal subject and address", 
          "प्रति" in reg_body and "जिल्हा: Solapur" in reg_body, 
          f"Marathi body: {reg_body[:100]}...")
    check("Secondary document is in English without raw Marathi text",
          "To," in en_body and "SUBJECT:" in en_body and not any(0x0900 <= ord(c) <= 0x097F for c in en_body),
          f"English body has Devanagari or missing formal structure")

    # 5. Printable Document View (/document/{case_id})
    status, html_page, _ = http_req(f"/document/CASE-PHASE4-MR?token={token}", headers=get_test_headers())
    check("Printable view returns HTTP 200 HTML with valid query token", status == 200, f"Got {status}")
    check("Printable view includes official header, fonts, and print stylesheet",
          "@media print" in str(html_page) and "Awaaz Adhikar" in str(html_page) and "CASE-PHASE4-MR" in str(html_page),
          "Printable HTML missing print styles or case ID")

    # 6. Verify All 5 Demo Scenarios End-to-End
    status, samples, _ = http_req("/api/samples", headers=get_test_headers())
    check("Samples API returns 5 demo scenarios", status == 200 and isinstance(samples, list) and len(samples) == 5, f"Found {len(samples) if isinstance(samples, list) else 0} samples")

    scenario_success = True
    for s in samples:
        s_id = s.get("id")
        lang = s.get("language")
        transcript = s.get("transcript")
        # Step 1: Extract
        st, ext_res, _ = http_req("/api/extract", method="POST", data={"transcript": transcript, "language": lang}, headers=get_test_headers())
        if st != 200:
            scenario_success = False
            break
        # Step 2: Search sources
        st, src_res, _ = http_req("/api/search-sources", method="POST", data={"query": s.get("query"), "extracted_fields": ext_res.get("extracted_fields")}, headers=get_test_headers())
        if st != 200:
            scenario_success = False
            break
        # Step 3: Mappings
        st, map_res, _ = http_req("/api/mappings", method="POST", data={"extracted_fields": ext_res.get("extracted_fields"), "sources": src_res.get("sources")}, headers=get_test_headers())
        if st != 200:
            scenario_success = False
            break
        # Step 4: Generate Document
        demo_case = {
            "id": f"CASE-{s_id.upper()}",
            "language": lang,
            "citizen_name": s.get("citizen_name"),
            "original_transcript": transcript,
            "edited_transcript": transcript,
            "template_type": s.get("category"),
            "extracted_fields": ext_res.get("extracted_fields"),
            "sources": src_res.get("sources"),
            "claim_source_mappings": map_res,
            "verification_status": "Operator Verified"
        }
        st, gen_res, _ = http_req("/api/generate-document", method="POST", data={"case_data": demo_case}, headers=get_test_headers(token))
        if st != 200:
            scenario_success = False
            break
        # Clean up
        http_req(f"/api/cases/CASE-{s_id.upper()}", method="DELETE", headers=get_test_headers(token))

    check("All 5 demo scenarios execute full pipeline end-to-end (Intake -> AI -> Search -> Document)", scenario_success)

    # Clean up Phase 4 test case
    http_req("/api/cases/CASE-PHASE4-MR", method="DELETE", headers=get_test_headers(token))

    print("=" * 75)
    print(f"  PHASE 4 TEST SUMMARY: {passed} / {total} tests passed")
    print("=" * 75)
    return passed == total

if __name__ == "__main__":
    success = run_phase4_tests()
    sys.exit(0 if success else 1)
