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
        self.sock = socket.create_connection((host, int(port)), timeout=15)
        
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

def run_tests():
    print("=" * 70)
    print("AWAAZ ADHIKAR - REAL BROWSER STEP-GATING VERIFICATION")
    print("=" * 70)
    
    EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(EDGE_PATH):
        EDGE_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    port = 9225
    proc = subprocess.Popen([
        EDGE_PATH,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--no-default-browser-check",
        "--user-data-dir=C:\\Users\\RUTURAJ SHEVANTE\\AppData\\Local\\Temp\\gating_browser_profile",
        "http://127.0.0.1:8000"
    ])

    passed_count = 0
    failed_count = 0

    def assert_check(name, condition, evidence=""):
        nonlocal passed_count, failed_count
        if condition:
            passed_count += 1
            print(f"  [PASS] {name}")
            if evidence:
                print(f"         Evidence: {evidence}")
        else:
            failed_count += 1
            print(f"  [FAIL] {name}")
            if evidence:
                print(f"         Failure detail: {evidence}")

    try:
        time.sleep(2.5)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as res:
            tabs = json.loads(res.read().decode())
        app_tab = next(t for t in tabs if "Awaaz" in t.get("title", "") or "8000" in t.get("url", ""))
        client = MinimalCDPClient(app_tab["webSocketDebuggerUrl"])
        
        # 1. Login as demo operator to access workspace
        client.eval("handleDemoLogin()")
        time.sleep(1.0)
        
        # 2. Start a fresh new case
        client.eval("startNewCase(true)")
        time.sleep(0.5)
        
        print("\n--- TEST 1: Step 2 locked before Step 1 completion ---")
        # Check Step 1 Next button is disabled initially
        btn_disabled = client.eval("document.getElementById('btn-step1-next').disabled")
        assert_check("Step 1 'Review Information' button disabled when input is empty", btn_disabled is True, f"disabled={btn_disabled}")
        
        # Check Step 2 tab style and pointer-events
        tab2_pe = client.eval("document.getElementById('step-tab-2').style.pointerEvents")
        tab2_aria = client.eval("document.getElementById('step-tab-2').getAttribute('aria-disabled')")
        assert_check("Step 2 tab has pointer-events: none", tab2_pe == "none", f"pointerEvents='{tab2_pe}', aria-disabled='{tab2_aria}'")
        
        # Try direct click on Step 2 tab
        client.eval("document.getElementById('step-tab-2').click()")
        cur_step = client.eval("currentStep")
        panel1_hidden = client.eval("document.getElementById('step-panel-1').classList.contains('hidden')")
        panel2_hidden = client.eval("document.getElementById('step-panel-2').classList.contains('hidden')")
        assert_check("Direct click on Step 2 tab does NOT open Step 2", cur_step == 1 and not panel1_hidden and panel2_hidden,
                     f"currentStep={cur_step}, panel1_hidden={panel1_hidden}, panel2_hidden={panel2_hidden}")
        
        # Try programmatic bypass goToStep(2) without Step 1 completion
        client.eval("goToStep(2)")
        cur_step_after_bypass = client.eval("currentStep")
        banner_text = client.eval("document.getElementById('step-gate-banner') ? document.getElementById('step-gate-banner').textContent : ''")
        assert_check("Programmatic goToStep(2) rejected and kept at Step 1", cur_step_after_bypass == 1,
                     f"currentStep={cur_step_after_bypass}, banner='{banner_text}'")

        print("\n--- TEST 2: Step 2 opens after Step 1 completion ---")
        # Populate valid complaint text
        complaint = "मेरा नाम रमेश कुमार है। मुझे 3 महीने से वृद्धावस्था पेंशन नहीं मिली है। मैं रामपुर गाँव, जिला सीतापुर, उत्तर प्रदेश से हूँ।"
        client.eval(f"document.getElementById('raw-input-text').value = {json.dumps(complaint)}")
        client.eval("document.getElementById('raw-input-text').dispatchEvent(new Event('input'))")
        
        btn_now_enabled = client.eval("document.getElementById('btn-step1-next').disabled")
        assert_check("Step 1 Next button enables after valid text entered", btn_now_enabled is False, f"disabled={btn_now_enabled}")
        
        # Click Review Information button -> runs extraction and completes Step 1
        client.eval("processVoiceOrTextInput()")
        time.sleep(2.0) # wait for async extraction
        
        cur_step_extracted = client.eval("currentStep")
        panel2_vis = not client.eval("document.getElementById('step-panel-2').classList.contains('hidden')")
        step1_done = client.eval("isStepCompleted(1)")
        assert_check("Step 2 opens after Step 1 completion", cur_step_extracted == 2 and panel2_vis and step1_done,
                     f"currentStep={cur_step_extracted}, panel2_visible={panel2_vis}, isStepCompleted(1)={step1_done}")

        print("\n--- TEST 3: Step 3 locked before Step 2 completion ---")
        tab3_pe = client.eval("document.getElementById('step-tab-3').style.pointerEvents")
        assert_check("Step 3 tab has pointer-events: none while on Step 2", tab3_pe == "none", f"pointerEvents='{tab3_pe}'")
        
        # Try programmatic bypass to Step 3
        client.eval("goToStep(3)")
        cur_step_after_s3_bypass = client.eval("currentStep")
        assert_check("goToStep(3) blocked before Step 2 completion; redirected to Step 2", cur_step_after_s3_bypass == 2,
                     f"currentStep={cur_step_after_s3_bypass}")

        print("\n--- TEST 4: Step 4 locked before Step 3 completion ---")
        # Try programmatic bypass to Step 4
        client.eval("goToStep(4)")
        cur_step_after_s4_bypass = client.eval("currentStep")
        assert_check("goToStep(4) blocked before Step 3 completion; redirected to earliest incomplete step", cur_step_after_s4_bypass == 2,
                     f"currentStep={cur_step_after_s4_bypass}")
        
        # Now complete Step 2 -> advance to Step 3
        client.eval("handleSearchOfficialGovSources()")
        time.sleep(2.5) # wait for search
        cur_step_after_search = client.eval("currentStep")
        step2_done = client.eval("isStepCompleted(2)")
        panel3_vis = not client.eval("document.getElementById('step-panel-3').classList.contains('hidden')")
        assert_check("Step 3 opens after Step 2 search completion", cur_step_after_search == 3 and panel3_vis and step2_done,
                     f"currentStep={cur_step_after_search}, panel3_visible={panel3_vis}, isStepCompleted(2)={step2_done}")
        
        # On Step 3: verify Step 4 is still locked before Step 3 completion
        tab4_pe = client.eval("document.getElementById('step-tab-4').style.pointerEvents")
        assert_check("Step 4 tab has pointer-events: none while on Step 3", tab4_pe == "none", f"pointerEvents='{tab4_pe}'")
        client.eval("goToStep(4)")
        cur_step_s4_locked = client.eval("currentStep")
        assert_check("goToStep(4) blocked before Step 3 completion; stays at Step 3", cur_step_s4_locked == 3,
                     f"currentStep={cur_step_s4_locked}")

        print("\n--- TEST 5: Step 4 opens after Step 3 completion ---")
        # Quick verify and advance to Step 4
        client.eval("quickVerifyAllChecklist()")
        client.eval("handleProceedToCreateApplication()")
        time.sleep(2.0)
        cur_step_final = client.eval("currentStep")
        step3_done = client.eval("isStepCompleted(3)")
        panel4_vis = not client.eval("document.getElementById('step-panel-4').classList.contains('hidden')")
        assert_check("Step 4 opens after Step 3 document generation", cur_step_final == 4 and panel4_vis and step3_done,
                     f"currentStep={cur_step_final}, panel4_visible={panel4_vis}, isStepCompleted(3)={step3_done}")

        client.close()
    finally:
        proc.terminate()
        proc.wait()
    
    print("\n" + "=" * 70)
    print(f"STEP GATING TEST SUMMARY: {passed_count} PASSED, {failed_count} FAILED")
    print("=" * 70)
    return failed_count == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
