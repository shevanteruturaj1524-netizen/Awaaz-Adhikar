import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# SerpApi Configuration
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")

# Allowed Official Indian Government Domains
OFFICIAL_GOV_DOMAINS = [
    "gov.in",
    "nic.in",
    "pgportal.gov.in",
    "pmkisan.gov.in",
    "pensionersportal.gov.in",
    "epfindia.gov.in",
    "apra.gov.in",
    "india.gov.in",
    "uidai.gov.in",
    "nfsa.gov.in",
    "pmaymis.gov.in",
    "jaljeevanmission.gov.in",
]

# Supported Indian Languages
SUPPORTED_LANGUAGES = [
    {"code": "hi", "name": "Hindi", "native": "हिंदी", "speech_locale": "hi-IN"},
    {"code": "mr", "name": "Marathi", "native": "मराठी", "speech_locale": "mr-IN"},
    {"code": "bn", "name": "Bengali", "native": "বাংলা", "speech_locale": "bn-IN"},
    {"code": "te", "name": "Telugu", "native": "తెలుగు", "speech_locale": "te-IN"},
    {"code": "ta", "name": "Tamil", "native": "தமிழ்", "speech_locale": "ta-IN"},
    {"code": "gu", "name": "Gujarati", "native": "ગુજરાતી", "speech_locale": "gu-IN"},
    {"code": "en", "name": "English", "native": "English", "speech_locale": "en-IN"},
]
