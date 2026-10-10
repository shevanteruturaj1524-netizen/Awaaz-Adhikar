# AWAAZ ADHIKAR (आवाज़ अधिकार)
### AI-Powered Citizen Grievance Documentation & Verification Workspace

> **"Apni samasya apni bhasha mein batayein. Awaaz Adhikar aapki baat samajhne, relevant official government information dhoondhne aur application tayyar karne mein operator ki madad karta hai."**

---
🌐 **Live Demo:** https://awaaz-adhikar.onrender.com

## 1. Project Overview
**Awaaz Adhikar** is a civic documentation and verification platform built specifically for **Common Service Centre (CSC) operators, NGO workers, and rural help-desk operators**. It empowers operators to assist citizens in converting spoken or typed grievances in Indian languages (Hindi, Marathi, Bengali, English) into structured, source-backed, and verified bilingual petitions ready for official government submission.

Awaaz Adhikar is **NOT**:
- A generic chatbot
- A legal-advice chatbot
- An autonomous legal decision-making system

The human operator remains in full control of final verification and approval.

---

## 2. Problem
Over 800 million citizens across India face administrative roadblocks with public welfare schemes and civic amenities (such as non-disbursement of social welfare pensions, broken drinking water pipelines, delayed PM-KISAN installments, and land record mutation delays). Applications are frequently delayed or rejected because:
- Citizens encounter literacy and linguistic hurdles when preparing formal administrative representations.
- Petitions lack statutory nodal authority addresses, verified portal references, or required supporting documents.
- Citizens cannot easily navigate sprawling `.gov.in` and `.nic.in` government web directories.

---

## 3. Solution
Awaaz Adhikar provides a guided, human-in-the-loop workspace with an authentic 4-step workflow:
1. **Tell Your Problem**: Spoken or written grievance captured with native language selection and citizen consent.
2. **Review Information**: Real speech-to-text, fact extraction, missing information alerts, and contradiction detection.
3. **Verify & Find Information**: Real SerpApi retrieval of official `.gov.in` / `.nic.in` portals, dynamic intent-driven query generation, claim ↔ source mapping, and operator verification checklist.
4. **Create Application**: Professional bilingual document synthesis (Selected Language + English), automatic document validation, vector preview, and PDF download.

---

## 4. User-Facing 4-Step Workflow
The application is strictly organized into 4 intuitive, progressive stages:
- **STEP 1 — TELL YOUR PROBLEM** (`अपनी समस्या बताइए`)
  - Language Selection (Hindi, Marathi, Bengali, English)
  - Real Microphone Recording via `MediaRecorder` API
  - Direct Text Input Fallback
  - Explicit Citizen Consent Recording
- **STEP 2 — REVIEW INFORMATION** (`जानकारी समीक्षा`)
  - Original Citizen Transcript preserved intact
  - Operator-editable corrected transcript
  - AI Structured Fact Extraction (Citizen Name, Location, Issue Type, Duration, Department)
  - Missing Field Detection (`MISSING`) and Contradiction Alerts (`POSSIBLE CONTRADICTION`)
  - Cascading Searchable State (28 States + 8 UTs) and District Selector with cross-validation
  - Operator Case Creation SMS OTP Verification (Demo OTP: `123456`)
- **STEP 3 — VERIFY & FIND INFORMATION** (`सरकारी जानकारी खोज`)
  - Dynamic, focused search query generation from current grievance (no raw transcript dumps)
  - Official Government Source Retrieval via SerpApi / Curated Government Registry
  - 4-Tier Source Relevance Classification: `Direct Solution`, `Related Official Information`, `National Reference`, `Irrelevant`
  - Unrelated department demotion (e.g. non-RERA grievances never show RERA)
  - Operator Source Review (mark relevant, inspect URL, operator verified)
  - Traceable Claim ↔ Source Mapping Matrix
  - 8-Point Operator Verification Audit Checklist
- **STEP 4 — CREATE APPLICATION** (`आवेदन पत्र तैयार`)
  - Standardized Templates: Social Welfare Pension, Drinking Water & Civic Amenities, General Public Grievance
  - Professional Bilingual Synthesis (Zero raw conversational dialect leaked into English)
  - Side-by-Side Review & Edit
  - Automatic Document Validation (script checking, missing fact check, forbidden phrase filter)
  - Vector Document View and 1-Click PDF Download (`Information References` citation section)
  - Citizen Tracking Portal with OTP authentication

---

## 5. AI Role
AI in Awaaz Adhikar acts as an **assistive administrative intelligence**, NOT an autonomous decision maker:
1. **Speech-to-Text**: Converts real spoken audio into native-language text.
2. **Fact Extraction**: Identifies key entities without inventing missing facts.
3. **Contradiction Detection**: Detects conflicting dates, durations, or claims.
4. **Intent Understanding**: Discovers service intent, process intent, and authority context generically without hard-coded rules.
5. **Search Query Construction**: Formulates clean, focused queries without sending long transcripts blindly.
6. **Professional Drafting**: Generates formal, administrative bilingual petitions.

---

## 6. Government Search Role (SerpApi)
SerpApi is a retrieval provider, not a legal certifier:
- Prioritizes official `.gov.in` and `.nic.in` domains.
- Evaluates title, snippet, and domain relevance against the current problem.
- Detects ambiguous requests (e.g., bare "certificate" requests trigger clarification notes).
- Labels national portals (CPGRAMS, India.gov.in) as `National Reference` fallbacks.
- Never labels search results as "Government Approved" or "Legally Verified".

---

## 7. Operator Role
The operator (CSC operator, NGO staff, or help-desk volunteer) is the **final human verification layer**:
- Confirms citizen identity and statement accuracy.
- Resolves missing fields and contradictions.
- Validates official government sources.
- Checks template alignment and bilingual wording.
- Authorizes final PDF generation.

---

## 8. Technology Stack
- **Backend**: Python 3.10+, FastAPI, Uvicorn, SQLite3, Requests, Pydantic, Dotenv
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, Tailwind CSS, Google Fonts (Inter, Noto Sans Devanagari, Noto Sans Bengali)
- **Speech & Audio**: Browser MediaDevices API, MediaRecorder, Web Speech API, SpeechRecognition, PyDub / FFmpeg
- **Search Provider**: SerpApi Google Engine with strict government domain validation
- **PDF Engine**: Client-side `html2pdf.js` canvas rendering + backend printable vector HTML route (`/document/{case_id}`)
- **Security**: PBKDF2 HMAC SHA-256 password hashing, HTTP-only session cookies, SQLite operator session store, SHA-256 mobile hashing, rate-limiting

---

## 9. Setup & Installation

### Prerequisites
- Python 3.10 or higher
- Modern Chromium-based browser (Chrome, Edge, Brave) or Safari

### Steps
1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd "AVAJ ADHAKR"
   ```
2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
4. **Start the server**:
   ```bash
   python main.py
   ```
5. **Access the application**:
   Open `http://127.0.0.1:8000` in your web browser.

---

## 10. Environment Variables
See `.env.example` for the complete placeholder template:
```env
# SerpApi API Key for live government search
SERPAPI_API_KEY=your_serpapi_api_key_here

# Enable Demo Mode fallback
DEMO_MODE=true

# Optional Cloud STT/TTS Providers
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# SMS OTP Provider (Fast2SMS / Twilio / Custom HTTP Gateway)
FAST2SMS_API_KEY=your_fast2sms_api_key_here
```

---

## 11. Demo Mode
- `DEMO_MODE=true` enables testing without live paid API credentials.
- **Demo Operator Login**: `operator@awaazadhikar.gov.in` / `demo123` (or click "Operator Demo Login").
- **Demo OTP**: `123456` (enforces 5-minute expiry, single-use, max 5 attempts with 15-minute lockout).
- **Curated Scenarios**: Pre-configured real-world cases (Pension, Drinking Water, PM-KISAN, Ration, Contradictions).
- In Demo Mode, search results are transparently labeled with `DEMO MODE` tags.

---

## 12. Testing

Awaaz Adhikar includes automated tests for core workflows, grievance processing, security and validation.

### Run the test suites

From the project root directory, run:

```powershell
python run_required_tests.py
```

To run the final verification suite:

```powershell
python verify_final_suite.py
```

Additional test files cover browser workflows, business logic, extraction, security, multilingual processing and public URL checks.

### Test reporting

Test results should be recorded as:

- **PASS** — the test executed and passed.
- **FAIL** — the test executed and failed.
- **NOT TESTED** — the test could not be executed or requires manual verification.

Physical microphone input, audio playback and live deployment behaviour should be marked as tested only after actual verification.

## 13. Deployment
- **Localhost**: `http://127.0.0.1:8000`
- **Production Server**: Deploy behind a reverse proxy (Nginx / Caddy) with TLS/SSL:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
  ```
- Set `DEMO_MODE=false` in production to require real SMS OTPs.

---

## 14. Privacy & Security
- **Explicit Consent**: Citizen must check and confirm consent before recording audio.
- **Original Transcript Immutability**: The original spoken words are permanently preserved and never overwritten.
- **Data Minimization & Hashing**: Citizen mobile numbers are stored as SHA-256 hashes with masked displays (`98XXXXX210`).
- **No Third-Party Leakage**: No citizen grievance data is sent to public training sets.
- **Authentication**: Operator workspace routes and case endpoints are strictly protected by session tokens and HTTP-only cookies.

---

## 15. Limitations
- **Speech Recognition Support**: Web Speech API requires Chrome/Edge/Safari; on unsupported browsers, real MediaRecorder audio upload and text fallback are provided.
- **Offline Mode**: Full offline mode requires pre-cached government portals.

---

## 16. Future Scope
- Integration with DigiLocker for automatic document verification.
- Direct authenticated API submission to state grievance portals (UP Jansunwai, MahaGrievance, CPGRAMS).
- WhatsApp / IVR outbound status updates for rural citizens.
