import json, time, urllib.request
from test_cdp_ws import MinimalCDPClient

with urllib.request.urlopen("http://127.0.0.1:8000/api/health") as r:
    print("Health:", r.read().decode())
