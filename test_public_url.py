import sys, json, urllib.request, urllib.error
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE = 'https://compliance-increased-rogers-observation.trycloudflare.com'
passed = 0; total = 0

def req(path, method='GET', data=None, headers=None):
    h = headers or {}
    url = BASE + path
    body = json.dumps(data).encode() if data else None
    if body:
        h['Content-Type'] = 'application/json'
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20) as res:
            raw = res.read().decode('utf-8', errors='replace')
            try:
                return res.status, json.loads(raw)
            except Exception:
                return res.status, raw  # HTML response
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode('utf-8', errors='replace')
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {}

def check(name, ok, detail=''):
    global passed, total
    total += 1
    if ok:
        passed += 1
        print(f'  PASS {total:02d}: {name}')
    else:
        print(f'  FAIL {total:02d}: {name} - {detail}')

print('=== PUBLIC URL WORKFLOW TEST ===')
print(f'URL: {BASE}')
print()

# 1. Landing page
s, _ = req('/')
check('Landing page HTTP 200', s == 200, f'Got {s}')

# 2. Demo login
s, d = req('/api/auth/demo-login', 'POST', {})
check('Demo login returns token', s == 200 and 'token' in d, f'Got {s}')
token = d.get('token', '')
auth = {'Authorization': f'Bearer {token}'}

# 3. Normal operator login
s, d = req('/api/auth/login', 'POST', {'email': 'operator@awaazadhikar.gov.in', 'password': 'demo123'})
check('Normal operator login works', s == 200 and 'token' in d, f'Got {s}')

# 4. Languages
s, d = req('/api/languages')
codes = [l['code'] for l in d] if isinstance(d, list) else []
check('Languages hi, mr, bn, en all present', all(c in codes for c in ['hi','mr','bn','en']), f'Got {codes}')

# 5. State/District locations
s, d = req('/api/locations')
mh = d.get('Maharashtra', {})
mh_districts = mh.get('districts', []) if isinstance(mh, dict) else []
check('Maharashtra districts loaded (Solapur present)', 'Solapur' in mh_districts, f'Districts: {len(mh_districts)}')
wb = d.get('West Bengal', {})
wb_districts = wb.get('districts', []) if isinstance(wb, dict) else []
check('West Bengal districts loaded', len(wb_districts) > 0, f'Districts: {len(wb_districts)}')
total_states = len(d.keys())
check(f'All 36 states/UTs loaded', total_states >= 36, f'Got {total_states}')

# 6. Hindi AI extraction
s, d = req('/api/extract', 'POST', {
    'transcript': '\u092e\u0947\u0930\u093e \u0928\u093e\u092e \u0930\u092e\u0947\u0936 \u0915\u0941\u092e\u093e\u0930 \u0939\u0948\u0964 \u092e\u0948\u0902 \u0917\u094d\u0930\u093e\u092e \u0930\u093e\u092e\u092a\u0941\u0930 \u091c\u093f\u0932\u093e \u0938\u0940\u0924\u093e\u092a\u0941\u0930 \u0909\u0924\u094d\u0924\u0930 \u092a\u094d\u0930\u0926\u0947\u0936 \u0938\u0947 \u092c\u094b\u0932 \u0930\u0939\u093e \u0939\u0942\u0901\u0964 \u092e\u0947\u0930\u0940 \u092a\u0947\u0902\u0936\u0928 3 \u092e\u0939\u0940\u0928\u0947 \u0938\u0947 \u0928\u0939\u0940\u0902 \u0906\u0908\u0964',
    'language': 'hi'
})
check('Hindi AI extraction HTTP 200', s == 200, f'Got {s}')
name = d.get('extracted_fields', {}).get('citizen_name', '')
state = d.get('extracted_fields', {}).get('state', '')
check('Hindi extraction: name extracted', bool(name), f'name={name}')
check('Hindi extraction: state=Uttar Pradesh', 'Uttar Pradesh' in state or 'uttar' in state.lower(), f'state={state}')

# 7. Marathi AI extraction
s, d = req('/api/extract', 'POST', {
    'transcript': '\u092e\u093e\u091d\u0947 \u0928\u093e\u0935 \u0924\u0941\u0915\u093e\u0930\u093e\u092e \u092a\u093e\u091f\u0940\u0932. \u092e\u093e\u091d\u094d\u092f\u093e \u091c\u092e\u093f\u0928\u0940\u0935\u0930 \u0905\u0924\u093f\u0915\u094d\u0930\u092e\u0923 \u0906\u0939\u0947. \u091c\u093f\u0932\u094d\u0939\u093e \u0938\u094b\u0932\u093e\u092a\u0942\u0930.',
    'language': 'mr'
})
check('Marathi AI extraction HTTP 200', s == 200, f'Got {s}')
issue = d.get('extracted_fields', {}).get('issue_type', '')
check('Marathi extraction: issue detected', bool(issue), f'issue={issue}')

# 8. Bengali AI extraction
s, d = req('/api/extract', 'POST', {
    'transcript': '\u0986\u09ae\u09be\u09b0 \u09a8\u09be\u09ae \u09b8\u09cd\u09ac\u09aa\u09a8 \u09ae\u099c\u09c1\u09ae\u09a6\u09be\u09b0\u0964 \u099c\u09c7\u09b2\u09be \u09ae\u09c1\u09b0\u09cd\u09b6\u09bf\u09a6\u09be\u09ac\u09be\u09a6\u0964 \u09b0\u09c7\u09b6\u09a8 \u09aa\u09be\u099a\u09cd\u099b\u09bf \u09a8\u09be 2 \u09ae\u09be\u09b8\u0964',
    'language': 'bn'
})
check('Bengali AI extraction HTTP 200', s == 200, f'Got {s}')
name_bn = d.get('extracted_fields', {}).get('citizen_name', '')
check('Bengali extraction: name/fields extracted', bool(name_bn) or bool(d.get('extracted_fields',{})), f'name={name_bn}')

# 9. SerpApi / Demo Mode search
s, d = req('/api/search-sources', 'POST', {
    'query': 'pension Uttar Pradesh',
    'extracted_fields': {'state': 'Uttar Pradesh', 'scheme': 'pension'}
})
sources = d.get('sources', [])
check('SerpApi/Demo search returns sources', s == 200 and len(sources) > 0, f'Got {s} with {len(sources)} sources')
all_official = all('.gov.in' in str(src.get('url','')) or '.nic.in' in str(src.get('url','')) for src in sources)
check('All returned sources are official .gov.in/.nic.in', all_official, 'Non-official domains present')

# 10. Mappings
s, d = req('/api/mappings', 'POST', {
    'extracted_fields': {'citizen_name': 'Test', 'state': 'Maharashtra', 'scheme': 'pension'},
    'sources': sources[:2]
})
check('Claim-source mappings generated', s == 200 and isinstance(d, list) and len(d) > 0, f'Got {s} with {d}')

# 11. Bilingual document generation (authenticated)
case_data = {
    'id': 'CASE-PUBTEST-MR',
    'language': 'mr',
    'citizen_name': 'Tukaram Patil',
    'original_transcript': '\u091c\u092e\u0940\u0928 \u0905\u0924\u093f\u0915\u094d\u0930\u092e\u0923',
    'edited_transcript': '\u091c\u092e\u0940\u0928 \u0905\u0924\u093f\u0915\u094d\u0930\u092e\u0923',
    'template_type': 'general',
    'extracted_fields': {
        'citizen_name': 'Tukaram Patil',
        'village': 'Mohol',
        'district': 'Solapur',
        'state': 'Maharashtra',
        'duration': '3 months',
        'issue_type': 'Land Encroachment'
    },
    'sources': [],
    'verification_status': 'Operator Verified'
}
s, doc = req('/api/generate-document', 'POST', {'case_data': case_data}, auth)
check('Bilingual document generation HTTP 200', s == 200, f'Got {s}')
en_body = doc.get('english_application', {}).get('body', '')
reg_body = doc.get('regional_language', {}).get('body', '')
has_dev_in_en = any(0x0900 <= ord(c) <= 0x097F for c in en_body)
check('English document has NO Devanagari (Layer B OK)', not has_dev_in_en, 'Devanagari found in English')
check('Marathi regional doc has formal structure', '\u092a\u094d\u0930\u0924\u093f' in reg_body, f'Body: {reg_body[:50]}')
check('English doc contains professional wording', 'encroachment' in en_body.lower() or 'grievance' in en_body.lower(), f'Body: {en_body[:100]}')

# 12. PDF/Printable view
s, html = req(f'/document/CASE-PUBTEST-MR?token={token}')
check('Printable view accessible at public URL', s == 200, f'Got {s}')
check('Printable view has print CSS + branding', 'Awaaz Adhikar' in str(html) and 'print' in str(html), 'Missing branding/print CSS')

# 13. 5 Demo scenarios
s, samples = req('/api/samples')
check('5 demo scenarios accessible', s == 200 and len(samples) == 5, f'Got {len(samples) if isinstance(samples,list) else 0}')

# 14. Security: unauthenticated access blocked
s, _ = req('/api/cases')
check('Unauthenticated /api/cases blocked (401)', s == 401, f'Got {s}')

# 15. Logout + token invalidation
s, _ = req('/api/auth/logout', 'POST', {}, auth)
check('Logout returns 200', s == 200, f'Got {s}')
s, _ = req('/api/cases', headers={'Authorization': f'Bearer {token}'})
check('Old token rejected after logout (401)', s == 401, f'Got {s}')

print()
print('=' * 55)
print(f'  PUBLIC URL TEST SUMMARY: {passed}/{total} tests passed')
print(f'  Public URL: {BASE}')
print('=' * 55)
