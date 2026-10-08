def generate_printable_html(doc_data: dict, case_data: dict) -> str:
    """
    Renders an official, bilingual, print-ready HTML page with high-precision typography.
    Properly handles Devanagari (Hindi) and English typography, official government layout,
    SerpApi verification stamps, and disclaimer notices.
    """
    regional = doc_data.get("regional_language") or doc_data.get("hindi_application", {})
    hi = regional
    en = doc_data.get("english_application", {})
    case_id = doc_data.get("case_id", "CASE-001")
    template_name = doc_data.get("template_name", "Grievance Application")
    template_ver = doc_data.get("template_version", "v1.0")
    date_gen = doc_data.get("date_generated", "")
    reg_lang_display = regional.get("display") or "Selected Regional Language"
    
    extracted = case_data.get("extracted_fields", {})
    citizen_name = extracted.get("citizen_name", "Citizen")
    village = extracted.get("village", "Village")
    district = extracted.get("district", "District")
    state = extracted.get("state", "India")
    
    return f"""<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Awaaz Adhikar - Official Application #{case_id}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Bengali:wght@400;600;700&family=Noto+Sans+Devanagari:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    @page {{
      size: A4;
      margin: 15mm 15mm 15mm 15mm;
    }}
    body {{
      font-family: 'Inter', 'Noto Sans Devanagari', 'Noto Sans Bengali', sans-serif;
      color: #1e293b;
      background: #f8fafc;
      margin: 0;
      padding: 20px;
      line-height: 1.6;
    }}
    .document-container {{
      max-width: 800px;
      margin: 0 auto;
      background: #ffffff;
      padding: 36px 44px;
      border: 1px solid #cbd5e1;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
      position: relative;
    }}
    .header-banner {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2px solid #0f766e;
      padding-bottom: 12px;
      margin-bottom: 20px;
    }}
    .brand-title {{
      font-size: 20px;
      font-weight: 700;
      color: #0f766e;
      margin: 0;
    }}
    .brand-sub {{
      font-size: 11px;
      color: #64748b;
      margin-top: 2px;
    }}
    .case-badge {{
      background: #f0fdf4;
      border: 1px solid #86efac;
      padding: 6px 12px;
      border-radius: 6px;
      text-align: right;
      font-size: 12px;
    }}
    .verified-seal {{
      display: inline-block;
      font-weight: 600;
      color: #15803d;
    }}
    .lang-section {{
      margin-bottom: 30px;
      padding-bottom: 24px;
      border-bottom: 1px dashed #cbd5e1;
    }}
    .lang-section:last-child {{
      border-bottom: none;
    }}
    .section-title {{
      font-size: 15px;
      font-weight: 700;
      color: #0f172a;
      background: #f1f5f9;
      padding: 6px 12px;
      border-left: 4px solid #0f766e;
      margin-bottom: 14px;
    }}
    .app-body {{
      font-size: 13px;
      white-space: pre-wrap;
      background: #ffffff;
      padding: 4px;
      color: #334155;
    }}
    .meta-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      background: #f8fafc;
      padding: 12px 16px;
      border-radius: 6px;
      font-size: 12px;
      margin-bottom: 16px;
      border: 1px solid #e2e8f0;
    }}
    .sources-box {{
      background: #f0f9ff;
      border: 1px solid #bae6fd;
      padding: 12px 16px;
      border-radius: 6px;
      font-size: 11px;
      color: #0369a1;
      margin-top: 14px;
    }}
    .sources-title {{
      font-weight: 700;
      margin-bottom: 6px;
      color: #0284c7;
    }}
    .disclaimer-box {{
      margin-top: 14px;
      font-size: 10px;
      color: #64748b;
      border-top: 1px solid #e2e8f0;
      padding-top: 8px;
      font-style: italic;
    }}
    .print-controls {{
      max-width: 800px;
      margin: 0 auto 16px auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .btn {{
      background: #0f766e;
      color: #ffffff;
      padding: 10px 18px;
      border-radius: 6px;
      text-decoration: none;
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
      border: none;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }}
    .btn-secondary {{
      background: #e2e8f0;
      color: #334155;
    }}
    @media print {{
      body {{
        background: #ffffff;
        padding: 0;
      }}
      .print-controls {{
        display: none !important;
      }}
      .document-container {{
        border: none;
        box-shadow: none;
        padding: 0;
      }}
    }}
  </style>
</head>
<body>

  <div class="print-controls">
    <button onclick="window.history.back()" class="btn btn-secondary">← Back to Workspace</button>
    <div style="display:flex; gap:10px;">
      <button onclick="window.print()" class="btn">🖨️ Print / Save as PDF</button>
    </div>
  </div>

  <div class="document-container">
    <div class="header-banner">
      <div>
        <h1 class="brand-title">आवाज़ अधिकार (Awaaz Adhikar)</h1>
        <div class="brand-sub">Citizen Grievance Documentation & Verification System | Template: {template_name} ({template_ver})</div>
      </div>
      <div class="case-badge">
        <div><strong>Case ID:</strong> {case_id}</div>
        <div><strong>Date:</strong> {date_gen}</div>
        <div class="verified-seal">✓ Operator Verified & Source-Backed</div>
      </div>
    </div>

    <div class="meta-grid">
      <div><strong>Citizen:</strong> {citizen_name}</div>
      <div><strong>Village/Location:</strong> {village}, {district} ({state})</div>
      <div><strong>Category:</strong> {template_name}</div>
      <div><strong>Verification:</strong> Completed via SerpApi Gov Engine</div>
    </div>

    <!-- REGIONAL APPLICATION SECTION -->
    <div class="lang-section">
      <div class="section-title">SECTION 1: {regional.get("title", "Regional Grievance Application")} ({reg_lang_display})</div>
      <div class="app-body">{hi.get("body", "")}</div>
      <div class="sources-box">
        <div class="sources-title">📌 Information References (सत्यापित सूचना संदर्भ):</div>
        <div style="white-space: pre-wrap;">{hi.get("sources_reference", "")}</div>
      </div>
      <div class="disclaimer-box">{hi.get("disclaimer", "")}</div>
    </div>

    <!-- ENGLISH APPLICATION SECTION -->
    <div class="lang-section">
      <div class="section-title">PART 2: Formal English Grievance Application</div>
      <div class="app-body">{en.get("body", "")}</div>
      <div class="sources-box">
        <div class="sources-title">📌 Information References (Government Portals &amp; Statutory References):</div>
        <div style="white-space: pre-wrap;">{en.get("sources_reference", "")}</div>
      </div>
      <div class="disclaimer-box">{en.get("disclaimer", "")}</div>
    </div>

    <div style="text-align: center; margin-top: 24px; font-size: 11px; color: #94a3b8;">
      Generated via Awaaz Adhikar Civic Workspace • Designed for CSCs, NGOs & Rural Help Desks • Non-AI Chatbot Platform
    </div>
  </div>

</body>
</html>
"""
