import os
import sys
import json
import time
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

def run_phase2_tests():
    print("=" * 75)
    print("  AWAAZ ADHIKAR - PHASE 2 VERIFICATION TEST SUITE")
    print("  Scope: Intake, Multilingual STT/Text, AI Extraction, Validation,")
    print("         Missing Fields, Contradictions, Cascading Divisions")
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

    ip_counter = 200
    def get_test_headers():
        nonlocal ip_counter
        ip_counter += 1
        return {"X-Forwarded-For": f"198.51.100.{ip_counter}"}

    # 1. Administrative Locations API
    status, body, _ = http_req("/api/locations", headers=get_test_headers())
    check("Administrative locations endpoint returns HTTP 200", status == 200, f"Got status {status}")
    check("Administrative locations contains all 28 States and 8 UTs",
          isinstance(body, dict) and len(body) >= 36 and "Maharashtra" in body and "Uttar Pradesh" in body and "West Bengal" in body,
          f"Found {len(body) if isinstance(body, dict) else 0} administrative divisions")
    check("Administrative divisions include Solapur (MH) and Murshidabad (WB)",
          "Solapur" in body.get("Maharashtra", {}).get("districts", []) and
          "Murshidabad" in body.get("West Bengal", {}).get("districts", []),
          "Districts missing in administrative divisions")

    # 2. Supported Languages Endpoint
    status, langs, _ = http_req("/api/languages", headers=get_test_headers())
    check("Languages endpoint returns 200 with Hindi, Marathi, Bengali, English",
          status == 200 and isinstance(langs, list) and len(langs) >= 4 and
          any(l.get("code") == "hi" for l in langs) and
          any(l.get("code") == "mr" for l in langs) and
          any(l.get("code") == "bn" for l in langs) and
          any(l.get("code") == "en" for l in langs),
          f"Languages: {langs}")

    # 3. Empty Transcript Validation
    status, body, _ = http_req("/api/extract", method="POST", data={"transcript": "", "language": "hi"}, headers=get_test_headers())
    check("Empty transcript rejected with HTTP 400 or 422", status in [400, 422], f"Got status {status}")

    # 4. Hindi Extraction & Fact Structuring
    hi_text = "मेरा नाम रमेश कुमार है। मुझे 3 महीने से वृद्धावस्था पेंशन नहीं मिली है। मैं रामपुर गाँव, जिला सीतापुर, उत्तर प्रदेश से हूँ।"
    status, res, _ = http_req("/api/extract", method="POST", data={"transcript": hi_text, "language": "hi"}, headers=get_test_headers())
    check("Hindi fact extraction returns HTTP 200", status == 200, f"Got {status}")
    f = res.get("extracted_fields", {}) if isinstance(res, dict) else {}
    check("Hindi extraction parses Name: 'रमेश कुमार'", "रमेश कुमार" in f.get("citizen_name", ""), f"Got {f.get('citizen_name')}")
    check("Hindi extraction parses Location: Rampur, Sitapur, Uttar Pradesh",
          "रामपुर" in f.get("village", "") and f.get("district") == "Sitapur" and f.get("state") == "Uttar Pradesh",
          f"Village={f.get('village')}, Dist={f.get('district')}, State={f.get('state')}")
    check("Hindi extraction parses Duration: '3 महीने'", "3 महीने" in f.get("duration", ""), f"Got {f.get('duration')}")
    check("Hindi extraction classifies Scheme as 'pension'", f.get("scheme_code") == "pension", f"Got {f.get('scheme_code')}")

    # 5. Marathi Extraction & Alias Mapping
    mr_text = "माझे नाव तुकाराम पाटील आहे. मला ३ महिन्यांपासून पेन्शन मिळालेली नाही. मी सोलापूर जिल्ह्यातील आहे."
    status, res, _ = http_req("/api/extract", method="POST", data={"transcript": mr_text, "language": "mr"}, headers=get_test_headers())
    check("Marathi fact extraction returns HTTP 200", status == 200, f"Got {status}")
    f = res.get("extracted_fields", {}) if isinstance(res, dict) else {}
    check("Marathi extraction parses Name: 'तुकाराम पाटील'", "तुकाराम पाटील" in f.get("citizen_name", ""), f"Got {f.get('citizen_name')}")
    check("Marathi extraction resolves District: 'Solapur' and State: 'Maharashtra'",
          f.get("district") == "Solapur" and f.get("state") == "Maharashtra",
          f"Dist={f.get('district')}, State={f.get('state')}")
    check("Marathi extraction detects missing village and adds to missing_fields",
          any("village" in m.lower() for m in res.get("missing_fields", [])),
          f"Missing: {res.get('missing_fields')}")

    # 6. Bengali Extraction & Scheme Classification
    bn_text = "আমার নাম পরিমল বিশ্বাস। ৩ মাস ধরে রেশন পাচ্ছি না। আমি মুর্শিদাবাদ জেলার বাসিন্দা।"
    status, res, _ = http_req("/api/extract", method="POST", data={"transcript": bn_text, "language": "bn"}, headers=get_test_headers())
    check("Bengali fact extraction returns HTTP 200", status == 200, f"Got {status}")
    f = res.get("extracted_fields", {}) if isinstance(res, dict) else {}
    check("Bengali extraction parses Name: 'পরিমল বিশ্বাস'", "পরিমল বিশ্বাস" in f.get("citizen_name", ""), f"Got {f.get('citizen_name')}")
    check("Bengali extraction resolves District: 'Murshidabad' and State: 'West Bengal'",
          f.get("district") == "Murshidabad" and f.get("state") == "West Bengal",
          f"Dist={f.get('district')}, State={f.get('state')}")
    check("Bengali extraction classifies Scheme as 'ration'", f.get("scheme_code") == "ration", f"Got {f.get('scheme_code')}")

    # 7. English Extraction
    en_text = "My name is Rajesh Patel. I have not received PM Kisan installment for 6 months. I am from Kheda district, Gujarat."
    status, res, _ = http_req("/api/extract", method="POST", data={"transcript": en_text, "language": "en"}, headers=get_test_headers())
    check("English fact extraction returns HTTP 200", status == 200, f"Got {status}")
    f = res.get("extracted_fields", {}) if isinstance(res, dict) else {}
    check("English extraction parses Name: 'Rajesh Patel'", "Rajesh Patel" in f.get("citizen_name", ""), f"Got {f.get('citizen_name')}")
    check("English extraction classifies Scheme as 'pmkisan'", f.get("scheme_code") == "pmkisan", f"Got {f.get('scheme_code')}")

    # 8. Contradiction Detection: Conflicting Timeframes
    contra_text = "मेरा नाम मोहन है। मुझे 2 महीने और 3 साल से राशन नहीं मिला। जिला सीतापुर उत्तर प्रदेश।"
    status, res, _ = http_req("/api/extract", method="POST", data={"transcript": contra_text, "language": "hi"}, headers=get_test_headers())
    check("Contradiction detection flags conflicting timeframes (months vs years)",
          any("timeframe" in c.lower() or "month" in c.lower() for c in res.get("contradictions", [])),
          f"Contradictions: {res.get('contradictions')}")

    # 9. Contradiction Detection: State vs District Inconsistency
    from services.extractor_service import extract_structured_facts
    # Test programmatic check on state-district mismatch
    res_mismatch = extract_structured_facts("मेरा नाम सुरेश है। मैं सीतापुर जिला, महाराष्ट्र में रहता हूँ।", language="hi")
    check("Location mismatch detected when District does not belong to selected State",
          any("does not belong" in c for c in res_mismatch.get("contradictions", [])),
          f"Contradictions: {res_mismatch.get('contradictions')}")

    # 10. Missing Fields Flagging (No Hallucination)
    incomplete_text = "मेरी समस्या यह है कि पानी का नल टूट गया है।"
    status, res, _ = http_req("/api/extract", method="POST", data={"transcript": incomplete_text, "language": "hi"}, headers=get_test_headers())
    f = res.get("extracted_fields", {}) if isinstance(res, dict) else {}
    check("Incomplete statement leaves unstated name and village empty without hallucinating",
          f.get("citizen_name") == "" and f.get("village") == "",
          f"Hallucinated: Name={f.get('citizen_name')}, Village={f.get('village')}")
    check("Missing fields explicitly alert operator for Name and Village",
          any("name" in m.lower() for m in res.get("missing_fields", [])) and
          any("village" in m.lower() for m in res.get("missing_fields", [])),
          f"Missing: {res.get('missing_fields')}")

    print("=" * 75)
    print(f"  PHASE 2 TEST SUMMARY: {passed} / {total} tests passed")
    print("=" * 75)
    return passed == total

if __name__ == "__main__":
    success = run_phase2_tests()
    sys.exit(0 if success else 1)
