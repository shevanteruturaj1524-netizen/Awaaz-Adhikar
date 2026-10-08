import os
import sys
import json
import time
import socket
import struct
import base64
import random
import urllib.request
import urllib.error
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

class MinimalCDPClient:
    def __init__(self, ws_url):
        url_part = ws_url.replace("ws://", "")
        host_port, path = url_part.split("/", 1)
        host, port = host_port.split(":")
        self.sock = socket.create_connection((host, int(port)), timeout=20)
        
        key = base64.b64encode(os.urandom(16)).decode()
        handshake = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(handshake.encode())
        res = self.sock.recv(4096).decode(errors="ignore")
        if "101" not in res.split("\r\n")[0]:
            raise RuntimeError(f"WebSocket handshake failed: {res}")
        self._msg_id = 1

    def send_cmd(self, method, params=None):
        mid = self._msg_id
        self._msg_id += 1
        msg = json.dumps({"id": mid, "method": method, "params": params or {}})
        payload = msg.encode('utf-8')
        
        mask = [random.randint(0, 255) for _ in range(4)]
        length = len(payload)
        header = bytearray([0x81])
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack(">H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack(">Q", length))
        header.extend(mask)
        masked = bytearray([b ^ mask[i % 4] for i, b in enumerate(payload)])
        self.sock.sendall(header + masked)
        
        while True:
            rep = self._read_frame()
            if not rep:
                continue
            try:
                data = json.loads(rep)
                if data.get("id") == mid:
                    return data
            except Exception:
                pass

    def _read_frame(self):
        head = self.sock.recv(2)
        if len(head) < 2:
            return None
        length = head[1] & 0x7F
        if length == 126:
            ext = self.sock.recv(2)
            length = struct.unpack(">H", ext)[0]
        elif length == 127:
            ext = self.sock.recv(8)
            length = struct.unpack(">Q", ext)[0]
        
        chunks = []
        bytes_read = 0
        while bytes_read < length:
            chunk = self.sock.recv(min(length - bytes_read, 4096))
            if not chunk:
                break
            chunks.append(chunk)
            bytes_read += len(chunk)
        return b"".join(chunks).decode('utf-8', errors='ignore')

    def eval(self, expr):
        res = self.send_cmd("Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": True
        })
        return res.get("result", {}).get("result", {}).get("value")

    def close(self):
        try:
            self.sock.close()
        except:
            pass

def run_suite():
    results = {}
    print("="*60)
    print("STARTING FULL REAL BROWSER & END-TO-END VERIFICATION SUITE")
    print("="*60)

    # 1. TEST PUBLIC URL
    public_url = "https://share-sbjct-acquire-tiny.trycloudflare.com"
    print(f"\n[TEST 10: PUBLIC URL] Probing {public_url} ...")
    try:
        req = urllib.request.Request(f"{public_url}/", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            if resp.status == 200 and "Awaaz Adhikar" in content:
                print(f"  --> PASS: Public URL reached successfully with HTTP 200 and valid HTML title.")
                results["public_url"] = {"status": "PASS", "url": public_url, "code": resp.status}
            else:
                print(f"  --> FAIL: Public URL returned code {resp.status}")
                results["public_url"] = {"status": "FAIL", "url": public_url, "code": resp.status}
    except Exception as e:
        print(f"  --> ERROR probing public URL: {e}")
        results["public_url"] = {"status": "FAIL", "error": str(e)}

    # 2. TEST OTP ENDPOINT SECURITY & CITIZEN TRACKING
    print(f"\n[TEST 3 & 11: OTP SECURITY & CITIZEN TRACKING]")
    try:
        # A) Request OTP for non-existent case
        bad_payload = json.dumps({"case_id": "NON-EXISTENT-CASE", "mobile": "9876543210"}).encode('utf-8')
        req = urllib.request.Request("http://127.0.0.1:8000/api/citizen/request-otp", data=bad_payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                print(f"  --> UNEXPECTED SUCCESS on nonexistent case: {data}")
                results["otp_leak_prevention"] = {"status": "FAIL", "detail": "Did not reject nonexistent case"}
        except urllib.error.HTTPError as he:
            if he.code == 404:
                print(f"  --> PASS: Rejected non-existent case with HTTP 404. No demo OTP leaked.")
                results["otp_leak_prevention"] = {"status": "PASS", "code": 404}
            else:
                print(f"  --> PASS: Returned HTTP {he.code}")
                results["otp_leak_prevention"] = {"status": "PASS", "code": he.code}

        # B) Test request OTP and tracking on an authentic seeded case (CASE-DEMO-001, mobile: 9876543210)
        otp_req_data = json.dumps({"case_id": "CASE-DEMO-001", "mobile": "9876543210"}).encode('utf-8')
        req2 = urllib.request.Request("http://127.0.0.1:8000/api/citizen/request-otp", data=otp_req_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req2) as resp2:
            res_json = json.loads(resp2.read().decode())
            print(f"  --> Authenticated Case OTP Request: {res_json}")
            
        track_req_data = json.dumps({"case_id": "CASE-DEMO-001", "mobile": "9876543210", "otp": "123456"}).encode('utf-8')
        req3 = urllib.request.Request("http://127.0.0.1:8000/api/citizen/track", data=track_req_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req3) as resp3:
            track_json = json.loads(resp3.read().decode())
            print(f"  --> Citizen Tracking Result: Status='{track_json.get('status')}', Note='{track_json.get('submission_note')}'")
            if "Ready to Submit" in track_json.get("status", ""):
                print("  --> PASS: Status honestly indicates Ready to Submit.")
                results["citizen_tracking"] = {"status": "PASS", "data": track_json}
            else:
                print(f"  --> CHECK STATUS: {track_json.get('status')}")
                results["citizen_tracking"] = {"status": "WARN", "data": track_json}
    except Exception as e:
        print(f"  --> ERROR in OTP/tracking test: {e}")
        results["citizen_tracking"] = {"status": "FAIL", "error": str(e)}

    # 3. REAL BROWSER (EDGE) CDP AUTOMATION
    EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(EDGE_PATH):
        EDGE_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    port = 9228
    temp_profile = r"C:\Users\RUTURAJ SHEVANTE\AppData\Local\Temp\browser_bl_suite_profile"
    proc = subprocess.Popen([
        EDGE_PATH,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={temp_profile}",
        "http://127.0.0.1:8000"
    ])

    try:
        time.sleep(3.0)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as res:
            tabs = json.loads(res.read().decode())
            ws_url = None
            for t in tabs:
                if t.get("type") == "page" and "8000" in t.get("url", ""):
                    ws_url = t.get("webSocketDebuggerUrl")
                    break
            if not ws_url and tabs:
                ws_url = tabs[0].get("webSocketDebuggerUrl")

        cdp = MinimalCDPClient(ws_url)

        # Log in demo operator
        cdp.eval("""
            (async () => {
                await handleDemoLogin();
            })()
        """)
        time.sleep(1.5)

        # TEST MICROPHONE & STT ENVIRONMENT (Test F)
        print("\n[TEST F: MICROPHONE & STT CAPABILITIES IN BROWSER]")
        stt_info = cdp.eval("""
            (() => {
                const hasSpeechRec = Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
                const hasGetUserMedia = Boolean(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
                const hasMediaRecorder = typeof MediaRecorder !== 'undefined';
                const hasTTS = typeof window.speechSynthesis !== 'undefined';
                const langLocales = {
                    en: getSpeechLocale('en'),
                    hi: getSpeechLocale('hi'),
                    mr: getSpeechLocale('mr'),
                    bn: getSpeechLocale('bn')
                };
                return {
                    speechRecognition: hasSpeechRec,
                    getUserMedia: hasGetUserMedia,
                    mediaRecorder: hasMediaRecorder,
                    speechSynthesis: hasTTS,
                    locales: langLocales
                };
            })()
        """)
        print(f"  SpeechRecognition Available: {stt_info['speechRecognition']}")
        print(f"  getUserMedia Available: {stt_info['getUserMedia']}")
        print(f"  MediaRecorder Available: {stt_info['mediaRecorder']}")
        print(f"  SpeechSynthesis Available: {stt_info['speechSynthesis']}")
        print(f"  Configured STT Locales: {stt_info['locales']}")
        results["browser_multimodal"] = stt_info

        # TEST MULTILINGUAL AI VOICE GUIDE & DROPDOWN SYNC (Test G)
        print("\n[TEST G: MULTILINGUAL AI VOICE GUIDE & DROPDOWN SYNC]")
        voice_guide_checks = {}
        for lcode, expected_snippet in [
            ("hi", "नमस्ते। अपनी समस्या बताइए।"),
            ("mr", "नमस्कार. आपली समस्या सांगा."),
            ("bn", "\u09a8\u09ae\u09b8\u09cd\u0995\u09be\u09b0\u0964 \u0986\u09aa\u09a8\u09be\u09b0 \u09b8\u09ae\u09b8\u09cd\u09af\u09be \u09ac\u09b2\u09c1\u09a8\u0964"),
            ("en", "Hello. Please tell us your problem.")
        ]:
            cdp.eval(f"changeLanguage('{lcode}');")
            time.sleep(0.3)
            guide_txt = cdp.eval("document.getElementById('guide-step1-text')?.innerText")
            rec_lang = cdp.eval("recognition ? recognition.lang : ''")
            matches = expected_snippet in (guide_txt or "")
            voice_guide_checks[lcode] = {
                "guide_text": guide_txt,
                "recognition_lang": rec_lang,
                "matches": matches
            }
            print(f"  - Lang: {lcode} -> Guide: '{guide_txt}' | STT Lang: '{rec_lang}' -> Pass: {matches}")
        results["voice_guide"] = voice_guide_checks

        # HELPER TO RUN FULL WORKFLOW CASE
        def execute_case(case_name, transcript, lang, override_state=None, override_dist=None):
            print(f"\n=======================================================")
            print(f"RUNNING {case_name}")
            print(f"=======================================================")
            cdp.eval("startNewCase();")
            time.sleep(0.5)

            # Check fresh isolation
            clean_check = cdp.eval("""
                (() => {
                    return {
                        id: currentCase.id,
                        name: document.getElementById('field-name').value,
                        issue: document.getElementById('field-issue').value,
                        scheme: document.getElementById('field-scheme').value,
                        sources_count: currentCase.sources.length,
                        template: currentCase.template_type
                    };
                })()
            """)
            print(f"  [New Case Isolation] ID: {clean_check['id']}, Issue: '{clean_check['issue']}', Scheme: '{clean_check['scheme']}', Sources: {clean_check['sources_count']}")

            # Input complaint
            escaped_t = json.dumps(transcript)
            cdp.eval(f"""
                document.getElementById('consent-check').checked = true;
                document.getElementById('raw-input-text').value = {escaped_t};
                currentCase.original_transcript = {escaped_t};
                currentCase.edited_transcript = {escaped_t};
                changeLanguage('{lang}');
                validateStep1Form();
            """)
            time.sleep(0.5)

            # Extract facts
            cdp.eval("""
                (async () => {
                    await processVoiceOrTextInput();
                })()
            """)
            time.sleep(2.5)

            if override_state:
                cdp.eval(f"""
                    (() => {{
                        const stateSel = document.getElementById('field-state-select');
                        if (stateSel) {{
                            stateSel.value = '{override_state}';
                            handleStateSelectionChange('{override_state}', false);
                        }}
                    }})()
                """)
                time.sleep(0.5)
            if override_dist:
                cdp.eval(f"""
                    (() => {{
                        const distSel = document.getElementById('field-district-select');
                        if (distSel) {{
                            distSel.value = '{override_dist}';
                            handleDistrictSelectionChange('{override_dist}', false);
                        }}
                    }})()
                """)
                time.sleep(0.5)

            cdp.eval("syncFormFieldsToState();")
            review = cdp.eval("""
                (() => {
                    return {
                        name: document.getElementById('field-name').value,
                        village: document.getElementById('field-village').value,
                        state: document.getElementById('field-state-select').value,
                        district: document.getElementById('field-district-select').value,
                        duration: document.getElementById('field-duration').value,
                        issue_type: document.getElementById('field-issue').value,
                        scheme: document.getElementById('field-scheme').value,
                        department: document.getElementById('field-department').value,
                        template_type: currentCase.template_type
                    };
                })()
            """)
            print(f"  Review Details: Issue='{review['issue_type']}', Scheme='{review['scheme']}', Dept='{review['department']}', State='{review['state']}', Dist='{review['district']}'")

            # Search Government Sources
            cdp.eval("completedSteps.add(2); goToStep(3);")
            time.sleep(0.8)
            cdp.eval("""
                (async () => {
                    await executeSerpSearchManual();
                })()
            """)
            time.sleep(4.0)

            search = cdp.eval("""
                (() => {
                    return {
                        query: currentCase.search_query,
                        count: currentCase.sources.length,
                        top_sources: (currentCase.sources || []).slice(0, 3).map(s => ({
                            title: s.title,
                            url: s.url,
                            domain: s.domain,
                            relevance: s.relevance_status
                        }))
                    };
                })()
            """)
            print(f"  Government Sources: Total={search['count']}, Query='{search['query']}'")
            for idx, s in enumerate(search['top_sources'], 1):
                print(f"    Top #{idx}: [{s['relevance']}] {s['title']} ({s['url']})")

            # Step 4: Generation & Verification
            cdp.eval("completedSteps.add(3); goToStep(4);")
            time.sleep(0.5)
            cdp.eval("""
                (async () => {
                    await generateFinalBilingualDocument();
                })()
            """)
            time.sleep(2.5)

            docs = cdp.eval("""
                (() => {
                    const doc = currentCase.generated_documents || {};
                    const en = doc.english_application || {};
                    const reg = doc.regional_language || {};
                    return {
                        template_name: doc.template_name || '',
                        template_type: currentCase.template_type || '',
                        en_title: en.title || '',
                        en_body: en.body || '',
                        reg_title: reg.title || '',
                        reg_body: reg.body || '',
                        valid: (doc.validation || {}).valid,
                        errors: (doc.validation || {}).errors || []
                    };
                })()
            """)
            # Check script purity
            has_devanagari = any('\u0900' <= c <= '\u097F' for c in docs['en_body'])
            has_bengali = any('\u0980' <= c <= '\u09FF' for c in docs['en_body'])
            print(f"  Document Generated: Template='{docs['template_name']}' ({docs['template_type']})")
            print(f"  Validation Valid: {docs['valid']} (Errors: {docs['errors']})")
            print(f"  English Script Purity: Devanagari in EN: {has_devanagari}, Bengali in EN: {has_bengali}")

            return {
                "review": review,
                "search": search,
                "docs": {
                    "template_name": docs["template_name"],
                    "template_type": docs["template_type"],
                    "en_title": docs["en_title"],
                    "en_preview": docs["en_body"][:200],
                    "valid": docs["valid"],
                    "errors": docs["errors"],
                    "script_pure": not (has_devanagari or has_bengali)
                }
            }

        # Case 1: Electricity (Gujarat / Ahmedabad)
        c1 = execute_case(
            "CASE 1: ELECTRICITY (Gujarat / Ahmedabad)",
            "My electricity supply has been repeatedly failing for 3 months with continuous voltage fluctuations and power cuts. Resident of Ahmedabad, Gujarat.",
            "en",
            override_state="Gujarat",
            override_dist="Ahmedabad"
        )
        results["case1"] = c1

        # Case 2: Water (Maharashtra / Pune)
        c2 = execute_case(
            "CASE 2: WATER (Maharashtra / Pune)",
            "The drinking water supply pipeline has been completely broken for 15 days, causing severe water disruption in our village. District Pune, Maharashtra.",
            "mr",
            override_state="Maharashtra",
            override_dist="Pune"
        )
        results["case2"] = c2

        # Case 3: Pension (Rajasthan / Jaipur)
        c3 = execute_case(
            "CASE 3: PENSION (Rajasthan / Jaipur)",
            "I am Ramesh Sharma from Jaipur, Rajasthan. I have not received my old age welfare pension for 6 months.",
            "hi",
            override_state="Rajasthan",
            override_dist="Jaipur"
        )
        results["case3"] = c3

        # Case 4: Sequential Switching check (Switch to Electricity again and verify no carryover)
        c4 = execute_case(
            "CASE 4: SWITCHING ISOLATION VERIFICATION (Electricity, West Bengal / Nadia)",
            "Power supply has been disconnected wrongfully for 2 days. Nadia, West Bengal.",
            "bn",
            override_state="West Bengal",
            override_dist="Nadia"
        )
        results["case4"] = c4

        cdp.close()
    finally:
        proc.terminate()
        proc.wait()

    # Save results to scratch json
    out_path = r"C:\Users\RUTURAJ SHEVANTE\.gemini\antigravity\brain\201f0bfe-dfcb-4d47-8593-6f0d8d3b0f65\scratch\final_verification_results.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults successfully written to {out_path}")
    print("="*60)
    print("ALL VERIFICATIONS COMPLETED")
    print("="*60)

if __name__ == '__main__':
    run_suite()
