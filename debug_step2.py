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

from test_cdp_ws import MinimalCDPClient

port = 9226
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
proc = subprocess.Popen([
    EDGE_PATH,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--no-first-run",
    "--no-default-browser-check",
    "--user-data-dir=C:\\Users\\RUTURAJ SHEVANTE\\AppData\\Local\\Temp\\debug_gating_profile",
    "http://127.0.0.1:8000"
])

try:
    time.sleep(2)
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as res:
        tabs = json.loads(res.read().decode())
    app_tab = next(t for t in tabs if "Awaaz" in t.get("title", "") or "8000" in t.get("url", ""))
    client = MinimalCDPClient(app_tab["webSocketDebuggerUrl"])
    
    # Login and start new case
    client.eval("handleDemoLogin()")
    time.sleep(1)
    client.eval("startNewCase(true)")
    time.sleep(0.5)
    
    complaint = "मेरा नाम रमेश कुमार है। मुझे 3 महीने से वृद्धावस्था पेंशन नहीं मिली है। मैं रामपुर गाँव, जिला सीतापुर, उत्तर प्रदेश से हूँ।"
    client.eval(f"document.getElementById('raw-input-text').value = {json.dumps(complaint)}")
    client.eval("document.getElementById('raw-input-text').dispatchEvent(new Event('input'))")
    client.eval("processVoiceOrTextInput()")
    time.sleep(2.5)
    
    print("ADMIN_DIVISIONS keys count:", client.eval("Object.keys(ADMIN_DIVISIONS).length"))
    print("field-name:", client.eval("document.getElementById('field-name').value"))
    print("field-state-select:", client.eval("document.getElementById('field-state-select').value"))
    print("field-district-select:", client.eval("document.getElementById('field-district-select').value"))
    print("field-district:", client.eval("document.getElementById('field-district').value"))
    print("currentCase extracted_fields:", client.eval("JSON.stringify(currentCase.extracted_fields)"))
    
    # Try calling handleSearchOfficialGovSources
    client.eval("handleSearchOfficialGovSources()")
    time.sleep(1)
    print("currentStep after search call:", client.eval("currentStep"))
    print("missing-fields-box hidden?:", client.eval("document.getElementById('missing-fields-box').classList.contains('hidden')"))
    print("missing-fields-list:", client.eval("document.getElementById('missing-fields-list').innerText"))
    print("location-mismatch-box hidden?:", client.eval("document.getElementById('location-mismatch-box').classList.contains('hidden')"))
    if not client.eval("document.getElementById('location-mismatch-box').classList.contains('hidden')"):
        print("mismatch text:", client.eval("document.getElementById('location-mismatch-text').innerText"))
    
    client.close()
finally:
    proc.terminate()
    proc.wait()
