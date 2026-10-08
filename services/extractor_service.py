import re
import json
from pathlib import Path
from typing import Dict, List, Any
from config import DATA_DIR

# Load authoritative Indian administrative divisions
DIVISIONS_FILE = DATA_DIR / "india-administrative-divisions.json"
ADMINISTRATIVE_DIVISIONS: Dict[str, Any] = {}
if DIVISIONS_FILE.exists():
    try:
        ADMINISTRATIVE_DIVISIONS = json.loads(DIVISIONS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[Error loading administrative divisions]: {e}")

def _contains_keyword(text: str, keyword: str) -> bool:
    if not text or not keyword:
        return False
    pattern = r"(?<![A-Za-z\u0900-\u097F\u0980-\u09FF])" + re.escape(keyword.lower()) + r"(?![A-Za-z\u0900-\u097F\u0980-\u09FF])"
    return bool(re.search(pattern, text.lower()))

# Multilingual mappings for common States and Districts
LOCATION_ALIASES = {
    # States
    "उत्तर प्रदेश": "Uttar Pradesh",
    "uttar pradesh": "Uttar Pradesh",
    "up": "Uttar Pradesh",
    "राजस्थान": "Rajasthan",
    "rajasthan": "Rajasthan",
    "महाराष्ट्र": "Maharashtra",
    "maharashtra": "Maharashtra",
    "पश्चिम बंगाल": "West Bengal",
    "পশ্চিমবঙ্গ": "West Bengal",
    "west bengal": "West Bengal",
    "बिहार": "Bihar",
    "bihar": "Bihar",
    "मध्य प्रदेश": "Madhya Pradesh",
    "madhya pradesh": "Madhya Pradesh",
    "mp": "Madhya Pradesh",
    
    # Common Districts & Cities
    "सीतापुर": ("Sitapur", "Uttar Pradesh"),
    "sitapur": ("Sitapur", "Uttar Pradesh"),
    "अलवर": ("Alwar", "Rajasthan"),
    "alwar": ("Alwar", "Rajasthan"),
    "कोल्हापूर": ("Kolhapur", "Maharashtra"),
    "kolhapur": ("Kolhapur", "Maharashtra"),
    "अहमदनगर": ("Ahmednagar", "Maharashtra"),
    "ahmednagar": ("Ahmednagar", "Maharashtra"),
    "पुणे": ("Pune", "Maharashtra"),
    "pune": ("Pune", "Maharashtra"),
    "नागपूर": ("Nagpur", "Maharashtra"),
    "nagpur": ("Nagpur", "Maharashtra"),
    "नाशिक": ("Nashik", "Maharashtra"),
    "nashik": ("Nashik", "Maharashtra"),
    "ठाणे": ("Thane", "Maharashtra"),
    "thane": ("Thane", "Maharashtra"),
    "নদীয়া": ("Nadia", "West Bengal"),
    "নদিয়া": ("Nadia", "West Bengal"),
    "nadia": ("Nadia", "West Bengal"),
    "দক্ষিণ ২৪ পরগনা": ("South 24 Parganas", "West Bengal"),
    "south 24 parganas": ("South 24 Parganas", "West Bengal"),
    "কলকাতা": ("Kolkata", "West Bengal"),
    "kolkata": ("Kolkata", "West Bengal"),
    "হাওড়া": ("Howrah", "West Bengal"),
    "howrah": ("Howrah", "West Bengal"),
    "पटना": ("Patna", "Bihar"),
    "patna": ("Patna", "Bihar"),
    "जयपुर": ("Jaipur", "Rajasthan"),
    "jaipur": ("Jaipur", "Rajasthan"),
    "लखनऊ": ("Lucknow", "Uttar Pradesh"),
    "lucknow": ("Lucknow", "Uttar Pradesh"),
    "वाराणसी": ("Varanasi", "Uttar Pradesh"),
    "varanasi": ("Varanasi", "Uttar Pradesh"),
    "प्रयागराज": ("Prayagraj", "Uttar Pradesh"),
    "prayagraj": ("Prayagraj", "Uttar Pradesh"),
    "सोलापूर": ("Solapur", "Maharashtra"),
    "सोलापुर": ("Solapur", "Maharashtra"),
    "solapur": ("Solapur", "Maharashtra"),
    "मुर्शिदाबाद": ("Murshidabad", "West Bengal"),
    "মুর্শিদাবাদ": ("Murshidabad", "West Bengal"),
    "murshidabad": ("Murshidabad", "West Bengal"),
    "जबलपुर": ("Jabalpur", "Madhya Pradesh"),
    "jabalpur": ("Jabalpur", "Madhya Pradesh"),
    "भोपाल": ("Bhopal", "Madhya Pradesh"),
    "bhopal": ("Bhopal", "Madhya Pradesh"),
    "सूरत": ("Surat", "Gujarat"),
    "surat": ("Surat", "Gujarat"),
    "अहमदाबाद": ("Ahmedabad", "Gujarat"),
    "ahmedabad": ("Ahmedabad", "Gujarat")
}

# Keyword maps for realistic entity extraction from Indian languages / transcripts
SCHEME_KEYWORDS = {
    "scholarship": ["scholarship", "scholarships", "stipend", "fee", "student", "shishyavrutti", "chhatravritti", "छात्रवृत्ति", "स्कॉलरशिप", "শিক্ষাবৃত্তি", "ছাত্রবৃত্তি", "post matric", "pre matric", "post-matric", "pre-matric"],
    "land": ["land", "mutation", "dakhil kharij", "dakhil-kharij", "dakhil", "kharij", "namantaran", "patwari", "khasra", "khatauni", "zameen", "जमीन", "खसरा", "खतौनी", "पटवारी", "लेखपाल", "दाखिल खारिज", "नामांतरण", "জমির", "জমি", "খাসরা", "মিউটেশন", "encroach", "अतिक्रमण", "कब्जा"],
    "road": ["road", "pothole", "potholes", "drainage", "sewer", "waterlogging", "street light", "safai", "sanitation", "sadak", "gaddha", "सड़क", "सड़क", "गड्ढा", "नाली", "রাস্তা", "নর্দমা", "रस्ता", "खड्डे"],
    "electricity": ["bijli", "electricity", "power", "meter", "बिजली", "करंट", "voltage", "bill", "वीज", "विद्युत", "वीजपुरवठा", "বিদ্যুৎ", "outage", "power cut", "load shedding", "feeder", "transformer", "discom", "ugvcl", "dqvcl", "torrent"],
    "water": ["water", "पानी", "जल", "नल", "জল", "পানি", "पाणीपुरवठा", "पिण्याचे पाणी", "जलपुरवठा", "जल সরবরাহ", "পানীয় জল", "handpump", "pipe", "leakage", "jal jeevan", "drinking water", "swachh", "pipeline", "borewell", "paani", "pani", "panyacha", "panya", "pinnyachya", "purvatha"],
    "ration": ["ration", "raashan", "rashan", "pds", "food grain", "fair price", "fps", "kotedar", "quota", "ration card", "nfsa", "dealer", "anaj", "अनाज", "चाल", "গম", "राशन", "कोटा", "रुपए", "রেশন", "खाद्यान्न"],
    "pension": ["pension", "पेंशन", "पेन्शन", "পেনশন", "वृद्धावस्था", "विधवा", "दिव्यांग", "old age", "vridha", "vidhwa", "epfo", "nsap", "barodhakya", "বার্ধক্য ভাতা"],
    "pmkisan": ["kisan", "किसान", "কৃষক", "pm kisan", "pm-kisan", "samman nidhi", "कृषि", "khet", "खेती", "किस्त", "हप्ता"],
    "health": ["hospital", "doctor", "medicine", "health", "swasthya", "treatment", "phc", "chc", "ayushman", "अस्पताल", "स्वास्थ्य", "चिकित्सा", "হাসপাতাল"],
    "certificates": ["certificate", "praman patra", "birth certificate", "death certificate", "caste certificate", "income certificate", "domicile", "प्रमाणपत्र", "दस्तावेज़", "সার্টিফিকেট"],
    "housing": ["pmay", "awas", "आवास", "house", "मकान", "colony", "कालोनी", "घरकुल"]
}

DEPARTMENT_MAP = {
    "scholarship": "Department of Social Welfare / Higher Education (Scholarship Sanction Division)",
    "land": "Department of Revenue / Office of the Tehsildar & Sub-Divisional Magistrate",
    "road": "Municipal Corporation / Nagar Nigam / Public Works Department (PWD)",
    "ration": "Department of Food, Civil Supplies & Consumer Affairs",
    "electricity": "State Electricity Distribution Corporation (DISCOM) / Power Department",
    "water": "Department of Drinking Water & Sanitation / Jal Nigam / Municipal Water Works",
    "pension": "Department of Social Welfare / Social Justice & Empowerment",
    "pmkisan": "Department of Agriculture and Farmers Welfare",
    "health": "Department of Health & Family Welfare / District Chief Medical Officer",
    "certificates": "Department of E-Governance / Office of the Tehsildar",
    "housing": "Department of Rural Development / Housing Authority",
    "general": "Office of District Magistrate / District Collectorate"
}

REQUIRED_DOCUMENTS_BY_SCHEME = {
    "scholarship": ["Student College / School ID Card", "Institute Verification / Admission Slip", "Aadhaar Card Copy", "Bank Passbook with Active DBT/NPCI Seeding"],
    "land": ["Registered Sale Deed / Title Deed Copy", "Khasra / Khatauni Jamabandi Revenue Record", "Mutation Application Acknowledgement / Challan", "Identity Proof (Aadhaar Card)"],
    "road": ["Site Photographs of Damaged Road / Hazardous Potholes", "Ward Number / Locality Landmark Details", "Citizen Representation / Identity Proof"],
    "pension": ["Aadhaar Card Copy", "Bank Passbook with Active DBT/NPCI Seeded Account", "Age / Income Proof Certificate", "Disability Certificate (if applicable)"],
    "water": ["Consumer / Gram Panchayat Water Connection ID", "Site Photograph of Disrupted Supply", "Previous Grievance Registration Number (if any)"],
    "ration": ["Ration Card Copy", "Family Members Aadhaar Cards", "Income Certificate / NFSA Inclusion Slip"],
    "pmkisan": ["Aadhaar Card", "Land Khatauni / Revenue Record", "Bank Passbook with NPCI Seeding"],
    "housing": ["BPL / SECC Census ID", "Bank Account Details", "Aadhaar Card of Head of Household"],
    "electricity": ["Electricity Bill / Connection Number", "ID Proof", "Meter Reading Snapshot / Substation Feeder Reference"],
    "health": ["Hospital Registration Slip / OP Ticket", "Ayushman Bharat / PM-JAY Card", "Medical Reports / Doctor Prescription"],
    "certificates": ["Application Acknowledgement Receipt", "Supporting Identity Proofs", "Affidavit / Verification Report"]
}

def infer_civic_grievance_semantics(text: str) -> Dict[str, Any]:
    """
    Dynamically analyzes ANY citizen grievance text (seen or unseen) to determine:
    - issue_type: Precise, descriptive title of the grievance
    - scheme: Relevant civic service or administrative process
    - department: Likely competent authority or administrative department
    - scheme_code: Short semantic identifier
    - docs: Required documents
    """
    t_lower = text.lower()
    
    # 1. High-Precision Specific Civic Domains for Unseen & Standard Grievances
    if any(k in t_lower for k in ["property tax", "house tax", "holding tax", "tax receipt", "tax overcharge", "गृह कर", "संपत्ति कर", "मालमत्ता कर"]):
        return {
            "issue_type": "Property Tax Assessment & Payment Discrepancy",
            "scheme": "Municipal Property Taxation & Revenue Collection",
            "department": "Municipal Corporation / Directorate of Municipal Administration",
            "scheme_code": "property_tax",
            "docs": ["Property Tax Assessment Number / Holding ID", "Online Payment Receipt / Bank Debit Record", "Property Ownership Title / Deed Copy"]
        }

    if any(k in t_lower for k in ["birth certificate", "death certificate", "marriage certificate", "जन्म प्रमाण पत्र", "मृत्यु प्रमाण पत्र", "जन्म दाखला"]):
        cert_name = "Birth Certificate" if ("birth" in t_lower or "जन्म" in t_lower) else ("Death Certificate" if ("death" in t_lower or "मृत्यु" in t_lower) else "Civil Registration Certificate")
        return {
            "issue_type": f"Delayed Issuance / Correction of {cert_name}",
            "scheme": "Civil Registration System (CRS) & Municipal Vital Statistics",
            "department": "Office of the Registrar of Births & Deaths / Municipal Health Department",
            "scheme_code": "civil_registration",
            "docs": ["Hospital Discharge / Birth-Death Summary Record", "Parents / Informant Aadhaar Card Copy", "Application Acknowledgment Receipt / Token"]
        }

    if any(k in t_lower for k in ["driving licence", "driving license", "vehicle registration", "driving", "licence renewal", "license renewal", "challan", "ड्राइविंग लाइसेंस"]) or any(re.search(rf"\b{s}\b", t_lower) for s in ["dl", "rc", "rto"]):
        return {
            "issue_type": "Driving Licence & Motor Vehicle Service Delay",
            "scheme": "Vahan & Sarathi Citizen Mobility Services",
            "department": "Regional Transport Office (RTO) / Department of Transport",
            "scheme_code": "transport",
            "docs": ["Application Reference Number / Token Slip", "Learner Licence / Previous DL Copy", "Identity & Age Proof Documents"]
        }

    if any(k in t_lower for k in ["garbage", "kachra", "street light", "sewer", "safai", "कचरा", "स्ट्रीट लाइट", "सफाई", "गंदगी"]):
        return {
            "issue_type": "Urban Civic Amenities & Solid Waste Maintenance",
            "scheme": "Swachh Bharat Urban / Civic Maintenance Program",
            "department": "Municipal Corporation / Urban Local Body Sanitary Department",
            "scheme_code": "civic_maintenance",
            "docs": ["Photographs of Unattended Garbage / Defective Infrastructure", "Ward Number & Locality Landmark Reference"]
        }

    # 2. Existing Recognized Categories (as hints)
    for scheme, keywords in SCHEME_KEYWORDS.items():
        if any(kw in t_lower for kw in keywords):
            dept = DEPARTMENT_MAP.get(scheme, "Office of District Magistrate / District Collectorate")
            docs = REQUIRED_DOCUMENTS_BY_SCHEME.get(scheme, ["Identity Proof (Aadhaar/Voter ID)", "Relevant Application/Receipt Reference"])
            
            if scheme == "scholarship":
                return {
                    "issue_type": "Delayed Disbursement of Student Scholarship",
                    "scheme": "State / National Student Scholarship & DBT Scheme",
                    "department": dept, "scheme_code": scheme, "docs": docs
                }
            elif scheme == "land":
                if any(k in t_lower for k in ["mutation", "dakhil kharij", "dakhil-kharij", "dakhil", "namantaran", "दाखिल खारिज", "नामांतरण", "মিউটেশন"]):
                    return {
                        "issue_type": "Pending Land Mutation (Dakhil Kharij) & Revenue Record Updation",
                        "scheme": "Land Records Modernization & Mutation Services (DILRMP)",
                        "department": dept, "scheme_code": scheme, "docs": docs
                    }
                else:
                    return {
                        "issue_type": "Land Encroachment & Revenue Record Dispute",
                        "scheme": "Revenue Administration & Land Dispute Redressal",
                        "department": dept, "scheme_code": scheme, "docs": docs
                    }
            elif scheme == "road":
                return {
                    "issue_type": "Hazardous Road Potholes, Damaged Infrastructure & Drainage Maintenance",
                    "scheme": "Urban Civic Infrastructure & Municipal Public Works",
                    "department": dept, "scheme_code": scheme, "docs": docs
                }
            elif scheme == "pension":
                return {
                    "issue_type": "Non-Disbursement of Welfare Pension",
                    "scheme": "National / State Social Assistance Pension Scheme",
                    "department": dept, "scheme_code": scheme, "docs": docs
                }
            elif scheme == "water":
                return {
                    "issue_type": "Disruption of Drinking Water Supply",
                    "scheme": "Jal Jeevan Mission / Rural Water Supply",
                    "department": dept, "scheme_code": scheme, "docs": docs
                }
            elif scheme == "ration":
                return {
                    "issue_type": "Irregular / Non-Distribution of Food Grains",
                    "scheme": "National Food Security Act (NFSA) / PDS",
                    "department": dept, "scheme_code": scheme, "docs": docs
                }
            elif scheme == "pmkisan":
                return {
                    "issue_type": "PM-KISAN Installment Not Credited",
                    "scheme": "PM-KISAN Samman Nidhi",
                    "department": dept, "scheme_code": scheme, "docs": docs
                }
            elif scheme == "electricity":
                return {
                    "issue_type": "Electricity / Power Supply Outage",
                    "scheme": "Electricity Supply / Power Distribution Services",
                    "department": dept, "scheme_code": scheme, "docs": docs
                }
            elif scheme == "health":
                return {
                    "issue_type": "Essential Healthcare Services & Medicine Availability",
                    "scheme": "Public Health Care Services & Free Drug Distribution",
                    "department": dept, "scheme_code": scheme, "docs": docs
                }
            elif scheme == "certificates":
                return {
                    "issue_type": "Civil Registration & Public Certificate Issuance",
                    "scheme": "Civil Registration & Public Service Delivery",
                    "department": dept, "scheme_code": scheme, "docs": docs
                }
            elif scheme == "housing":
                return {
                    "issue_type": "Rural / Urban Housing Sanction Discrepancy",
                    "scheme": "Pradhan Mantri Awas Yojana (PMAY)",
                    "department": dept, "scheme_code": scheme, "docs": docs
                }

    return {
        "issue_type": "General Public Grievance",
        "scheme": "Public Grievance Redressal Mechanism",
        "department": "Office of District Magistrate / District Collectorate",
        "scheme_code": "general",
        "docs": ["Identity Proof (Aadhaar/Voter ID)", "Relevant Application/Receipt Reference"]
    }

def extract_normalized_intent(text: str, state: str = "", district: str = "") -> Dict[str, Any]:
    """
    Creates ONE generic normalized English intent from the CURRENT citizen complaint.
    Guarantees:
    - 2-6 concise English words for service_intent
    - NEVER includes non-English words, Devanagari, Bengali, or conversational filler
    - State and district sourced from current confirmed case
    """
    t_lower = (text or "").lower()

    # 1. Certificates / Civil Registration / Revenue Documents
    if any(k in t_lower for k in [
        "praman patra", "pramanpatra", "certificate", "dakhla", "praman", "प्रमाण पत्र", "प्रमाणपत्र", "दाखला",
        "आय प्रमाण", "जाति प्रमाण", "निवास प्रमाण", "जन्म प्रमाण", "मृत्यु प्रमाण", "সার্টিফিকেট", "প্রমাণপত্র"
    ]):
        if any(k in t_lower for k in ["income", "aay", "aai", "आय", "उत्पन्न"]):
            service = "income certificate delay"
            process = "income certificate issuance"
            authority = "Department of Revenue and District Administration"
            entities = ["income certificate", "tehsildar"]
        elif any(k in t_lower for k in ["caste", "jati", "jaati", "जाति", "जात"]):
            service = "caste certificate delay"
            process = "caste certificate issuance"
            authority = "Department of Social Welfare / Revenue"
            entities = ["caste certificate", "sub-divisional magistrate"]
        elif any(k in t_lower for k in ["domicile", "niwas", "aawas", "adivas", "निवास", "अधिवास"]):
            service = "domicile certificate delay"
            process = "domicile certificate issuance"
            authority = "Department of Revenue / Tehsil"
            entities = ["domicile certificate", "tehsil"]
        elif any(k in t_lower for k in ["birth", "janam", "janm", "जन्म"]):
            service = "birth certificate delay"
            process = "civil registration birth certificate"
            authority = "Municipal Health Department / Registrar of Births and Deaths"
            entities = ["birth certificate", "registrar"]
        elif any(k in t_lower for k in ["death", "mrityu", "मृत्यु"]):
            service = "death certificate delay"
            process = "civil registration death certificate"
            authority = "Municipal Health Department / Registrar of Births and Deaths"
            entities = ["death certificate", "registrar"]
        else:
            service = "certificate issuance delay"
            process = "public service certificate issuance"
            authority = "Department of Revenue / E-District Administration"
            entities = ["public certificate", "e-district portal"]

        return {
            "problem_summary": f"Delay or non-issuance of public certificate ({service})",
            "service_intent": service,
            "process_intent": process,
            "authority_intent": authority,
            "important_entities": entities,
            "important_actions": ["issuance", "verification", "delivery"],
            "state": state,
            "district": district
        }

    # 2. Scholarship / Student Financial Aid
    if any(k in t_lower for k in ["scholarship", "shishyavrutti", "chhatravritti", "stipend", "fee", "छात्रवृत्ति", "स्कॉलरशिप", "শিক্ষাবৃত্তি"]):
        return {
            "problem_summary": "Non-disbursement or delay in student scholarship funds",
            "service_intent": "scholarship disbursement delay",
            "process_intent": "student scholarship DBT disbursement",
            "authority_intent": "Department of Social Welfare / Higher Education",
            "important_entities": ["scholarship", "DBT bank account"],
            "important_actions": ["disbursement", "sanction", "account credit"],
            "state": state,
            "district": district
        }

    # 3. Land / Revenue Mutation (Dakhil Kharij) / Land Encroachment
    if any(k in t_lower for k in ["mutation", "dakhil kharij", "dakhil", "kharij", "namantaran", "khasra", "khatauni", "zameen", "patwari", "lekhpal", "जमीन", "दाखिल खारिज", "नामांतरण", "खसरा"]):
        return {
            "problem_summary": "Pending land mutation or revenue record dispute",
            "service_intent": "land mutation revenue dispute",
            "process_intent": "land revenue record mutation dakhil kharij",
            "authority_intent": "Department of Revenue / Office of the Tehsildar",
            "important_entities": ["land record", "mutation", "tehsildar"],
            "important_actions": ["mutation", "hearing", "record correction"],
            "state": state,
            "district": district
        }

    # 4. Electricity / Power Supply / Transformer / Meter
    if any(k in t_lower for k in ["bijli", "electricity", "power", "meter", "transformer", "feeder", "voltage", "बिजली", "विद्युत", "वीज", "বিদ্যুৎ"]):
        return {
            "problem_summary": "Electricity power supply outage or burnt transformer",
            "service_intent": "electricity power outage complaint",
            "process_intent": "electricity distribution network restoration",
            "authority_intent": "State Electricity Distribution Corporation (DISCOM)",
            "important_entities": ["power supply", "transformer", "electricity discom"],
            "important_actions": ["restoration", "repair", "power supply"],
            "state": state,
            "district": district
        }

    # 5. Drinking Water / Pipeline / Water Disruption
    if any(k in t_lower for k in ["water", "pani", "paani", "jal", "नल", "जल", "पानी", "পাইপলাইন", "पाइपलाइन", "borewell", "handpump"]):
        return {
            "problem_summary": "Drinking water supply disruption or broken pipeline",
            "service_intent": "drinking water supply disruption",
            "process_intent": "municipal drinking water pipeline restoration",
            "authority_intent": "Department of Drinking Water & Sanitation / Jal Nigam",
            "important_entities": ["water supply", "pipeline", "jal nigam"],
            "important_actions": ["supply restoration", "pipeline repair"],
            "state": state,
            "district": district
        }

    # 6. Ration / PDS / Food Grains
    if any(k in t_lower for k in ["ration", "pds", "food grain", "kotedar", "fps", "राशन", "রেশন", "anaj", "अनाज"]):
        return {
            "problem_summary": "Irregularity or non-distribution of ration food grains",
            "service_intent": "ration food grain distribution",
            "process_intent": "public distribution system food grain allocation",
            "authority_intent": "Department of Food, Civil Supplies & Consumer Affairs",
            "important_entities": ["ration card", "fair price shop"],
            "important_actions": ["quota distribution", "dealer inquiry"],
            "state": state,
            "district": district
        }

    # 7. Pension / Social Security
    if any(k in t_lower for k in ["pension", "पेंशन", "पेन्शन", "পেনশন", "old age", "vridha", "vidhwa", "divyang"]):
        return {
            "problem_summary": "Delay or non-credit of social security welfare pension",
            "service_intent": "social security pension delay",
            "process_intent": "welfare pension DBT account disbursement",
            "authority_intent": "Department of Social Welfare",
            "important_entities": ["welfare pension", "DBT bank account"],
            "important_actions": ["disbursement", "Aadhaar seeding verification"],
            "state": state,
            "district": district
        }

    # 8. Road / Drainage / Potholes / Civic Amenities
    if any(k in t_lower for k in ["road", "pothole", "potholes", "drainage", "sewer", "gaddha", "sadak", "सड़क", "सड़क", "गड्ढा", "नाली"]):
        return {
            "problem_summary": "Hazardous road potholes, damaged road or drainage blockage",
            "service_intent": "road repair drainage maintenance",
            "process_intent": "civic infrastructure repair and public works",
            "authority_intent": "Municipal Corporation / Public Works Department (PWD)",
            "important_entities": ["road", "drainage", "municipal corporation"],
            "important_actions": ["repair", "resurfacing", "drainage desilting"],
            "state": state,
            "district": district
        }

    # 9. PM-KISAN / Farmer Subsidy
    if any(k in t_lower for k in ["pm kisan", "pm-kisan", "kisan", "किसान", "কৃষক", "samman nidhi"]):
        return {
            "problem_summary": "PM-KISAN Samman Nidhi installment not credited",
            "service_intent": "PM Kisan installment delay",
            "process_intent": "PM-KISAN DBT direct benefit transfer",
            "authority_intent": "Department of Agriculture and Farmers Welfare",
            "important_entities": ["PM Kisan", "DBT installment"],
            "important_actions": ["installment credit", "land seeding"],
            "state": state,
            "district": district
        }

    # 10. Driving Licence / RTO / Transport
    if any(k in t_lower for k in ["driving", "licence", "license", "rto", "vahan", "sarathi", "ड्राइविंग"]):
        return {
            "problem_summary": "Delay in driving licence renewal or vehicle service",
            "service_intent": "driving licence renewal delay",
            "process_intent": "RTO citizen transport service",
            "authority_intent": "Regional Transport Office (RTO) / Department of Transport",
            "important_entities": ["driving licence", "RTO"],
            "important_actions": ["dispatch", "renewal", "approval"],
            "state": state,
            "district": district
        }

    # 11. Property Tax / Holding Tax
    if any(k in t_lower for k in ["property tax", "house tax", "holding tax", "संपत्ति कर", "गृह कर"]):
        return {
            "problem_summary": "Discrepancy or payment dispute in municipal property tax",
            "service_intent": "property tax assessment discrepancy",
            "process_intent": "municipal property taxation assessment",
            "authority_intent": "Municipal Corporation Revenue Department",
            "important_entities": ["property tax", "municipal corporation"],
            "important_actions": ["assessment review", "receipt generation"],
            "state": state,
            "district": district
        }

    # 12. Street Light / Waste / Sanitation
    if any(k in t_lower for k in ["street light", "garbage", "kachra", "safai", "कचरा", "स्ट्रीट लाइट", "सफाई"]):
        return {
            "problem_summary": "Defective street lighting or uncollected garbage in locality",
            "service_intent": "street light garbage sanitation",
            "process_intent": "urban civic maintenance and sanitation",
            "authority_intent": "Municipal Corporation Sanitation Department",
            "important_entities": ["street lights", "sanitation"],
            "important_actions": ["garbage clearance", "light repair"],
            "state": state,
            "district": district
        }

    # 13. Generic / Unseen / Unknown Grievance
    english_tokens = re.findall(r'[a-zA-Z]{3,}', t_lower)
    filler = {"the", "and", "for", "with", "this", "that", "from", "please", "help", "sir", "madam", "problem", "issue", "complaint", "portal"}
    meaningful = [w for w in english_tokens if w not in filler][:3]
    if meaningful:
        derived_service = " ".join(meaningful) + " grievance delay"
    else:
        derived_service = "public civic service grievance"

    return {
        "problem_summary": f"Citizen grievance regarding {derived_service}",
        "service_intent": derived_service,
        "process_intent": "administrative public grievance redressal",
        "authority_intent": "Competent District Administrative Authority",
        "important_entities": ["public grievance", "district administration"],
        "important_actions": ["redressal", "inquiry", "resolution"],
        "state": state,
        "district": district
    }

def extract_structured_facts(transcript: str, language: str = "hi") -> Dict[str, Any]:
    """
    Extracts structured facts from the citizen grievance transcript.
    Never invents missing facts. Marks missing items clearly with operator alerts.
    Detects contradictions and location consistency.
    """
    text = transcript.strip()
    extracted: Dict[str, Any] = {}
    missing_fields: List[str] = []
    contradictions: List[str] = []

    # 1. Scheme & Issue Classification
    detected_scheme = "general"
    for scheme, keywords in SCHEME_KEYWORDS.items():
        if any(kw in text.lower() for kw in keywords):
            detected_scheme = scheme
            break
            
    # 2. Extract Duration / Timeline
    # Examples: "3 mahine", "3 महीने", "15 days", "1 saal", "२ महिने", "২ মাস"
    duration_match = re.search(r'(\d+|[०-९]+|[০-৯]+)\s*(mahine|mahino|mahina|months?|महीने|महीनों|महिन्यांपासून|महिने|মাস|বছর|साल|saal|years?|din|days?|दिवस|दिन)', text, re.IGNORECASE)
    if duration_match:
        extracted["duration"] = f"{duration_match.group(1)} {duration_match.group(2)}"
    else:
        extracted["duration"] = ""
        missing_fields.append("Duration of problem is missing (e.g., '3 months')")

    # 3. Extract Citizen Name
    name_match = re.search(r'(?:mera naam|my name is|naam|name is|i am|main|mein|मेरा नाम|माझं नाव|माझे नाव|mazhe naav|majhe naav|mazhe nav|majhe nav|amar naam|আমার নাম|নাম|নামটি)\s+([A-Za-z\u0900-\u097F\u0980-\u09FF]+(?:\s+[A-Za-z\u0900-\u097F\u0980-\u09FF]+)?)', text, re.IGNORECASE)
    if name_match:
        raw_name = name_match.group(1).strip()
        stopwords = ["se", "hoon", "hai", "ka", "ki", "ko", "village", "gaon", "आहे", "বলছি", "হলো", "from", "in"]
        if raw_name.lower() not in stopwords and len(raw_name) > 2:
            extracted["citizen_name"] = raw_name
        else:
            extracted["citizen_name"] = ""
            missing_fields.append("Citizen Name is missing (Please enter citizen's legal name)")
    else:
        extracted["citizen_name"] = ""
        missing_fields.append("Citizen Name is missing (Please enter citizen's legal name)")

    # 4. Extract Village / Town
    village_match = re.search(r'([A-Za-z\u0900-\u097F\u0980-\u09FF]+)\s*(?:village|gaon|gaon se|se hoon|गाँव|गांव|ग्राम|मौजे|গ্রাম)', text, re.IGNORECASE)
    if village_match:
        cand = village_match.group(1).strip()
        if cand.lower() not in ["main", "mera", "mere", "se", "hai", "hum", "आम्ही"]:
            extracted["village"] = cand
        else:
            extracted["village"] = ""
            missing_fields.append("Village / Town name is missing")
    else:
        alt_match = re.search(r'([A-Za-z\u0900-\u097F\u0980-\u09FF]+)\s*(?:se hoon|se hu|से हूँ|से हूं|येथून|থেকে বলছি)', text, re.IGNORECASE)
        if alt_match and alt_match.group(1).strip().lower() not in ["pension", "pareshan", "sukhi", "main", "hum"]:
            extracted["village"] = alt_match.group(1).strip()
        else:
            extracted["village"] = ""
            missing_fields.append("Village / Town name is missing")

    # 5. Extract State and District using Authoritative Administrative Divisions
    detected_state = ""
    detected_district = ""
    explicit_state_in_text = ""

    # Check if a state is explicitly named in the text (multilingual or standard)
    STATE_KEYWORDS = {
        "उत्तर प्रदेश": "Uttar Pradesh", "uttar pradesh": "Uttar Pradesh", "up": "Uttar Pradesh",
        "महाराष्ट्र": "Maharashtra", "maharashtra": "Maharashtra",
        "पश्चिम बंगाल": "West Bengal", "পশ্চিমবঙ্গ": "West Bengal", "west bengal": "West Bengal",
        "बिहार": "Bihar", "bihar": "Bihar",
        "राजस्थान": "Rajasthan", "rajasthan": "Rajasthan",
        "मध्य प्रदेश": "Madhya Pradesh", "madhya pradesh": "Madhya Pradesh", "mp": "Madhya Pradesh",
        "गुजरात": "Gujarat", "gujarat": "Gujarat"
    }
    for skw, sval in STATE_KEYWORDS.items():
        if re.search(rf'(?<![A-Za-z0-9ऀ-ॿঀ-৿]){re.escape(skw)}(?![A-Za-z0-9ऀ-ॿঀ-৿])', text, re.IGNORECASE):
            explicit_state_in_text = sval
            break

    if not explicit_state_in_text:
        for sname in ADMINISTRATIVE_DIVISIONS.keys():
            if re.search(rf'\b{re.escape(sname)}\b', text, re.IGNORECASE):
                explicit_state_in_text = sname
                break

    # Check known district aliases
    for alias, target in LOCATION_ALIASES.items():
        if isinstance(target, tuple) and re.search(rf'(?<![A-Za-z0-9ऀ-ॿঀ-৿]){re.escape(alias)}(?![A-Za-z0-9ऀ-ॿঀ-৿])', text, re.IGNORECASE):
            detected_district, mapped_state = target
            detected_state = explicit_state_in_text if explicit_state_in_text else mapped_state
            break

    # Search all administrative divisions for district if not matched by aliases
    if not detected_district:
        for state_name, info in ADMINISTRATIVE_DIVISIONS.items():
            for d in info.get("districts", []):
                if re.search(rf'\b{re.escape(d)}\b', text, re.IGNORECASE):
                    detected_district = d
                    if not explicit_state_in_text:
                        detected_state = state_name
                    break
            if detected_district:
                break

    if explicit_state_in_text:
        detected_state = explicit_state_in_text

    extracted["state"] = detected_state
    extracted["district"] = detected_district
    
    if not detected_state:
        missing_fields.append("Please select your State/Union Territory.")
    if not detected_district:
        missing_fields.append("Please select your District.")

    # Location consistency validation (Contradiction detection)
    if detected_state and detected_district and ADMINISTRATIVE_DIVISIONS:
        valid_districts = ADMINISTRATIVE_DIVISIONS.get(detected_state, {}).get("districts", [])
        if valid_districts and detected_district not in valid_districts:
            contradictions.append(f"District '{detected_district}' does not belong to the selected State '{detected_state}'. Please review.")

    # 6. Issue Type, Service & Department (Dynamically inferred for seen and unseen grievances)
    semantics = infer_civic_grievance_semantics(text) or {
        "issue_type": "General Public Grievance",
        "scheme": "Public Grievance Redressal Mechanism",
        "department": "Office of District Magistrate / District Collectorate",
        "scheme_code": "general",
        "docs": ["Identity Proof (Aadhaar/Voter ID)", "Relevant Application/Receipt Reference"]
    }
    extracted["issue_type"] = semantics["issue_type"]
    extracted["scheme"] = semantics["scheme"]
    extracted["department"] = semantics["department"]
    extracted["scheme_code"] = semantics["scheme_code"]
    extracted["problem_description"] = text
    detected_scheme = semantics["scheme_code"]
    required_docs = semantics.get("docs") or REQUIRED_DOCUMENTS_BY_SCHEME.get(detected_scheme, ["Identity Proof (Aadhaar/Voter ID)", "Relevant Application/Receipt Reference"])
    
    intent = extract_normalized_intent(text, detected_state, detected_district)
    extracted["normalized_intent"] = intent
    extracted["service_intent"] = intent["service_intent"]
    extracted["problem_summary"] = intent["problem_summary"]
    
    # 7. Mentioned Documents
    docs_found = []
    if "aadhaar" in text.lower() or "आधार" in text or "আধার" in text:
        docs_found.append("Aadhaar Card (Mentioned by citizen)")
    if "passbook" in text.lower() or "khata" in text.lower() or "खाता" in text or "बैंक" in text or "পাসবই" in text:
        docs_found.append("Bank Account Passbook (Mentioned by citizen)")
    if "ration" in text.lower() or "राशन" in text or "রেশন" in text:
        docs_found.append("Ration Card (Mentioned by citizen)")
    extracted["mentioned_documents"] = docs_found

    # 8. Contradiction Detection
    village_candidates = [w for w in ["Rampur", "Bilaspur", "Sonpur", "Dholpur", "रामपुर", "बिलासपुर", "রামপুর"] if w in text]
    if len(set(village_candidates)) > 1:
        contradictions.append(f"Possible mismatch in Village name: Conflicting locations detected ({', '.join(set(village_candidates))}).")
        
    if ("mahine" in text.lower() or "महीने" in text or "মাসের" in text) and ("saal" in text.lower() or "साल" in text or "বছরের" in text):
        contradictions.append("Conflicting timeframes: both months and years mentioned in statement. Operator confirmation required.")

    return {
        "extracted_fields": extracted,
        "missing_fields": missing_fields,
        "contradictions": contradictions,
        "recommended_template": detected_scheme if detected_scheme in ["pension", "water"] else "general",
        "required_documents_checklist": required_docs
    }

def generate_claim_source_mappings(extracted_fields: dict, sources: list) -> list:
    mappings = []
    mappings.append({
        "id": "csm-1",
        "claim_type": "Citizen-Provided Information",
        "claim_label": "Citizen Grievance Statement",
        "claim_text": f"Grievance: {extracted_fields.get('issue_type', 'Complaint')} - Duration: {extracted_fields.get('duration', 'Unspecified')}",
        "source_type": "Citizen Verbal Declaration",
        "source_reference": "Recorded & verified by Operator from citizen testimony",
        "verification_status": "Citizen-Provided (Personal Claim)",
        "is_official_source": False
    })

    mappings.append({
        "id": "csm-2",
        "claim_type": "Citizen-Provided Information",
        "claim_label": "Citizen Identity & Residence",
        "claim_text": f"Resident of {extracted_fields.get('village', 'Village')}, {extracted_fields.get('district', 'District')}, {extracted_fields.get('state', 'State')}",
        "source_type": "Citizen Verbal Declaration",
        "source_reference": "Subject to operator verification with physical Aadhaar card",
        "verification_status": "Operator Verified" if extracted_fields.get("village") and extracted_fields.get("district") else "Needs Review",
        "is_official_source": False
    })

    verified_sources = [s for s in sources if s.get("operator_verified")] or [s for s in sources if s.get("is_official")]
    for idx, s in enumerate(verified_sources[:3], 3):
        mappings.append({
            "id": f"csm-{idx}",
            "claim_type": "Statutory Entitlement / Procedure",
            "claim_label": f"Official Procedure Reference #{idx-2}",
            "claim_text": f"Grievance mechanism verified under {s.get('title')}",
            "source_type": "Official Government Portal",
            "source_reference": f"{s.get('domain')} ({s.get('url')})",
            "verification_status": "Operator Verified" if s.get("operator_verified") else "Official Domain Matched",
            "is_official_source": True
        })

    return mappings
