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
    EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(EDGE_PATH):
        EDGE_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    port = 9227
    proc = subprocess.Popen([
        EDGE_PATH,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--no-default-browser-check",
        "--user-data-dir=C:\\Users\\RUTURAJ SHEVANTE\\AppData\\Local\\Temp\\browser_bl_test_2",
        "http://127.0.0.1:8000"
    ])

    try:
        time.sleep(2.5)
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

        # Login as demo operator
        cdp.eval("""
            (async () => {
                await handleDemoLogin();
            })()
        """)
        time.sleep(1.5)

        # Helper to run a case through the frontend
        def run_case_test(name, transcript, lang, override_state=None, override_dist=None):
            print(f"\n=======================================================")
            print(f"RUNNING {name}")
            print(f"=======================================================")
            
            # Start New Case
            cdp.eval("startNewCase();")
            time.sleep(0.5)

            # Check isolation immediately
            init_state = cdp.eval("""
                (() => {
                    return {
                        id: currentCase.id,
                        name: document.getElementById('field-name').value,
                        issue: document.getElementById('field-issue').value,
                        scheme: document.getElementById('field-scheme').value,
                        department: document.getElementById('field-department').value,
                        sources_count: currentCase.sources.length,
                        tmpl: currentCase.template_type,
                        raw_input: document.getElementById('raw-input-text').value
                    };
                })()
            """)
            print(f"  [Isolation on Start] Case ID: {init_state['id']}")
            print(f"    - Clean fields: issue='{init_state['issue']}', scheme='{init_state['scheme']}', sources={init_state['sources_count']}")

            # Enter transcript & consent
            escaped_transcript = json.dumps(transcript)
            cdp.eval(f"""
                document.getElementById('consent-check').checked = true;
                document.getElementById('raw-input-text').value = {escaped_transcript};
                currentCase.original_transcript = {escaped_transcript};
                currentCase.edited_transcript = {escaped_transcript};
                changeLanguage('{lang}');
                validateStep1Form();
            """)
            time.sleep(0.5)

            # Trigger fact extraction using processVoiceOrTextInput()
            cdp.eval("""
                (async () => {
                    await processVoiceOrTextInput();
                })()
            """)
            time.sleep(2.5)

            # If override state / dist provided, set them and trigger change
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

            # Sync form fields
            cdp.eval("syncFormFieldsToState();")

            # Get Step 2 Review Details values
            review_details = cdp.eval("""
                (() => {
                    return {
                        citizen_name: document.getElementById('field-name').value,
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
            print(f"  Review Details:")
            for k, v in review_details.items():
                print(f"    - {k}: {v}")

            # Advance to Step 3: Search Government Sources
            cdp.eval("""
                completedSteps.add(2);
                goToStep(3);
            """)
            time.sleep(1.0)

            # Trigger search
            cdp.eval("""
                (async () => {
                    await executeSerpSearchManual();
                })()
            """)
            time.sleep(4.0)

            search_details = cdp.eval("""
                (() => {
                    return {
                        query: currentCase.search_query,
                        sources_count: currentCase.sources.length,
                        sources: (currentCase.sources || []).slice(0, 3).map(s => ({
                            title: s.title,
                            url: s.url,
                            domain: s.domain,
                            relevance: s.relevance_status
                        }))
                    };
                })()
            """)
            print(f"  Government Sources Search:")
            print(f"    Query: {search_details['query']}")
            print(f"    Total Sources: {search_details['sources_count']}")
            for idx, s in enumerate(search_details['sources'], 1):
                print(f"    Top #{idx}: [{s['relevance']}] {s['title']} ({s['url']})")

            # Advance to Step 4: Application generation
            cdp.eval("""
                completedSteps.add(3);
                goToStep(4);
            """)
            time.sleep(0.5)

            # Generate final document
            cdp.eval("""
                (async () => {
                    await generateFinalBilingualDocument();
                })()
            """)
            time.sleep(2.5)

            doc_details = cdp.eval("""
                (() => {
                    const doc = currentCase.generated_documents || {};
                    const en = doc.english_application || {};
                    const reg = doc.regional_language || {};
                    return {
                        template_name: doc.template_name || '',
                        template_type: currentCase.template_type || '',
                        en_title: en.title || '',
                        en_body: (en.body || '').substring(0, 300),
                        reg_title: reg.title || '',
                        reg_body: (reg.body || '').substring(0, 300),
                        valid: (doc.validation || {}).valid,
                        validation_errors: (doc.validation || {}).errors || []
                    };
                })()
            """)
            print(f"  Generated Document:")
            print(f"    Selected Template: {doc_details['template_name']} ({doc_details['template_type']})")
            print(f"    English Title: {doc_details['en_title']}")
            print(f"    English Body Preview:\n{doc_details['en_body'][:250]}...")
            print(f"    Validation Valid: {doc_details['valid']}")
            if doc_details['validation_errors']:
                print(f"    Validation Errors: {doc_details['validation_errors']}")

            return review_details, search_details, doc_details

        # Run Case 1: Electricity (Gujarat / Ahmedabad)
        res1 = run_case_test(
            "CASE 1: ELECTRICITY (Gujarat / Ahmedabad)",
            "My electricity supply has been repeatedly failing for 3 months with continuous voltage fluctuations and power cuts. Resident of Ahmedabad, Gujarat.",
            "en",
            override_state="Gujarat",
            override_dist="Ahmedabad"
        )

        # Run Case 2: Water (Maharashtra / Pune)
        res2 = run_case_test(
            "CASE 2: WATER (Maharashtra / Pune)",
            "The drinking water supply pipeline has been completely broken for 15 days, causing severe water disruption in our village. District Pune, Maharashtra.",
            "en",
            override_state="Maharashtra",
            override_dist="Pune"
        )

        # Run Case 3: Pension (Rajasthan / Jaipur)
        res3 = run_case_test(
            "CASE 3: PENSION (Rajasthan / Jaipur)",
            "I am Ramesh Sharma from Jaipur, Rajasthan. I have not received my old age welfare pension for 6 months.",
            "en",
            override_state="Rajasthan",
            override_dist="Jaipur"
        )

        cdp.close()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    run()
