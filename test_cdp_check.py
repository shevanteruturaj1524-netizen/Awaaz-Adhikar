import subprocess
import time
import json
import urllib.request
import os

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE_PATH):
    EDGE_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

print(f"Using browser: {EDGE_PATH}")

# Launch browser
proc = subprocess.Popen([
    EDGE_PATH,
    "--headless=new",
    "--remote-debugging-port=9222",
    "--no-first-run",
    "--no-default-browser-check",
    "--user-data-dir=C:\\Users\\RUTURAJ SHEVANTE\\AppData\\Local\\Temp\\browser_test_profile",
    "http://127.0.0.1:8000"
])

try:
    time.sleep(2)
    # Check CDP endpoint
    with urllib.request.urlopen("http://127.0.0.1:9222/json") as res:
        tabs = json.loads(res.read().decode())
        print(f"Found {len(tabs)} tabs via CDP:")
        for t in tabs:
            print(" ", t.get("title"), t.get("url"), t.get("id"))
finally:
    proc.terminate()
    proc.wait()
    print("Browser closed successfully.")
