import re
from datetime import datetime
from typing import Dict, Any
from services.translation_service import synthesize_professional_wording, normalize_duration_to_english

TEMPLATES_META = {
    "pension": {
        "id": "pension",
        "name": "Social Welfare Pension Grievance Application",
        "name_hi": "सामाजिक सुरक्षा पेंशन शिकायत एवं समाधान आवेदन",
        "name_mr": "सामाजिक सुरक्षा पेन्शन तक्रार व निवारण अर्ज",
        "name_bn": "সামাজিক সুরক্ষা পেনশন বকেয়া ও নিষ্পত্তি আবেদনপত্র",
        "version": "v1.2-2026",
        "last_reviewed": "28 Mar 2026",
        "department_default": "Office of the District Social Welfare Officer"
    },
    "water": {
        "id": "water",
        "name": "Drinking Water & Civic Amenities Grievance Petition",
        "name_hi": "पेयजल एवं जनसुविधा व्यवधान निवारण आवेदन",
        "name_mr": "पेयजल व नागरी सुविधा निवारण अर्ज",
        "name_bn": "পানীয় জল ও নাগরিক সমস্যা নিষ্পত্তি আবেদন",
        "version": "v1.1-2026",
        "last_reviewed": "28 Mar 2026",
        "department_default": "Office of the Executive Engineer, Jal Nigam / Block Development Office"
    },
    "general": {
        "id": "general",
        "name": "General Citizen Public Grievance Application",
        "name_hi": "सामान्य जन शिकायत एवं समाधान प्रार्थना पत्र",
        "name_mr": "सार्वजनिक तक्रार निवारण अर्ज",
        "name_bn": "সাধারণ নাগরিক অভিযোগ ও নিষ্পত্তি আবেদনপত্র",
        "version": "v1.0-2026",
        "last_reviewed": "28 Mar 2026",
        "department_default": "Office of the District Magistrate / Sub-Divisional Officer (SDM)"
    }
}

def generate_bilingual_application(case_data: dict) -> dict:
    """
    Generates bilingual application texts: Selected Language (Hindi / Marathi / Bengali / English) + English.
    """
    extracted = case_data.get("extracted_fields", {})
    template_type = case_data.get("template_type", "general")
    meta = TEMPLATES_META.get(template_type, TEMPLATES_META["general"])
    lang = case_data.get("language", "hi")
    
    citizen_name = (extracted.get("citizen_name") or "").strip() or (case_data.get("citizen_name") or "").strip() or "[MISSING: Citizen Name Required]"
    village = extracted.get("village") or "[MISSING: Village Name Required]"
    district = extracted.get("district") or "[MISSING: District Required]"
    state = extracted.get("state") or "India"
    duration = extracted.get("duration") or "Unspecified period"
    issue_type = extracted.get("issue_type") or "Public Welfare Grievance"
    department = extracted.get("department") or meta["department_default"]
    problem_desc = case_data.get("edited_transcript") or case_data.get("original_transcript") or extracted.get("problem_description", "")
    
    # Synthesize high-quality professional wording for both English and Regional language
    wording = synthesize_professional_wording(problem_desc, lang, extracted)
    problem_en = wording["english"]
    problem_hi = wording["regional"] if lang == "hi" else synthesize_professional_wording(problem_desc, "hi", extracted)["regional"]
    problem_mr = wording["regional"] if lang == "mr" else synthesize_professional_wording(problem_desc, "mr", extracted)["regional"]
    problem_bn = wording["regional"] if lang == "bn" else synthesize_professional_wording(problem_desc, "bn", extracted)["regional"]
    
    sources = case_data.get("sources", [])
    verified_sources = [s for s in sources if s.get("operator_verified")] or [s for s in sources if s.get("is_official")]
    
    date_str = datetime.now().strftime("%d-%m-%Y")
    case_id = case_data.get("id") or case_data.get("case_id") or "CASE-NEW"
    operator_id = case_data.get("operator_id", "CSC-OPERATOR-01")
    
    # Format source references for English and Regional Languages
    sources_ref_en = []
    sources_ref_hi = []
    sources_ref_mr = []
    sources_ref_bn = []
    
    for idx, s in enumerate(verified_sources[:3], 1):
        status_tag_en = "[Operator Verified]" if s.get("operator_verified") else "[Official Gov Domain]"
        status_tag_hi = "[ऑपरेटर सत्यापित]" if s.get("operator_verified") else "[आधिकारिक सरकारी डोमेन]"
        status_tag_mr = "[ऑपरेटर पडताळणीकृत]" if s.get("operator_verified") else "[अधिकृत शासकीय डोमेन]"
        status_tag_bn = "[অপারেটর যাচাইকৃত]" if s.get("operator_verified") else "[সরকারি ডোমেইন]"
        
        sources_ref_en.append(f"{idx}. {s.get('title')} ({status_tag_en})\n   Official Portal: {s.get('url')}")
        sources_ref_hi.append(f"{idx}. {s.get('title')} ({status_tag_hi})\n   आधिकारिक पोर्टल: {s.get('url')}")
        sources_ref_mr.append(f"{idx}. {s.get('title')} ({status_tag_mr})\n   अधिकृत पोर्टल: {s.get('url')}")
        sources_ref_bn.append(f"{idx}. {s.get('title')} ({status_tag_bn})\n   সরকারি পোর্টাল: {s.get('url')}")
    
    if not sources_ref_en:
        sources_ref_en.append("No official external portal linked. Case based on verified citizen testimony.")
        sources_ref_hi.append("कोई बाहरी पोर्टल संबद्ध नहीं। आवेदन नागरिक के सत्यापित बयान पर आधारित है।")
        sources_ref_mr.append("कोणतेही बाह्य पोर्टल जोडलेले नाही. अर्ज नागरिकांच्या सत्यापित जबाबावर आधारित आहे.")
        sources_ref_bn.append("কোনো সরকারি পোর্টাল সংযুক্ত নয়। নাগরিকের যাচাইকৃত বক্তব্যের ভিত্তিতে প্রস্তুত।")
        
    source_block_en = "\n".join(sources_ref_en)
    source_block_hi = "\n".join(sources_ref_hi)
    source_block_mr = "\n".join(sources_ref_mr)
    source_block_bn = "\n".join(sources_ref_bn)

    # 1. HINDI TEMPLATES
    if template_type == "pension":
        body_hi = f"""सेवा में,
श्रीमान जिला समाज कल्याण अधिकारी,
{department}
जिला: {district}, राज्य: {state}

विषय: सामाजिक सुरक्षा पेंशन का विगत {duration} से भुगतान न होने के संबंध में आवेदन पत्र।

महोदय,
सविनय निवेदन है कि प्रार्थी/प्रार्थिया {citizen_name}, ग्राम/कस्बा: {village}, जिला: {district} का/की मूल निवासी है।

प्रार्थी को विगत {duration} से शासन द्वारा स्वीकृत सामाजिक सुरक्षा पेंशन की धनराशि बैंक खाते में प्राप्त नहीं हो पा रही है। प्रार्थी द्वारा बैंक एवं स्थानीय कार्यालय में संपर्क किया गया, किंतु समाधान नहीं हो सका।

नागरिक द्वारा दर्ज समस्या का विवरण:
"{problem_hi}"

अतः श्रीमान जी से विनम्र प्रार्थना है कि प्रार्थी के पेंशन खाते (Aadhaar-DBT Seeding / NPCI Status) की जांच करवाकर रुकी हुई पेंशन राशि का त्वरित भुगतान कराने की कृपा करें।

संलग्न दस्तावेज (चेकलिस्ट):
1. प्रार्थी का आधार कार्ड प्रति
2. बैंक पासबुक प्रति (डीबीटी सीडेड खाता)
3. पेंशन स्वीकृति पत्र / पीपीओ संख्या (यदि उपलब्ध हो)

प्रार्थी का नाम: {citizen_name}
पता: ग्राम {village}, जिला {district}, {state}
आवेदन पंजीयन क्रमांक: {case_id}
सत्यापनकर्ता ऑपरेटर: {operator_id}
दिनांक: {date_str}
"""
    elif template_type == "water":
        body_hi = f"""सेवा में,
श्रीमान अधिशासी अभियंता / खंड विकास अधिकारी,
{department}
जिला: {district}, राज्य: {state}

विषय: ग्राम {village} में पेयजल आपूर्ति बाधित होने एवं तत्पर समाधान बाबत।

महोदय,
सविनय निवेदन है कि प्रार्थी {citizen_name}, ग्राम {village}, जिला {district} का निवासी है।

हमारे ग्राम/मोहल्ले में विगत {duration} से पेयजल की आपूर्ति पूरी तरह ठप/अनियमित है, जिससे ग्रामीणों एवं पशुओं को भारी कठिनाई का सामना करना पड़ रहा है।

नागरिक द्वारा दर्ज शिकायत का विवरण:
"{problem_hi}"

अतः श्रीमान जी से सादर अनुरोध है कि समस्या का संज्ञान लेते हुए जल निगम टीम भेजकर पाइपलाइन/नलकूप की तत्काल मरम्मत कराएं एवं नियमित जलापूर्ति बहाल करने की कृपा करें।

प्रार्थी: {citizen_name}
पता: ग्राम {village}, जिला {district}
दिनांक: {date_str}
"""
    else:
        body_hi = f"""सेवा में,
श्रीमान सक्षम प्राधिकारी,
{department}
जिला: {district}, राज्य: {state}

विषय: {issue_type} के निवारण हेतु प्रार्थना पत्र।

महोदय,
सविनय निवेदन है कि प्रार्थी {citizen_name}, निवासी: ग्राम/कस्बा {village}, जिला {district}, {state} निम्नलिखित लोक समस्या के संबंध में आपका ध्यान आकर्षित कराना चाहता/चाहती है:

समस्या विवरण (नागरिक के अनुसार):
"{problem_hi}"
अवधि: {duration}

अतः श्रीमान से सादर अनुरोध है कि उक्त मामले की निष्पक्ष जांच कराकर जनहित में त्वरित विधिक कार्यवाही सुनिश्चित करने का कष्ट करें।

प्रार्थी: {citizen_name}
पता: {village}, {district}
दिनांक: {date_str}
"""

    # 2. MARATHI TEMPLATES
    if template_type == "pension":
        body_mr = f"""प्रति,
मा. जिल्हा समाजकल्याण अधिकारी,
{department}
जिल्हा: {district}, राज्य: {state}

विषय: सामाजिक सुरक्षा पेन्शन मागील {duration} पासून बँक खात्यात जमा न झाल्याबाबत अर्ज.

महोदय,
सविनय विनंती अशी की, मी अर्जदार {citizen_name}, राहणार: {village}, तालुका/जिल्हा: {district}, {state} येथील रहिवासी आहे.

मला शासनाकडून मंजूर झालेली सामाजिक सुरक्षा पेन्शन मागील {duration} पासून मिळालेली नाही. स्थानिक बँक व कार्यालयात विचारणा केली असता अद्याप काहीही तोडगा निघालेला नाही.

नागरिकाने नोंदवलेला तक्रार तपशील:
"{problem_mr}"

तरी मा. अधिकाऱ्यांनी माझ्या खात्याची (Aadhaar-DBT / NPCI Seeding) पडताळणी करून प्रलंबित पेन्शन तात्काळ जमा करण्याचे आदेश द्यावेत ही नम्र विनंती.

सोबत जोडलेली कागदपत्रे:
१. आधार कार्ड प्रत
२. बँक पासबुक प्रत (आधार संलग्न)
३. पेन्शन मंजुरी पत्र क्रमांक (असल्यास)

अर्जदार: {citizen_name}
पत्ता: मु.पो. {village}, जिल्हा: {district}
नोंदणी क्रमांक: {case_id}
दिनांक: {date_str}
"""
    elif template_type == "water":
        body_mr = f"""प्रति,
मा. कार्यकारी अभियंता / गट विकास अधिकारी,
{department}
जिल्हा: {district}, राज्य: {state}

विषय: मौजे {village} येथे पिण्याच्या पाण्याचा पुरवठा खंडित असल्याबाबत तक्रार अर्ज.

महोदय,
सविनय सादर करतो की, मी {citizen_name}, राहणार {village}, जिल्हा {district} येथील ग्रामस्थ आहे.

आमच्या गावात मागील {duration} पासून सार्वजनिक नळयोजनेची पाईपलाईन फुटल्याने पिण्याच्या पाण्याची तीव्र टंचाई निर्माण झाली आहे. नागरिकांना व गुरांना पाण्यासाठी वणवण भटकावे लागत आहे.

तक्रार तपशील:
"{problem_mr}"

तरी जल जीवन मिशन / ग्रामपंचायत अंतर्गत तातडीने दुरुस्ती पथक पाठवून नियमित पाणीपुरवठा सुरू करावा ही विनंती.

अर्जदार: {citizen_name}
पत्ता: {village}, {district}
दिनांक: {date_str}
"""
    else:
        body_mr = f"""प्रति,
मा. सक्षम अधिकारी,
{department}
जिल्हा: {district}, राज्य: {state}

विषय: {issue_type} च्या निवारणाबाबत औपचारिक अर्ज.

महोदय,
सविनय अर्ज सादर करतो की, मी {citizen_name}, मु.पो. {village}, जिल्हा {district}, {state} येथील रहिवासी असून खालील समस्येकडे आपले लक्ष वेधू इच्छितो:

समस्या तपशील:
"{problem_mr}"
कालावधी: {duration}

तरी या तक्रारीची तात्काळ दखल घेऊन चौकशी करावी व जनहिताचा निर्णय घ्यावा ही नम्र विनंती.

अर्जदार: {citizen_name}
पत्ता: {village}, {district}
दिनांक: {date_str}
"""

    # 3. BENGALI TEMPLATES
    if template_type == "pension":
        body_bn = f"""প্রতি,
মাননীয় জেলা সমাজকল্যাণ আধিকারিক,
{department}
জেলা: {district}, রাজ্য: {state}

বিষয়: বিগত {duration} যাবত সামাজিক সুরক্ষা পেনশন না পাওয়া সংক্রান্ত আবেদনপত্র।

মহাশয়,
বিনীত নিবেদন এই যে, আমি {citizen_name}, গ্রাম/শহর: {village}, জেলা: {district}, {state}-এর স্থায়ী বাসিন্দা।

সরকারি অনুমোদিত সামাজিক সুরক্ষা পেনশনের টাকা বিগত {duration} যাবত আমার ব্যাংক অ্যাকাউন্টে জমা হচ্ছে না। স্থানীয় দপ্তর ও ব্যাংকে যোগাযোগ করা হলেও কোনো সদুত্তর মেলেনি।

নাগরিকের অভিযোগ বিবরণ:
"{problem_bn}"

অতএব মহাশয়ের নিকট বিনীত প্রার্থনা, আমার ব্যাংক অ্যাকাউন্টের (Aadhaar-DBT / NPCI) স্থিতি খতিয়ে দেখে দ্রুত বকেয়া পেনশন প্রদানের বিহিত ব্যবস্থা গ্রহণ করতে আজ্ঞা হয়।

সংযুক্ত নথিপত্র:
১. আধার কার্ডের প্রতিলিপি
২. ব্যাংক পাসবইয়ের প্রতিলিপি
৩. পেনশন মঞ্জুরি শংসাপত্র (যদি থাকে)

আবেদনকারী: {citizen_name}
ঠিকানা: গ্রাম {village}, জেলা {district}
কেস আইডি: {case_id}
তারিখ: {date_str}
"""
    elif template_type == "water":
        body_bn = f"""প্রতি,
মাননীয় নির্বাহী বাস্তুকার / ব্লক সমষ্টি উন্নয়ন আধিকারিক,
{department}
জেলা: {district}, রাজ্য: {state}

বিষয়: {village} গ্রামে পানীয় জল সরবরাহ বন্ধ থাকা ও দ্রুত সংস্কারের আবেদন।

মহাশয়,
বিনীত নিবেদন এই যে, আমি {citizen_name}, গ্রাম: {village}, জেলা: {district}-এর বাসিন্দা।

বিগত {duration} যাবত আমাদের এলাকায় জনস্বাস্থ্য কারিগরি পাইপলাইন অচল থাকায় পানীয় জলের তীব্র সংকট দেখা দিয়েছে। গ্রামবাসীদের চরম দুর্ভোগ পোহাতে হচ্ছে।

অভিযোগ বিবরণ:
"{problem_bn}"

অতএব দ্রুত পাইপলাইন সংস্কার করে স্বাভাবিক জল সরবরাহ পুনঃপ্রতিষ্ঠা করার বিনীত অনুরোধ জানাচ্ছি।

আবেদনকারী: {citizen_name}
ঠিকানা: {village}, {district}
তারিখ: {date_str}
"""
    else:
        body_bn = f"""প্রতি,
মাননীয় উপযুক্ত কর্তৃপক্ষ,
{department}
জেলা: {district}, রাজ্য: {state}

বিষয়: {issue_type} সংক্রান্ত নাগরিক অভিযোগ ও দ্রুত প্রতিকার প্রার্থনা।

মহাশয়,
বিনীত নিবেদন এই যে, আমি {citizen_name}, গ্রাম: {village}, জেলা: {district}, {state}-এর বাসিন্দা। নিম্নোক্ত জনস্বার্থমূলক বিষয়ে আপনার দৃষ্টি আকর্ষণ করছি:

অভিযোগের বিবরণ:
"{problem_bn}"
সময়কাল: {duration}

অতএব বিষয়টি গুরুত্ব সহকারে বিবেচনা করে দ্রুত প্রশাসনিক সমাধান প্রদান করার অনুরোধ জানাচ্ছি।

আবেদনকারী: {citizen_name}
ঠিকানা: {village}, {district}
তারিখ: {date_str}
"""

    # 4. ENGLISH TEMPLATES
    def to_latin(text: Any) -> str:
        s = str(text or '')
        s = re.sub(r'[\u0900-\u097F\u0980-\u09FF]', '', s)
        s = re.sub(r'\(\s*\)', '', s)
        return re.sub(r'\s+', ' ', s).strip()

    citizen_name_en = to_latin(citizen_name) or "Citizen"
    village_en = to_latin(village) or "Village"
    district_en = to_latin(district) or "District"
    state_en = to_latin(state) or "India"
    duration_en = normalize_duration_to_english(duration)
    issue_type_en = to_latin(issue_type) or "Public Welfare Grievance"
    department_en = to_latin(department) or meta["department_default"]

    if template_type == "pension":
        body_en = f"""To,
The District Social Welfare Officer,
{department_en}
District: {district_en}, State: {state_en}

SUBJECT: Formal Representation regarding Non-Disbursement of Social Welfare Pension for the past {duration_en}.

Respected Sir/Madam,

I, {citizen_name_en}, resident of Village/Town: {village_en}, District: {district_en}, {state_en}, respectfully submit this representation.

I am an eligible beneficiary of the Government Social Welfare Pension Scheme. However, the pension amount has not been credited to my bank account for the past {duration_en}. Inquiries at the local bank branch have not resolved the issue.

Citizen Statement / Specific Grievance:
"{problem_en}"

PRAYER / RELIEF SOUGHT:
It is respectfully prayed that my pension account, DBT seeding status, and NPCI mapper records be reviewed, and all overdue pension arrears be released into my bank account without further delay.

Enclosed Documents (Verification Checklist):
1. Copy of Aadhaar Card
2. Copy of Bank Passbook (NPCI/DBT Seeded)
3. Pension Sanction Order / PPO Number (if available)

Applicant: {citizen_name_en}
Address: Village {village_en}, District {district_en}, {state_en}
Case Reference Number: {case_id}
Verification Operator: {operator_id}
Date: {date_str}
"""
    elif template_type == "water":
        body_en = f"""To,
The Executive Engineer, Rural Water Supply / Block Development Officer,
{department_en}
District: {district_en}, State: {state_en}

SUBJECT: Urgent Petition regarding complete disruption of Drinking Water Supply in Village {village_en}.

Respected Sir/Madam,

I, {citizen_name_en}, resident of Village {village_en}, District: {district_en}, bring to your urgent attention the severe breakdown of potable drinking water supply in our area for the past {duration_en}.

Citizen Grievance Details:
"{problem_en}"

PRAYER / RELIEF SOUGHT:
We request immediate dispatch of a technical repair team to inspect the Jal Jeevan Mission pipeline / tubewell and restore safe drinking water supply immediately.

Applicant: {citizen_name_en}
Address: Village {village_en}, District {district_en}
Date: {date_str}
"""
    else:
        body_en = f"""To,
The Competent Grievance Redressal Authority,
{department_en}
District: {district_en}, State: {state_en}

SUBJECT: Formal Representation regarding {issue_type_en}.

Respected Sir/Madam,

I, {citizen_name_en}, resident of Village/Town: {village_en}, District: {district_en}, {state_en}, submit this formal grievance regarding:

Issue Description:
"{problem_en}"
Duration of Hardship: {duration_en}

It is requested that the concerned authorities take immediate cognizance of this matter and initiate necessary redressal in accordance with government citizen charters.

Applicant: {citizen_name_en}
Address: {village_en}, {district_en}
Date: {date_str}
"""

    disclaimer_en = "DISCLAIMER: This application is prepared through the Awaaz Adhikar Civic Workspace to assist the citizen in formalizing their spoken grievance. Reference links indicate statutory schemes and official portal procedures discovered via SerpApi; they do not constitute government endorsement or prior administrative approval."
    disclaimer_hi = "अस्वीकरण (DISCLAIMER): यह आवेदन पत्र नागरिक की मौखिक शिकायत को औपचारिक रूप देने हेतु 'आवाज़ अधिकार' ऑपरेटर वर्कस्पेस के माध्यम से तैयार किया गया है। उद्धृत संदर्भ लिंक SerpApi द्वारा खोजे गए प्रासंगिक सरकारी पोर्टल एवं मार्गदर्शिकाएं दर्शाते हैं; यह किसी पूर्व सरकारी स्वीकृति का प्रमाण नहीं हैं।"
    disclaimer_mr = "अस्वीकरण (DISCLAIMER): हा अर्ज नागरिकांच्या मौखिक तक्रारीला कायदेशीर स्वरूप देण्यासाठी 'आवाज अधिकार' प्रणालीद्वारे तयार करण्यात आला आहे. उद्धृत संदर्भ SerpApi द्वारे शोधलेले अधिकृत सरकारी पोर्टल दर्शवतात; हे पूर्वप्रशासकीय मान्यतेचे प्रमाणपत्र नाही."
    disclaimer_bn = "দাবিত্যাগ (DISCLAIMER): এই আবেদনপত্রটি নাগরিকের মৌখিক অভিযোগকে প্রাতিষ্ঠানিক রূপ দিতে 'আওয়াজ অধিকার' ওয়ার্কস্পেসের মাধ্যমে প্রস্তুত করা হয়েছে। উল্লেখিত তথ্যসূত্রগুলি SerpApi-এর মাধ্যমে সংগৃহীত প্রাসঙ্গিক সরকারি নির্দেশিকা নির্দেশ করে।"

    # Determine regional application based on selected language
    if lang == "mr":
        regional_title = meta.get("name_mr", meta["name"])
        body_regional = body_mr
        source_block_regional = source_block_mr
        disclaimer_regional = disclaimer_mr
        lang_display = "Marathi (मराठी)"
    elif lang == "bn":
        regional_title = meta.get("name_bn", meta["name"])
        body_regional = body_bn
        source_block_regional = source_block_bn
        disclaimer_regional = disclaimer_bn
        lang_display = "Bengali (বাংলা)"
    elif lang == "en":
        regional_title = meta["name"]
        body_regional = body_en
        source_block_regional = source_block_en
        disclaimer_regional = disclaimer_en
        lang_display = "English"
    else: # default hi
        regional_title = meta["name_hi"]
        body_regional = body_hi
        source_block_regional = source_block_hi
        disclaimer_regional = disclaimer_hi
        lang_display = "Hindi (हिंदी)"

    return {
        "case_id": case_id,
        "template_name": meta["name"],
        "template_version": meta["version"],
        "last_reviewed": meta["last_reviewed"],
        "date_generated": date_str,
        "language_primary": lang,
        "regional_language": {
            "code": lang,
            "display": lang_display,
            "title": regional_title,
            "body": body_regional,
            "sources_reference": source_block_regional,
            "disclaimer": disclaimer_regional
        },
        # For backward compatibility
        "hindi_application": {
            "title": regional_title,
            "body": body_regional,
            "sources_reference": source_block_regional,
            "disclaimer": disclaimer_regional
        },
        "english_application": {
            "title": meta["name"],
            "body": body_en,
            "sources_reference": source_block_en,
            "disclaimer": disclaimer_en
        }
    }
