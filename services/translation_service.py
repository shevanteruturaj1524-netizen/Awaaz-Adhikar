import re
from typing import Dict, Any

# Formal professional wording synthesizer and translation engine for Awaaz Adhikar.
# Preserves facts, proper nouns, and numbers without raw conversational dialect or untranslated snippets.

def clean_conversational_filler(text: str) -> str:
    """Removes conversational intros and outros from transcripts in Indian languages."""
    s = text.strip()
    # Remove intros
    s = re.sub(r'^(मेरा नाम\s+[^\।\.\n,]+(?:\।|\.|\,)?)\s*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'^(माझं नाव\s+[^\।\.\n,]+(?:\।|\.|\,)?)\s*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'^(माझे नाव\s+[^\।\.\n,]+(?:\।|\.|\,)?)\s*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'^(আমার নাম\s+[^\।\.\n,]+(?:\।|\.|\,)?)\s*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'^(my name is\s+[^\.\n,]+(?:\.|\,)?)\s*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'^(i am\s+[^\.\n,]+(?:\.|\,)?)\s*', '', s, flags=re.IGNORECASE)
    return s.strip()

def detect_grievance_category(text: str, scheme_code: str = "") -> str:
    """Classifies grievance into specific sub-category for high-fidelity professional legal/civic wording."""
    t = text.lower()
    
    # 1. Scholarship / student aid
    if scheme_code == "scholarship" or any(k in t for k in ["scholarship", "scholarships", "stipend", "fee", "student", "shishyavrutti", "chhatravritti", "छात्रवृत्ति", "स्कॉलरशिप", "শিক্ষাবৃত্তি", "ছাত্রবৃত্তি"]):
        return "scholarship"

    # 2. Land mutation (Dakhil Kharij)
    if any(k in t for k in ["mutation", "dakhil kharij", "dakhil-kharij", "dakhil", "namantaran", "दाखिल खारिज", "नामांतरण", "মিউটেশন", "biharbhumi", "jamabandi"]):
        return "land_mutation"

    # 3. Land encroachment / boundary dispute
    if any(k in t for k in ["अतिक्रमण", "कब्जा", "कब्ज़ा", "शेती", "दखल", "encroach", "land grab", "illegal possession", "boundary dispute"]):
        return "land_encroachment"
        
    # 4. Road / municipal drainage / civic infrastructure
    if scheme_code == "road" or any(k in t for k in ["road", "pothole", "potholes", "drainage", "sewer", "waterlogging", "street light", "municipal", "nagar nigam", "nagar palika", "safai", "sanitation", "sadak", "gaddha", "सड़क", "सड़क", "गड्ढा", "नाली", "রাস্তা", "নর্দমা", "रस्ता", "खड्डे"]):
        return "road"

    # 5. Electricity / power supply
    if scheme_code == "electricity" or any(k in t for k in ["बिजली", "विद्युत", "वीज", "বিদ্যুৎ", "electricity", "power cut", "meter", "voltage", "outage", "feeder", "transformer"]):
        return "electricity"

    # 6. Water supply disruption / broken infrastructure
    if scheme_code == "water" or any(k in t for k in ["पानी", "जल", "नल", "জল", "পাইপলাইন", "पाइपलाइन", "पाईपलाईन", "leakage", "water supply", "handpump", "borewell"]):
        return "water"

    # 7. Ration / PDS distribution
    if scheme_code == "ration" or any(k in t for k in ["ration", "राशन", "রেশন", "কোটা", "pds", "dealer", "dilar", "खाद्यान्न", "food grain"]):
        return "ration"

    # 8. Pension delay / non-receipt
    if scheme_code == "pension" or any(k in t for k in ["पेंशन", "पेन्शन", "পেনশন", "pension", "वृद्धावस्था", "विधवा", "दिव्यांग", "old age"]):
        return "pension"
        
    # 9. PM-KISAN / agricultural subsidy
    if scheme_code == "pmkisan" or any(k in t for k in ["pm kisan", "pm-kisan", "सन्मान निधी", "हप्ता", "हप्ते", "किस्त", "किसान", "কৃষক"]):
        return "pmkisan"
        
    # 10. Rural Housing / PMAY
    if scheme_code == "housing" or any(k in t for k in ["awas", "आवास", "घरकुल", "ঘর", "pmay", "makan", "colony"]):
        return "housing"
        
    return "general"

def normalize_duration_to_english(duration_str: str) -> str:
    if not duration_str:
        return "an extended period"
    s = str(duration_str).strip()
    dev_digits = {"०": "0", "१": "1", "२": "2", "३": "3", "४": "4", "५": "5", "६": "6", "७": "7", "८": "8", "९": "9"}
    for d, val in dev_digits.items():
        s = s.replace(d, val)
    ben_digits = {"০": "0", "১": "1", "২": "2", "৩": "3", "৪": "4", "৫": "5", "৬": "6", "৭": "7", "৮": "8", "৯": "9"}
    for d, val in ben_digits.items():
        s = s.replace(d, val)
    replacements = [
        (r'\b(mahine|mahino|mahina|महीने|महीनों|महिन्यांपासून|महिने|मास|মাসের|মাস)\b', 'months'),
        (r'\b(din|days?|दिवस|दिन|दिनों|দিনের|দিন)\b', 'days'),
        (r'\b(saal|years?|साल|सालों|वर्षांपासून|वर्षे|वर्ष|বছরের|বছর)\b', 'years'),
        (r'\b(hafte|weeks?|हफ्ते|आठवड्यांपासून|सप्ताह|সপ্তাহের|সপ্তাহ)\b', 'weeks'),
    ]
    for pattern, rep in replacements:
        s = re.sub(pattern, rep, s, flags=re.IGNORECASE)
    s = re.sub(r'[\u0900-\u097F\u0980-\u09FF]', '', s).strip()
    return s if s else "an extended period"

def synthesize_professional_wording(transcript: str, language: str, extracted_fields: Dict[str, Any]) -> Dict[str, str]:
    """
    Synthesizes:
    - english: Professional, formal English application wording (never raw transcript)
    - regional: Formal, administrative regional language wording in the citizen's selected language
    - original: Preserved raw citizen statement
    """
    raw_text = transcript.strip()
    cleaned = clean_conversational_filler(raw_text)
    
    citizen_name = extracted_fields.get("citizen_name") or "Citizen"
    village = extracted_fields.get("village") or "the village"
    district = extracted_fields.get("district") or "the district"
    state = extracted_fields.get("state") or "India"
    duration = extracted_fields.get("duration") or "an extended period"
    scheme_code = extracted_fields.get("scheme_code") or ""
    
    # English sanitized equivalents
    citizen_name_en = re.sub(r'[\u0900-\u097F\u0980-\u09FF]', '', str(citizen_name)).strip() or "Citizen"
    village_en = re.sub(r'[\u0900-\u097F\u0980-\u09FF]', '', str(village)).strip() or "the village"
    district_en = re.sub(r'[\u0900-\u097F\u0980-\u09FF]', '', str(district)).strip() or "the district"
    state_en = re.sub(r'[\u0900-\u097F\u0980-\u09FF]', '', str(state)).strip() or "India"
    duration_en = normalize_duration_to_english(duration)
    issue_type_en = re.sub(r'[\u0900-\u097F\u0980-\u09FF]', '', str(extracted_fields.get('issue_type', 'a public civic matter'))).strip() or "a public civic matter"
    
    category = detect_grievance_category(raw_text, scheme_code)
    
    # 1. SCHOLARSHIP / STUDENT DISBURSEMENT
    if category == "scholarship":
        english = (
            f"I am an eligible student submitting this formal representation regarding the delayed disbursement of my Student Scholarship in Village/Town: {village_en}, District: {district_en}, {state_en}. "
            f"The scholarship disbursement has been pending for the past {duration_en} despite successful institutional verification. "
            f"I respectfully request the competent education and social welfare authorities to review my application, verify my DBT account status, and expedite the release of the pending scholarship amount."
        )
        hindi = (
            f"प्रार्थी ग्राम/कस्बा: {village}, जिला: {district}, {state} का निवासी एवं छात्र है। "
            f"प्रार्थी द्वारा छात्रवृत्ति (Scholarship) हेतु आवेदन किया गया था, किंतु विगत {duration} से छात्रवृत्ति की स्वीकृत धनराशि बैंक खाते में प्राप्त नहीं हुई है। "
            f"संस्थान स्तर से सत्यापन पूर्ण हो चुका है। अतः सक्षम प्राधिकारी से सादर अनुरोध है कि छात्रवृत्ति आवेदन एवं आधार-डीबीटी स्थिति की जांच कराकर रुकी हुई छात्रवृत्ति राशि का त्वरित भुगतान कराने की कृपा करें।"
        )
        marathi = (
            f"मी अर्जदार मु.पो. {village}, जिल्हा: {district}, {state} येथील विद्यार्थी असून मला मंजूर झालेली शिष्यवृत्ती (Scholarship) मागील {duration} पासून बँक खात्यात जमा झालेली नाही. "
            f"शैक्षणिक संस्थेमार्फत पडताळणी पूर्ण झाली आहे. तरी सक्षम अधिकाऱ्यांनी अर्ज व आधार-डीबीटी संलग्नतेची तपासणी करून प्रलंबित शिष्यवृत्ती तात्काळ वितरित करावी ही नम्र विनंती."
        )
        bengali = (
            f"আমি গ্রাম/শহর: {village}, জেলা: {district}, {state}-এর একজন ছাত্র/ছাত্রী। "
            f"বিগত {duration} ধরে আমার প্রাপ্য ছাত্রবৃত্তি (Scholarship)-র অর্থ ব্যাংক একাউন্টে জমা পড়েনি, যদিও শিক্ষাপ্রতিষ্ঠান স্তরে যাচাই সম্পন্ন হয়েছে। "
            f"অতএব, উপযুক্ত কর্তৃপক্ষের নিকট বিনীত অনুরোধ, আবেদন ও আধার-ডিবিটি স্ট্যাটাস খতিয়ে দেখে বকেয়া বৃত্তির অর্থ অবিলম্বে প্রদান করা হোক।"
        )

    # 2. LAND MUTATION (DAKHIL KHARIJ)
    elif category == "land_mutation":
        english = (
            f"I am submitting this formal representation regarding the pending Land Mutation (Dakhil Kharij) application and revenue record updation for my registered land in Village/Town: {village_en}, District: {district_en}, {state_en}, which has remained pending for the past {duration_en}. "
            f"I possess all valid registered title deeds and official mutation receipts. "
            f"I respectfully request the competent revenue authorities to conduct necessary verification and expedite the issuance of the mutation order in accordance with statutory rules."
        )
        hindi = (
            f"प्रार्थी ग्राम/कस्बा: {village}, जिला: {district}, {state} का निवासी है। "
            f"प्रार्थी द्वारा अपनी भूमि के दाखिल खारिज (Mutation) / नामांतरण हेतु नियमानुसार आवेदन किया गया था, जो विगत {duration} से लंबित है। "
            f"प्रार्थी के पास वैध रजिस्टर्ड बैनामा एवं राजस्व साक्ष्य उपलब्ध हैं। अतः सक्षम राजस्व प्राधिकारी से सादर अनुरोध है कि प्रकरण का संज्ञान लेकर दाखिल खारिज की कार्यवाही शीघ्र संपन्न कराने की कृपा करें।"
        )
        marathi = (
            f"मी अर्जदार मु.पो. {village}, जिल्हा: {district}, {state} येथील रहिवासी असून माझ्या जमिनीच्या फेरफार (Mutation) / सातबारा नोंदीचा अर्ज मागील {duration} पासून प्रलंबित आहे. "
            f"माझ्याकडे अधिकृत खरेदीखत व आवश्यक महसूल कागदपत्रे उपलब्ध आहेत. तरी सक्षम महसूल अधिकाऱ्यांनी तात्काळ चौकशी करून फेरफार नोंद मंजूर करावी ही नम्र विनंती."
        )
        bengali = (
            f"আমি গ্রাম/শহর: {village}, জেলা: {district}, {state}-এর বাসিন্দা। "
            f"আমার বৈধ জমির দাখিল খারিজ (মিউটেশন) সংক্রান্ত আবেদন বিগত {duration} ধরে সংশ্লিষ্ট রাজস্ব দপ্তরে অনিষ্পন্ন অবস্থায় পড়ে রয়েছে। "
            f"আমার নিকট বৈধ দলিল ও খাজনার রশিদ রয়েছে। অতএব, রাজস্ব কর্তৃপক্ষের নিকট অনুরোধ, দ্রুত মিউটেশন প্রক্রিয়া সম্পন্ন করা হোক।"
        )

    # 3. ROAD POTHOLES & MUNICIPAL CIVIC INFRASTRUCTURE
    elif category == "road":
        english = (
            f"I am submitting this formal complaint regarding severely damaged road infrastructure, hazardous deep potholes, and broken drainage in Village/Town/Ward: {village_en}, District: {district_en}, {state_en}, which has persisted for the past {duration_en}. "
            f"This condition poses severe danger to commuters and local public safety. "
            f"I respectfully request the municipal corporation and public works authorities to immediately inspect the location, resurface the road, and clear the drainage blockage."
        )
        hindi = (
            f"प्रार्थी ग्राम/कस्बा/वार्ड: {village}, जिला: {district}, {state} का निवासी है। "
            f"हमारे क्षेत्र की मुख्य सड़क अत्यंत जर्जर स्थिति में है तथा विगत {duration} से गहरे गड्ढे एवं जलभराव/नाली अवरोध के कारण दुर्घटनाओं की गंभीर आशंका बनी हुई है। "
            f"अतः सक्षम नगर निगम / लोक निर्माण विभाग से सादर अनुरोध है कि मौके का निरीक्षण कर सड़क की तत्काल मरम्मत एवं जलनिकासी व्यवस्था दुरुस्त कराने की कृपा करें।"
        )
        marathi = (
            f"मी अर्जदार मु.पो./प्रभाग: {village}, जिल्हा: {district}, {state} येथील रहिवासी असून आमच्या परिसरातील मुख्य रस्त्यावर मोठमोठे खड्डे पडले असून सांडपाण्याचा निचरा न झाल्याने मागील {duration} पासून नागरिकांची मोठी गैरसोय होत आहे. "
            f"तरी महानगरपालिका / सार्वजनिक बांधकाम विभागाने प्रत्यक्ष पाहणी करून रस्त्याची तातडीने दुरुस्ती करावी ही नम्र विनंती."
        )
        bengali = (
            f"আমি গ্রাম/শহর/ওয়ার্ড: {village}, জেলা: {district}, {state}-এর অধিবাসী। "
            f"আমাদের এলাকার প্রধান রাস্তাটি অত্যন্ত বেহাল এবং বিগত {duration} ধরে মারাত্মক খানাখন্দ ও নিকাশি সমস্যার কারণে যাতায়াত বিপজ্জনক হয়ে উঠেছে। "
            f"অতএব, পৌরসভা / পূর্ত দপ্তরের নিকট বিনীত অনুরোধ, অবিলম্বে রাস্তা সংস্কার ও নর্দমা পরিষ্কারের কার্যকর ব্যবস্থা গ্রহণ করা হোক।"
        )

    # 4. ELECTRICITY SUPPLY & DISCOM OUTAGE
    elif category == "electricity":
        english = (
            f"I am submitting this formal grievance regarding persistent electricity supply disruptions, prolonged power outages, and infrastructure faults in Village/Town: {village_en}, District: {district_en}, {state_en}, which have persisted for the past {duration_en}. "
            f"This has caused severe hardship to local residents and economic activity. "
            f"I respectfully request the electricity distribution company (DISCOM) and power department to inspect the local feeder/transformer, rectify the fault, and restore uninterrupted power supply."
        )
        hindi = (
            f"प्रार्थी ग्राम/कस्बा: {village}, जिला: {district}, {state} का निवासी है। "
            f"हमारे क्षेत्र में विगत {duration} से विद्युत आपूर्ति की गंभीर समस्या बनी हुई है तथा बार-बार अघोषित बिजली कटौती एवं लो-वोल्टेज के कारण जनजीवन बुरी तरह प्रभावित है। "
            f"अतः सक्षम विद्युत वितरण निगम (DISCOM) से सादर अनुरोध है कि स्थानीय ट्रांसफार्मर/फीडर की तकनीकी जांच कराकर निर्बाध विद्युत आपूर्ति बहाल करने की कृपा करें।"
        )
        marathi = (
            f"मी अर्जदार मु.पो. {village}, जिल्हा: {district}, {state} येथील रहिवासी असून आमच्या भागात मागील {duration} पासून वीजपुरवठा वारंवार खंडित होत आहे आणि सततच्या वीज कपातीमुळे नागरिकांचे मोठे हाल होत आहेत. "
            f"तरी विद्युत वितरण कंपनीने (महावितरण) तातडीने तपासणी करून सुरळीत व अखंड वीजपुरवठा पूर्ववत सुरू करावा ही नम्र विनंती."
        )
        bengali = (
            f"আমি গ্রাম/শহর: {village}, জেলা: {district}, {state}-এর বাসিন্দা। "
            f"আমাদের এলাকায় বিগত {duration} ধরে তীব্র বিদ্যুৎ বিভ্রাট ও লো-ভোল্টেজের কারণে জনজীবন বিপর্যস্ত। "
            f"অতএব, বিদ্যুৎ বণ্টন কর্তৃপক্ষের নিকট অনুরোধ, দ্রুত ট্রান্সফর্মার/ফিডার মেরামতের মাধ্যমে নিয়মিত বিদ্যুৎ সরবরাহ নিশ্চিত করা হোক।"
        )

    # 5. LAND ENCROACHMENT / BOUNDARY DISPUTE
    elif category == "land_encroachment":
        english = (
            "I am reporting an alleged unauthorized encroachment on my land by another party. "
            "I possess the relevant land ownership documents and revenue records. "
            "I respectfully request the competent revenue and administrative authorities to inspect the site, "
            "verify the land records, and initiate appropriate proceedings."
        )
        hindi = (
            "प्रार्थी सादर सूचित करता है कि मेरी निजी भूमि पर अन्य पक्ष द्वारा कथित अनाधिकृत अतिक्रमण किया गया है। "
            "प्रार्थी के पास भूमि के वैध अभिलेख एवं राजस्व दस्तावेज उपलब्ध हैं। "
            "अतः सक्षम राजस्व एवं प्रशासनिक प्राधिकारियों से सादर अनुरोध है कि मौके का निरीक्षण कर, "
            "भूमि अभिलेखों का सत्यापन करें तथा नियमानुसार आवश्यक वैधानिक कार्यवाही करने की कृपा करें।"
        )
        marathi = (
            "मी अर्जदार कळवितो की, माझ्या मालकीच्या जमिनीवर दुसऱ्या व्यक्तीकडून कथित अनधिकृत अतिक्रमण करण्यात आले आहे. "
            "माझ्याकडे जमिनीच्या मालकीची अधिकृत कागदपत्रे व महसूल नोंदी उपलब्ध आहेत. "
            "तरी सक्षम महसूल व संबंधित प्रशासकीय अधिकाऱ्यांनी प्रत्यक्ष जागेची पाहणी करून, "
            "कागदपत्रांची पडताळणी करावी व आवश्यक ती योग्य कायदेशीर कार्यवाही करावी ही नम्र विनंती."
        )
        bengali = (
            "আমি বিনীতভাবে আবেদন জানাচ্ছি যে, আমার ব্যক্তিগত জমির ওপর অপর পক্ষ কর্তৃক অননুমোদিত জবরদখল করা হয়েছে। "
            "আমার নিকট উক্ত জমির বৈধ মালিকানা সংক্রান্ত নথিপত্র ও রাজস্ব রেকর্ড সংরক্ষিত রয়েছে। "
            "অতএব, সংশ্লিষ্ট রাজস্ব ও প্রশাসনিক কর্তৃপক্ষের নিকট বিনীত অনুরোধ, সরেজমিনে পরিদর্শনপূর্বক "
            "নথিপত্র যাচাই করে প্রয়োজনীয় আইনানুগ ব্যবস্থা গ্রহণ করার অনুরোধ জানাচ্ছি।"
        )

    # 6. PENSION GRIEVANCE
    elif category == "pension":
        english = (
            f"I am an eligible beneficiary under the Social Welfare Pension Scheme. "
            f"I state that my monthly pension entitlement has not been credited to my bank account for the past {duration_en}. "
            f"Despite previous inquiries at the local level, the disbursement remains overdue. "
            f"I request administrative review of my Aadhaar-DBT / NPCI bank seeding status and expedited release of all pending arrears."
        )
        hindi = (
            f"प्रार्थी शासन द्वारा संचालित सामाजिक सुरक्षा पेंशन योजना का पात्र लाभार्थी है। "
            f"प्रार्थी को विगत {duration} से शासन द्वारा स्वीकृत पेंशन धनराशि बैंक खाते में प्राप्त नहीं हो पा रही है। "
            f"स्थानीय स्तर पर विचार-विमर्श करने के उपरांत भी समस्या का समाधान नहीं हो सका है। "
            f"अतः आधार-डीबीटी बैंक सीडिंग की जांच करवाकर रुकी हुई पेंशन राशि का त्वरित भुगतान कराने की कृपा करें।"
        )
        marathi = (
            f"मी अर्जदार सामाजिक सुरक्षा पेन्शन योजनेचा अधिकृत लाभार्थी असून, मला मागील {duration} पासून "
            f"शासनाकडून मंजूर झालेली पेन्शनची रक्कम बँक खात्यात प्राप्त झालेली नाही. "
            f"स्थानिक कार्यालयात विचारणा करूनही अद्याप निराकरण झालेले नाही. "
            f"तरी बँक खात्याची व आधार-डीबीटी संलग्नतेची तपासणी करून प्रलंबित पेन्शन तात्काळ जमा करावी ही नम्र विनंती."
        )
        bengali = (
            f"আমি সামাজিক সুরক্ষা পেনশন প্রকল্পের একজন নথিভুক্ত বৈধ সুবিধাভোগী। "
            f"বিগত {duration} ধরে আমার ব্যাংক একাউন্টে সরকারি অনুদানকৃত পেনশনের অর্থ জমা পড়েনি। "
            f"স্থানীয় স্তরে যোগাযোগ করেও সমস্যাটির সমাধান সম্ভব হয়নি। "
            f"অতএব, আধার-ডিবিটি ব্যাংক সংযোগ অবিলম্বে যাচাই করে বকেয়া পেনশনের সমুদয় অর্থ প্রদানের ব্যবস্থা করা হোক।"
        )

    # 7. DRINKING WATER SUPPLY DISRUPTION
    elif category == "water":
        english = (
            f"I am reporting a severe breakdown and disruption of the potable drinking water supply in Village {village_en}, "
            f"District: {district_en}, which has persisted for the past {duration_en} due to damaged pipeline/pumping infrastructure. "
            f"This has caused acute hardship to local households and livestock. "
            f"I request the urgent dispatch of a technical repair team under the Rural Water Supply / Jal Jeevan Mission "
            f"to repair the defect and restore regular safe water supply."
        )
        hindi = (
            f"ग्राम {village}, जिला {district} में मुख्य पेयजल वितरण पाइपलाइन / नलकूप क्षतिग्रस्त होने के कारण "
            f"विगत {duration} से स्वच्छ पेयजल की आपूर्ति पूर्णतः बाधित है। "
            f"इससे ग्रामवासियों एवं मवेशियों को भीषण जल संकट का सामना करना पड़ रहा है। "
            f"अतः जल जीवन मिशन / पेयजल विभाग की तकनीकी टीम भेजकर पाइपलाइन की तत्काल मरम्मत कराने एवं नियमित जलापूर्ति बहाल करने की कृपा करें।"
        )
        marathi = (
            f"मौजे {village}, जिल्हा {district} येथे पिण्याच्या पाण्याच्या मुख्य पाईपलाईनमध्ये बिघाड झाल्याने "
            f"मागील {duration} पासून पाणीपुरवठा पूर्णपणे खंडित झाला आहे. "
            f"यामुळे ग्रामस्थ व गुरांना पिण्याच्या पाण्यासाठी तीव्र हाल सोसावे लागत आहेत. "
            f"तरी जल जीवन मिशन / ग्रामपंचायत अंतर्गत तातडीने दुरुस्ती पथक पाठवून नियमित पाणीपुरवठा पूर्ववत सुरू करावा ही नम्र विनंती."
        )
        bengali = (
            f"আমাদের গ্রামে ({village}, জেলা: {district}) পানীয় জলের মূল পাইপলাইন ক্ষতিগ্রস্ত হওয়ার ফলে "
            f"বিগত {duration} ধরে পানীয় জল সরবরাহ সম্পূর্ণ বন্ধ রয়েছে। "
            f"এর ফলে সমগ্র গ্রামবাসীকে চরম দুর্ভোগ সহ্য করতে হচ্ছে। "
            f"অতএব, জল জীবন মিশন / জনস্বাস্থ্য কারিগরি বিভাগের পক্ষ থেকে দ্রুত মেরামতের ব্যবস্থা করে নিয়মিত জল সরবরাহ চালু করার অনুরোধ জানাচ্ছি।"
        )

    # 8. PM-KISAN SUBSIDY
    elif category == "pmkisan":
        english = (
            f"I am an eligible beneficiary farmer under the PM-KISAN Samman Nidhi scheme. "
            f"I report that my direct benefit installments have not been credited to my bank account for the past {duration_en}. "
            f"I request that my land revenue record verification and Aadhaar-DBT bank seeding status be reviewed "
            f"to release all pending installment payments."
        )
        hindi = (
            f"मैं प्रधानमंत्री किसान सम्मान निधि (PM-KISAN) योजना के अंतर्गत पंजीकृत पात्र किसान हूँ। "
            f"मुझे विगत {duration} से योजना की देय किस्त राशि बैंक खाते में प्राप्त नहीं हुई है। "
            f"अतः मेरे भू-अभिलेखों एवं बैंक खाते की आधार-डीबीटी सीडिंग की समीक्षा कर रोकी गई किस्त राशि शीघ्र अंतरित कराने की कृपा करें।"
        )
        marathi = (
            f"मी पंतप्रधान किसान सन्मान निधी (PM-KISAN) योजनेचा अधिकृत लाभार्थी शेतकरी असून, "
            f"मला मागील {duration} पासून योजनेचे देय हप्ते बँक खात्यात प्राप्त झालेले नाहीत. "
            f"तरी माझ्या महसूल नोंदी व बँक आधार-डीबीटी पडताळणी करून प्रलंबित हप्त्यांची रक्कम तात्काळ जमा करण्यात यावी ही नम्र विनंती."
        )
        bengali = (
            f"আমি প্রধানমন্ত্রী কিষাণ সম্মান নিধি (PM-KISAN) প্রকল্পের একজন বৈধ সুবিধাভোগী কৃষক। "
            f"বিগত {duration} ধরে আমার ব্যাংক একাউন্টে প্রকল্পের প্রাপ্য কিস্তির অর্থ জমা হয়নি। "
            f"অতএব, জমির রেকর্ড ও ব্যাংক আধার-ডিবিটি স্ট্যাটাস পর্যালোচনা করে বকেয়া কিস্তির টাকা দ্রুত ছাড় করার অনুরোধ জানাচ্ছি।"
        )

    # 9. RATION / PDS SUPPLY
    elif category == "ration":
        english = (
            f"I report an irregularity regarding my entitled quota of subsidized food grains under the Public Distribution System (PDS). "
            f"My ration entitlement has been disrupted/blocked for the past {duration_en}. "
            f"I request an official inquiry and immediate restoration of the subsidized food grain distribution."
        )
        hindi = (
            f"मैं राष्ट्रीय खाद्य सुरक्षा अधिनियम (NFSA) / सार्वजनिक वितरण प्रणाली के अंतर्गत वैध राशन कार्डधारक हूँ। "
            f"विगत {duration} से खाद्यान्न वितरण में अनियमितता / राशन कार्ड बाधित होने के कारण परिवार को राशन प्राप्त नहीं हो पा रहा है। "
            f"अतः मामले की जांच कर राशन आपूर्ति नियमित कराने की कृपा करें।"
        )
        marathi = (
            f"मी सार्वजनिक अन्नधान्य वितरण प्रणाली (PDS) अंतर्गत अधिकृत रेशनकार्डधारक असून, "
            f"मागील {duration} पासून धान्य वितरणात अनियमितता झाल्याने हक्काचे अन्नधान्य मिळणे बंद झाले आहे. "
            f"तरी या तक्रारीची चौकशी करून रेशनकार्ड पूर्ववत सुरू करावे व नियमित धान्य वाटप सुनिश्चित करावे ही विनंती."
        )
        bengali = (
            f"আমি গণবণ্টন ব্যবস্থার (PDS) অধীনে বৈধ রেশন কার্ডধারী সুবিধাভোগী। "
            f"বিগত {duration} ধরে রেশন বণ্টন অনিয়মিত হওয়ায় পরিবারভুক্ত খাদ্যশস্য বরাদ্দ পেতে গুরুতর বিঘ্ন ঘটছে। "
            f"অতএব, বিষয়টি তদন্ত করে নির্ধারিত খাদ্যশস্য বণ্টন স্বাভাবিক করার অনুরোধ জানাচ্ছি।"
        )

    # 10. GENERAL CIVIC / ADMINISTRATIVE GRIEVANCE
    # 10. GENERAL CIVIC / ADMINISTRATIVE GRIEVANCE
    else:
        # Avoid putting verbatim regional characters in the English sentence
        has_non_latin = any(ord(c) > 127 for c in cleaned)
        if has_non_latin or len(cleaned) <= 10:
            english = (
                f"I am submitting this formal representation regarding {issue_type_en} "
                f"in Village/Town: {village_en}, District: {district_en}, {state_en}, which has persisted for the past {duration_en}. "
                f"I possess the relevant supporting documents and respectfully request the competent authority to examine "
                f"the matter and initiate appropriate administrative redressal."
            )
        else:
            english = (
                f"I am submitting this formal representation regarding: '{cleaned}'. "
                f"The matter has persisted for {duration_en} in Village/Town: {village_en}, District: {district_en}. "
                f"I respectfully request that the competent authority examine the facts and initiate appropriate administrative action."
            )
            
        hindi = (
            f"प्रार्थी ग्राम/कस्बा: {village}, जिला: {district}, {state} में विगत {duration} से व्याप्त "
            f"{extracted_fields.get('issue_type', 'जनसमस्या')} के संबंध में यह औपचारिक प्रार्थना पत्र प्रस्तुत कर रहा है। "
            f"प्रार्थी के पास आवश्यक संबंधित साक्ष्य उपलब्ध हैं। अतः सक्षम प्राधिकारी से सादर अनुरोध है कि प्रकरण की जांच कर "
            f"उचित प्रशासनिक निवारण सुनिश्चित करने की कृपा करें।"
        )
        marathi = (
            f"मी अर्जदार मु.पो. {village}, जिल्हा: {district}, {state} येथील रहिवासी असून मागील {duration} पासून उद्भवलेल्या "
            f"{extracted_fields.get('issue_type', 'नागरी समसमस्या')}बाबत हा औपचारिक अर्ज सादर करीत आहे. "
            f"माझ्याकडे आवश्यक कागदपत्रे उपलब्ध आहेत. तरी सक्षम अधिकाऱ्यांनी सदर प्रकरणाची सखोल चौकशी करून "
            f"योग्य ती प्रशासकीय कार्यवाही करावी ही नम्र विनंती."
        )
        bengali = (
            f"আমি গ্রাম/শহর: {village}, জেলা: {district}, {state}-এর অধিবাসী হিসেবে বিগত {duration} ধরে চলমান "
            f"উক্ত নাগরিক সমস্যার বিষয়ে এই আনুষ্ঠানিক আবেদনপত্র পেশ করছি। "
            f"আমার নিকট সংশ্লিষ্ট প্রমাণাদি সংরক্ষিত রয়েছে। অতএব, উপযুক্ত কর্তৃপক্ষের নিকট অনুরোধ, বিষয়টি তদন্ত করে "
            f"প্রয়োজনীয় প্রশাসনিক পদক্ষেপ গ্রহণ করা হোক।"
        )

    # Final guarantee: strip any accidental Devanagari or Bengali characters from english
    english = re.sub(r'[\u0900-\u097F\u0980-\u09FF]', '', english)
    english = re.sub(r'\s+', ' ', english).strip()

    # Select the regional wording based on citizen's selected language
    if language == "mr":
        selected_regional = marathi
    elif language == "bn":
        selected_regional = bengali
    elif language == "en":
        selected_regional = english
    else: # default hi
        selected_regional = hindi

    return {
        "original": raw_text,
        "english": english,
        "regional": selected_regional,
        "language": language,
        "category": category,
        "verified_by_operator": False
    }
