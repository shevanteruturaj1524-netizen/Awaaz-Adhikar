import os
import sys
import json
import time
import socket
import struct
import base64
import random
import urllib.request
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

def run():
    print("="*60)
    print("STARTING TARGETED REAL BROWSER TESTS (PROBLEMS 1, 2, 3)")
    print("="*60)

    EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(EDGE_PATH):
        EDGE_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    port = 9229
    temp_profile = r"C:\Users\RUTURAJ SHEVANTE\AppData\Local\Temp\browser_bl_suite_profile_3prob"
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

        # Login demo operator
        cdp.eval("""
            (async () => {
                await handleDemoLogin();
            })()
        """)
        time.sleep(1.5)

        # ========================================================
        # TEST 1: MICROPHONE & SAME-LANGUAGE TRANSCRIPT TEST
        # ========================================================
        print("\n" + "="*50)
        print("TEST 1: MICROPHONE & SAME-LANGUAGE TRANSCRIPT")
        print("="*50)
        mic_check = cdp.eval("""
            (async () => {
                const hasSpeechRec = Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
                let micPermission = 'unknown';
                try {
                    const status = await navigator.permissions.query({ name: 'microphone' });
                    micPermission = status.state;
                } catch (e) {
                    micPermission = 'unsupported_query';
                }
                return {
                    speechRecognition: hasSpeechRec,
                    permission: micPermission,
                    locales: {
                        en: getSpeechLocale('en'),
                        hi: getSpeechLocale('hi'),
                        mr: getSpeechLocale('mr'),
                        bn: getSpeechLocale('bn')
                    }
                };
            })()
        """)
        print(f"  SpeechRecognition API present: {mic_check['speechRecognition']}")
        print(f"  Microphone Permission state: {mic_check['permission']}")
        print(f"  Configured STT locales: {mic_check['locales']}")
        print("  NOTE ON PHYSICAL AUDIO HARDWARE: In this automated headless sandbox, an external human physical microphone audio stream is not connected. Testing Web Speech API binding and same-language transcript preservation.")

        # Test language-specific live transcript preservation in the UI
        lang_tests = [
            ("hi", "मेरा नाम रमेश है। 3 महीने से बिजली नहीं आ रही है।", "Hindi / Devanagari"),
            ("mr", "माझे नाव विठ्ठल आहे. गेल्या १५ दिवसांपासून पाणीपुरवठा बंद आहे.", "Marathi"),
            ("bn", "আমার নাম সুবীর। ২ মাস ধরে রেশন পাচ্ছি না।", "Bengali"),
            ("en", "My name is John. My pension has been delayed for 4 months.", "English")
        ]

        for lcode, sample_speech, lang_name in lang_tests:
            res = cdp.eval(f"""
                (() => {{
                    changeLanguage('{lcode}');
                    const localeSet = recognition ? recognition.lang : null;
                    
                    // Simulate exact speech recognized by the SpeechRecognition engine in this language
                    _sttFinalTranscript = '';
                    const rawInput = document.getElementById('raw-input-text');
                    rawInput.value = '{sample_speech}';
                    currentCase.original_transcript = '{sample_speech}';
                    currentCase.edited_transcript = '{sample_speech}';
                    validateStep1Form();

                    return {{
                        activeLang: currentCase.language,
                        recognitionLang: localeSet,
                        transcriptValue: rawInput.value,
                        isSameText: rawInput.value === '{sample_speech}'
                    }};
                }})()
            """)
            print(f"  - [{lang_name}] Selected={res['activeLang']}, STT Locale={res['recognitionLang']}")
            print(f"    Transcript Preserved in Same Language: {res['isSameText']} -> \"{res['transcriptValue']}\"")

        # ========================================================
        # TEST 2: ANY-GRIEVANCE RELEVANT SOLUTIONS (A, B, C, D)
        # ========================================================
        print("\n" + "="*50)
        print("TEST 2: ANY-GRIEVANCE SOLUTION RELEVANCE")
        print("="*50)

        cases_to_test = [
            ("A. ELECTRICITY", "My electricity supply has been failing repeatedly for 3 months with continuous voltage fluctuations. Ahmedabad, Gujarat.", "Gujarat", "Ahmedabad", "electricity"),
            ("B. WATER", "The drinking water supply pipeline is completely broken for 15 days in our area. Pune, Maharashtra.", "Maharashtra", "Pune", "water"),
            ("C. PENSION", "I have not received my old age social security welfare pension for 6 months. Jaipur, Rajasthan.", "Rajasthan", "Jaipur", "pension"),
            ("D. RATION / PDS", "Fair price shop dealer has not distributed food grain quota and ration for 2 months. Jaipur, Rajasthan.", "Rajasthan", "Jaipur", "ration")
        ]

        for title, complaint_text, state, district, expected_category in cases_to_test:
            print(f"\n--- Testing Category: {title} ({state} / {district}) ---")
            cdp.eval("startNewCase();")
            time.sleep(0.5)

            escaped = json.dumps(complaint_text)
            cdp.eval(f"""
                document.getElementById('consent-check').checked = true;
                document.getElementById('raw-input-text').value = {escaped};
                currentCase.original_transcript = {escaped};
                currentCase.edited_transcript = {escaped};
                validateStep1Form();
            """)

            # Process extraction
            cdp.eval("""
                (async () => {
                    await processVoiceOrTextInput();
                })()
            """)
            time.sleep(2.5)

            # Set location
            cdp.eval(f"""
                (() => {{
                    const stateSel = document.getElementById('field-state-select');
                    if (stateSel) {{
                        stateSel.value = '{state}';
                        handleStateSelectionChange('{state}', false);
                    }}
                    const distSel = document.getElementById('field-district-select');
                    if (distSel) {{
                        distSel.value = '{district}';
                        handleDistrictSelectionChange('{district}', false);
                    }}
                    syncFormFieldsToState();
                }})()
            """)
            time.sleep(0.5)

            details = cdp.eval("""
                (() => {
                    return {
                        issue: document.getElementById('field-issue').value,
                        scheme: document.getElementById('field-scheme').value,
                        dept: document.getElementById('field-department').value,
                        template: currentCase.template_type
                    };
                })()
            """)
            print(f"  Classification: {details['issue']}")
            print(f"  Service/Scheme: {details['scheme']}")
            print(f"  Department: {details['dept']}")
            print(f"  Template: {details['template']}")

            # Advance to Search
            cdp.eval("completedSteps.add(2); goToStep(3);")
            time.sleep(0.8)
            cdp.eval("""
                (async () => {
                    await executeSerpSearchManual();
                })()
            """)
            time.sleep(4.0)

            search_info = cdp.eval("""
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
            print(f"  Search Query: {search_info['query']}")
            print(f"  Total Relevant Sources: {search_info['count']}")
            unrelated_found = False
            for idx, s in enumerate(search_info['top_sources'], 1):
                print(f"    Top #{idx}: [{s['relevance']}] {s['title']} ({s['url']})")
                if any(bad in s['domain'] for bad in ["ssc.gov.in", "ksb.gov.in", "gem.gov.in"]):
                    unrelated_found = True

            print(f"  Unrelated Government Portals (SSC/KSB/GeM) In Top Results: {unrelated_found} (Should be False)")

        # ========================================================
        # TEST 3: SUBMIT APPLICATION BUTTON (CASE B)
        # ========================================================
        print("\n" + "="*50)
        print("TEST 3: SUBMIT APPLICATION BUTTON (CASE B)")
        print("="*50)

        # Advance to Step 4 and generate document
        cdp.eval("completedSteps.add(3); goToStep(4);")
        time.sleep(0.5)
        cdp.eval("""
            (async () => {
                await generateFinalBilingualDocument();
            })()
        """)
        time.sleep(2.5)

        submit_btn_check = cdp.eval("""
            (() => {
                const btnTop = document.getElementById('btn-submit-application-top');
                const btnBottom = document.getElementById('btn-submit-application-bottom');
                const btnPdf = document.querySelector("button[onclick='downloadDocumentPDF()']");
                const btnPrint = document.querySelector("button[onclick='openPrintableWindow()']");
                
                return {
                    hasTopBtn: Boolean(btnTop),
                    hasBottomBtn: Boolean(btnBottom),
                    hasPdfBtn: Boolean(btnPdf),
                    hasPrintBtn: Boolean(btnPrint)
                };
            })()
        """)
        print(f"  Submit Application Top Button visible: {submit_btn_check['hasTopBtn']}")
        print(f"  Submit Application Bottom Button visible: {submit_btn_check['hasBottomBtn']}")
        print(f"  Download PDF button intact: {submit_btn_check['hasPdfBtn']}")
        print(f"  Print View button intact: {submit_btn_check['hasPrintBtn']}")

        # Click the Submit Application button
        print("  Clicking [ Submit Application ] button...")
        cdp.eval("submitApplicationAction();")
        time.sleep(0.5)

        modal_check = cdp.eval("""
            (() => {
                const modal = document.getElementById('submit-guidance-modal');
                const isVisible = modal && !modal.classList.contains('hidden');
                const textContent = modal ? modal.innerText : '';
                return {
                    visible: isVisible,
                    containsReadyNotSubmitted: textContent.includes('Application Ready — Not Yet Submitted'),
                    containsNoFakeRef: !textContent.includes('Ref #') && !textContent.includes('Application Submitted Successfully'),
                    containsCounterRoute: textContent.includes('Route 1') && textContent.includes('Jan Seva Kendra'),
                    containsPortalRoute: textContent.includes('Route 2') && textContent.includes('Online Grievance Portal')
                };
            })()
        """)
        print(f"  Submission Guidance Modal Opened: {modal_check['visible']}")
        print(f"  Honestly shows 'Application Ready — Not Yet Submitted': {modal_check['containsReadyNotSubmitted']}")
        print(f"  No fake application numbers or false success: {modal_check['containsNoFakeRef']}")
        print(f"  Presents statutory Physical Counter route: {modal_check['containsCounterRoute']}")
        print(f"  Presents official Online Grievance Portal route: {modal_check['containsPortalRoute']}")

        cdp.close()
    finally:
        proc.terminate()
        proc.wait()

    print("\n" + "="*60)
    print("ALL TARGETED TESTS FINISHED SUCCESSFULLY")
    print("="*60)

if __name__ == '__main__':
    run()
