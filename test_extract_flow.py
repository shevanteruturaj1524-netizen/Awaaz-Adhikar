import json
import urllib.request
import sys
import time
from test_cdp_ws import MinimalCDPClient

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with urllib.request.urlopen('http://127.0.0.1:9223/json') as res:
    tabs = json.loads(res.read().decode())
app_tab = next(t for t in tabs if 'Awaaz' in t.get('title', '') or '8000' in t.get('url', ''))
client = MinimalCDPClient(app_tab['webSocketDebuggerUrl'])

client.eval('handleDemoLogin()')
time.sleep(0.5)
client.eval('startNewCase(true)')
time.sleep(0.5)

complaint = "My name is Ramesh Kumar. I have not received pension for 3 months. I am from Rampur village, Sitapur district, Uttar Pradesh."
client.eval(f"document.getElementById('raw-input-text').value = {json.dumps(complaint)}")
client.eval("document.getElementById('raw-input-text').dispatchEvent(new Event('input'))")
client.eval("processVoiceOrTextInput()")
time.sleep(2.5)

print("extracted:", client.eval("JSON.stringify(currentCase.extracted_fields)"))
print("state select:", client.eval("document.getElementById('field-state-select').value"))
print("district select:", client.eval("document.getElementById('field-district-select').value"))
print("district val:", client.eval("document.getElementById('field-district').value"))
client.close()
