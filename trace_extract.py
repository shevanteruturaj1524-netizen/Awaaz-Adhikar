import os
import sys
import json
import time
import subprocess
import urllib.request
from test_cdp_ws import MinimalCDPClient

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
proc = subprocess.Popen([
    EDGE_PATH,
    "--headless=new",
    "--remote-debugging-port=9228",
    "--no-first-run",
    "--no-default-browser-check",
    "--user-data-dir=C:\\Users\\RUTURAJ SHEVANTE\\AppData\\Local\\Temp\\check_inp_prof2",
    "http://127.0.0.1:8000"
])

try:
    time.sleep(2)
    with urllib.request.urlopen("http://127.0.0.1:9228/json") as res:
        tabs = json.loads(res.read().decode())
    app_tab = next(t for t in tabs if "Awaaz" in t.get("title", "") or "8000" in t.get("url", ""))
    client = MinimalCDPClient(app_tab["webSocketDebuggerUrl"])
    
    client.eval("handleDemoLogin()")
    time.sleep(0.5)
    client.eval("startNewCase(true)")
    time.sleep(0.5)
    
    complaint = "मेरा नाम रमेश कुमार है। मुझे 3 महीने से वृद्धावस्था पेंशन नहीं मिली है। मैं रामपुर गाँव, जिला सीतापुर, उत्तर प्रदेश से हूँ।"
    client.eval(f"document.getElementById('raw-input-text').value = {json.dumps(complaint)}")
    client.eval("document.getElementById('raw-input-text').dispatchEvent(new Event('input'))")
    client.eval("processVoiceOrTextInput()")
    time.sleep(3.0)
    
    print("currentCase extracted_fields:", client.eval("JSON.stringify(currentCase.extracted_fields)"))
    print("field-state value:", client.eval("document.getElementById('field-state').value"))
    print("field-state-select value:", client.eval("document.getElementById('field-state-select').value"))
    print("field-district value:", client.eval("document.getElementById('field-district').value"))
    print("field-district-select value:", client.eval("document.getElementById('field-district-select').value"))
    client.close()
finally:
    proc.terminate()
    proc.wait()
