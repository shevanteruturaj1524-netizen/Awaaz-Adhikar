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

def run_suite():
    print("="*60)
    print("RUNNING TARGETED AUDIT SUITE IN STRICT PRIORITY ORDER")
    print("="*60)

    EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(EDGE_PATH):
        EDGE_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    port = 9230
    temp_profile = r"C:\Users\RUTURAJ SHEVANTE\AppData\Local\Temp\browser_priority_suite_profile"
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

        def execute_workflow(test_label, citizen_name, raw_transcript, state, district, lang="hi"):
            print(f"\n--- {test_label} ---")
            cdp.eval("startNewCase();")
            time.sleep(0.4)

            # Check clean initial state
            fresh_check = cdp.eval("""
                (() => {
                    return {
                        id: currentCase.id,
                        name: document.getElementById('field-name').value,
                        issue: document.getElementById('field-issue').value,
                        scheme: document.getElementById('field-scheme').value,
                        sources: currentCase.sources.length,
                        raw: document.getElementById('raw-input-text').value
                    };
                })()
            """)
            print(f"  [Fresh Start] Case: {fresh_check['id']}, Initial Name: '{fresh_check['name']}', Initial Issue: '{fresh_check['issue']}', Initial Sources: {fresh_check['sources']}")

            # Input complaint & citizen name
            escaped_t = json.dumps(raw_transcript)
            escaped_name = json.dumps(citizen_name)
            cdp.eval(f"""
                document.getElementById('consent-check').checked = true;
                document.getElementById('raw-input-text').value = {escaped_t};
                currentCase.original_transcript = {escaped_t};
                currentCase.edited_transcript = {escaped_t};
                changeLanguage('{lang}');
                validateStep1Form();
            """)
            time.sleep(0.3)

            # Extract facts
            cdp.eval("""
                (async () => {
                    await processVoiceOrTextInput();
                })()
            """)
            time.sleep(2.5)

            # Set verified name & location
            cdp.eval(f"""
                (() => {{
                    document.getElementById('field-name').value = {escaped_name};
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

            review = cdp.eval("""
                (() => {
                    return {
                        name: document.getElementById('field-name').value,
                        village: document.getElementById('field-village').value,
                        state: document.getElementById('field-state-select').value,
                        district: document.getElementById('field-district-select').value,
                        duration: document.getElementById('field-duration').value,
                        issue: document.getElementById('field-issue').value,
                        scheme: document.getElementById('field-scheme').value,
                        dept: document.getElementById('field-department').value,
                        template: currentCase.template_type
                    };
                })()
            """)
            print(f"  [Review Details] Name: '{review['name']}', Issue: '{review['issue']}', Scheme: '{review['scheme']}', Dept: '{review['dept']}', Template: '{review['template']}'")

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
                        sources: (currentCase.sources || []).slice(0, 3).map(s => ({
                            title: s.title,
                            url: s.url,
                            domain: s.domain,
                            relevance: s.relevance_status
                        }))
                    };
                })()
            """)
            print(f"  [Search Results] Total: {search['count']}, Query: '{search['query']}'")
            unrelated_in_top = False
            for idx, s in enumerate(search['sources'], 1):
                print(f"    Top #{idx}: [{s['relevance']}] {s['title']} ({s['url']})")
                if any(bad in s['domain'] for bad in ["ssc.gov.in", "ksb.gov.in", "gem.gov.in"]):
                    unrelated_in_top = True

            # Advance to Step 4 & Generate Document
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
                        reg_body: reg.body || '',
                        valid: (doc.validation || {}).valid,
                        errors: (doc.validation || {}).errors || []
                    };
                })()
            """)
            has_devanagari_in_en = any('\u0900' <= c <= '\u097F' for c in docs['en_body'])
            has_bengali_in_en = any('\u0980' <= c <= '\u09FF' for c in docs['en_body'])
            name_in_en = citizen_name in docs['en_body'] or citizen_name.split()[0] in docs['en_body']

            print(f"  [Generated Application] Template: '{docs['template_name']}', Valid: {docs['valid']}")
            print(f"    Citizen Name in English Doc: {name_in_en}")
            print(f"    Script Cleanliness: Devanagari in EN: {has_devanagari_in_en}, Bengali in EN: {has_bengali_in_en}")

            return {
                "fresh_check": fresh_check,
                "review": review,
                "search": search,
                "docs": docs,
                "name_in_en": name_in_en,
                "unrelated_in_top": unrelated_in_top,
                "script_clean": not (has_devanagari_in_en or has_bengali_in_en)
            }

        # 1. Electricity Case
        elec_res = execute_workflow(
            "1. ELECTRICITY CASE (Ahmedabad, Gujarat)",
            "Ramesh Patel",
            "My electricity supply has been repeatedly failing for 3 months with voltage fluctuations and power cuts. Resident of Ahmedabad, Gujarat.",
            "Gujarat",
            "Ahmedabad"
        )

        # 2. Ration / PDS Case
        ration_res = execute_workflow(
            "2. RATION / PDS CASE (Jaipur, Rajasthan)",
            "Suresh Sharma",
            "The fair price shop dealer has not distributed ration food grain quota for 2 months. Resident of Jaipur, Rajasthan.",
            "Rajasthan",
            "Jaipur"
        )

        # 3. Water -> Electricity cross-case isolation
        print("\n" + "="*50)
        print("3. WATER -> ELECTRICITY CROSS-CASE ISOLATION")
        print("="*50)
        # First execute Water case
        water_res = execute_workflow(
            "Step 3a: WATER CASE (Pune, Maharashtra)",
            "Vitthal Kamble",
            "Drinking water pipeline has been completely broken for 15 days in our village. Pune, Maharashtra.",
            "Maharashtra",
            "Pune"
        )
        # Immediately start fresh Electricity case and verify zero carryover
        elec_after_water = execute_workflow(
            "Step 3b: FRESH ELECTRICITY CASE (Ahmedabad, Gujarat) IMMEDIATELY AFTER WATER",
            "Nitin Desai",
            "Repeated electricity failure and power cuts for 1 month. Ahmedabad, Gujarat.",
            "Gujarat",
            "Ahmedabad"
        )
        no_water_in_elec = (
            "water" not in elec_after_water["review"]["issue"].lower() and
            "water" not in elec_after_water["docs"]["en_body"].lower() and
            "Vitthal" not in elec_after_water["docs"]["en_body"] and
            "Pune" not in elec_after_water["docs"]["en_body"]
        )
        print(f"  --> Water data completely absent from Electricity application: {no_water_in_elec}")

        # 4. Pension -> Water cross-case isolation
        print("\n" + "="*50)
        print("4. PENSION -> WATER CROSS-CASE ISOLATION")
        print("="*50)
        pension_res = execute_workflow(
            "Step 4a: PENSION CASE (Jaipur, Rajasthan)",
            "Kailash Meena",
            "Old age welfare pension has not been credited for 6 months. Jaipur, Rajasthan.",
            "Rajasthan",
            "Jaipur"
        )
        water_after_pension = execute_workflow(
            "Step 4b: FRESH WATER CASE (Pune, Maharashtra) IMMEDIATELY AFTER PENSION",
            "Sunita Patil",
            "Village drinking water supply pipeline disrupted for 20 days. Pune, Maharashtra.",
            "Maharashtra",
            "Pune"
        )
        no_pension_in_water = (
            "pension" not in water_after_pension["review"]["issue"].lower() and
            "pension" not in water_after_pension["docs"]["en_body"].lower() and
            "Kailash" not in water_after_pension["docs"]["en_body"] and
            "Jaipur" not in water_after_pension["docs"]["en_body"]
        )
        print(f"  --> Pension data completely absent from Water application: {no_pension_in_water}")

        # 5. Check Submit on Official Portal action
        print("\n" + "="*50)
        print("5. SUBMISSION ACTION: 'Submit on Official Portal'")
        print("="*50)
        btn_top_text = cdp.eval("document.getElementById('btn-submit-application-top')?.innerText")
        btn_bottom_text = cdp.eval("document.getElementById('btn-submit-application-bottom')?.innerText")
        print(f"  Top Button Text: '{btn_top_text}'")
        print(f"  Bottom Button Text: '{btn_bottom_text}'")
        is_official_portal_label = "Submit on Official Portal" in (btn_top_text or "") and "Submit on Official Portal" in (btn_bottom_text or "")
        print(f"  Button label is strictly 'Submit on Official Portal': {is_official_portal_label}")

        cdp.eval("submitApplicationAction();")
        time.sleep(0.5)
        modal_info = cdp.eval("""
            (() => {
                const modal = document.getElementById('submit-guidance-modal');
                const link = document.getElementById('submit-portal-external-link');
                return {
                    visible: modal && !modal.classList.contains('hidden'),
                    statusText: modal ? modal.querySelector('.text-amber-800')?.innerText : '',
                    portalHref: link ? link.href : '',
                    portalLabel: link ? link.innerText : ''
                };
            })()
        """)
        print(f"  Modal Visible: {modal_info['visible']}")
        print(f"  Honest Status: '{modal_info['statusText']}'")
        print(f"  Official Portal Link: {modal_info['portalHref']} ('{modal_info['portalLabel']}')")

        cdp.close()
    finally:
        proc.terminate()
        proc.wait()

    print("\n" + "="*60)
    print("ALL PRIORITY AUDIT TESTS FINISHED")
    print("="*60)

if __name__ == '__main__':
    run_suite()
