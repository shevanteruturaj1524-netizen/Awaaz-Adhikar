// AWAAZ ADHIKAR - CIVIC GRIEVANCE WORKSPACE JAVASCRIPT ENGINE

// Global State
let currentCase = {
  id: "CASE-NEW",
  language: "hi",
  consent: true,
  citizen_name: "",
  original_transcript: "",
  edited_transcript: "",
  extracted_fields: {
    citizen_name: "",
    village: "",
    state: "",
    district: "",
    duration: "",
    issue_type: "",
    scheme: "",
    department: ""
  },
  missing_fields: [],
  contradictions: [],
  search_query: "",
  sources: [],
  claim_source_mappings: [],
  verification_status: "Needs Review",
  checklist_state: {},
  template_type: "general",
  template_version: "v1.2-2026",
  generated_documents: {},
  audio_file: null
};

let currentStep = 1;
let currentView = "landing";
let currentUser = null; // Stored operator session
let ADMIN_DIVISIONS = {}; // Loaded from /api/locations
let extractionRequestGeneration = 0;
let sourceSearchGeneration = 0;
let sourceSearchController = null;

// Step gating: tracks which steps have been successfully completed
// Step N being in completedSteps means the user may proceed to step N+1
let completedSteps = new Set();

// Media & Speech Recognition State
let mediaStream = null;
let mediaRecorder = null;
let recordedAudioChunks = [];
let recordedAudioBlob = null;
let recordedAudioUrl = null;
let isRecording = false;
let recordTimerInterval = null;
let recordSeconds = 0;
let recognition = null;

// i18n Translation Dictionary
const TRANSLATIONS = {
  hi: {
    brand_sub: "एआई-संचालित नागरिक शिकायत प्रलेखन एवं सत्यापन प्रणाली",
    landing_tagline: "सार्वजनिक सेवा नागरिक शिकायत सहायता केंद्र",
    landing_hero_msg: "अपनी समस्या अपनी भाषा में बताएं। आवाज़ अधिकार आपकी बात समझने, संबंधित आधिकारिक सरकारी जानकारी ढूँढने और आवेदन तैयार करने में ऑपरेटर की मदद करता है।",
    how_it_works_title: "आवाज़ अधिकार कैसे कार्य करता है",
    nav_dashboard: "ऑपरेटर डैशबोर्ड",
    nav_workspace: "शिकायत कार्यक्षेत्र",
    dash_welcome: "ग्रामीण जन शिकायत प्रलेखन केंद्र",
    step1_nav: "१. अपनी समस्या बताइए",
    step2_nav: "२. जानकारी समीक्षा",
    step3_nav: "३. सरकारी जानकारी खोज",
    step4_nav: "४. आवेदन पत्र तैयार",
    guide_step1: "नमस्ते। अपनी समस्या बताइए।",
    guide_step2: "कृपया निकाली गई जानकारी की समीक्षा करें और पुष्टि करें।",
    guide_step3: "हम आधिकारिक सरकारी पोर्टल और नियम खोज रहे हैं।",
    guide_step4: "आपका द्विभाषी आवेदन पत्र तैयार है। आप इसे देख सकते हैं और डाउनलोड कर सकते हैं।",
    btn_listen: "सुनें / Listen",
    ai_voice_guide: "आवाज़ सहायक",
    ai_confirmation_label: "आपकी बात की पुष्टि",
    confirmation_yes: "✓ हाँ, आगे बढ़ें",
    confirmation_edit: "✏ सुधारें",
    record_status_idle: "शिकायत की रिकॉर्डिंग शुरू करने के लिए नीचे दबाएँ",
    record_supported: "हिंदी, मराठी, बंगाली और अंग्रेज़ी बोलें",
    stt_live: "● आवाज़ पहचानी जा रही है",
    lbl_transcript_input: "नागरिक का कथन / टेक्स्ट इनपुट:",
    btn_search_sources: "🔎 Search Official Gov Sources via SerpApi →",
    btn_create_app: "📄 Create Application →",
    btn_download_pdf: "📥 Download PDF (.pdf)"
  },
  mr: {
    brand_sub: "एआय-सक्षम नागरिक तक्रार नोंदणी व पडताळणी प्रणाली",
    landing_tagline: "लोकसेवा नागरिक तक्रार निवारण सहाय्य केंद्र",
    landing_hero_msg: "आपली समस्या आपल्या भाषेत सांगा. आवाज अधिकार आपले म्हणणे समजून घेणे, संबंधित अधिकृत सरकारी माहिती शोधणे आणि अर्ज तयार करण्यात ऑपरेटरला मदत करतो.",
    how_it_works_title: "आवाज अधिकार कसे कार्य करते",
    nav_dashboard: "ऑपरेटर डॅशबोर्ड",
    nav_workspace: "तक्रार कार्यक्षेत्र",
    dash_welcome: "ग्रामीण नागरिक तक्रार नोंदणी केंद्र",
    step1_nav: "१. आपली समस्या सांगा",
    step2_nav: "२. माहिती पडताळणी",
    step3_nav: "३. शासकीय माहिती शोध",
    step4_nav: "४. अर्ज तयार आहे",
    guide_step1: "नमस्कार. आपली समस्या सांगा.",
    guide_step2: "कृपया नोंदवलेल्या माहितीची तपासणी करा आणि खात्री करा.",
    guide_step3: "आम्ही अधिकृत शासकीय पोर्टल आणि नियम शोधत आहोत.",
    guide_step4: "आपला द्विभाषिक अर्ज तयार आहे. आपण तो पाहू शकता आणि डाउनलोड करू शकता.",
    btn_listen: "ऐका / Listen",
    ai_voice_guide: "आवाज सहाय्यक",
    ai_confirmation_label: "तुमच्या बोलण्याची खात्री",
    confirmation_yes: "✓ होय, पुढे जा",
    confirmation_edit: "✏ दुरुस्त करा",
    record_status_idle: "तक्रार नोंदवण्यासाठी खालील बटण दाबा",
    record_supported: "हिंदी, मराठी, बंगाली आणि इंग्रजी बोलू शकता",
    stt_live: "● आवाज ओळख सुरू आहे",
    lbl_transcript_input: "नागरिकाचे म्हणणे / मजकूर नोंदवा:",
    btn_search_sources: "🔎 शासकीय माहिती शोधा (SerpApi) →",
    btn_create_app: "📄 अर्ज तयार करा →",
    btn_download_pdf: "📥 PDF डाउनलोड करा (.pdf)"
  },
  bn: {
    brand_sub: "এআই-চালিত নাগরিক অভিযোগ নথিভুক্তকরণ ও যাচাইকরণ ব্যবস্থা",
    landing_tagline: "জনসেবা নাগরিক অভিযোগ সহায়তা কেন্দ্র",
    landing_hero_msg: "আপনার সমস্যা নিজের ভাষায় বলুন। আওয়াজ অধিকার আপনার কথা বুঝতে, প্রাসঙ্গিক সরকারি নির্দেশিকা খুঁজতে এবং আবেদনপত্র তৈরি করতে সহায়তা করে।",
    how_it_works_title: "আওয়াজ অধিকার কীভাবে কাজ করে",
    nav_dashboard: "অপারেটর ড্যাশবোর্ড",
    nav_workspace: "অভিযোগ ওয়ার্কস্পেস",
    dash_welcome: "গ্রামীণ নাগরিক অভিযোগ নথিভুক্তকরণ কেন্দ্র",
    step1_nav: "১. আপনার সমস্যা বলুন",
    step2_nav: "২. তথ্য পর্যালোচনা",
    step3_nav: "৩. সরকারি তথ্য যাচাই",
    step4_nav: "৪. আবেদন প্রস্তুত",
    guide_step1: "নমস্কার। আপনার সমস্যা বলুন।",
    guide_step2: "অনুগ্রহ করে সংগৃহীত তথ্যাবলী পর্যালোচনা করুন এবং নিশ্চিত করুন।",
    guide_step3: "আমরা সরকারি পোর্টাল এবং নিয়মাবলী অনুসন্ধান করছি।",
    guide_step4: "আপনার দ্বিভাষিক আবেদনপত্র প্রস্তুত। আপনি এটি দেখতে ও ডাউনলোড করতে পারেন।",
    btn_listen: "শুনুন / Listen",
    ai_voice_guide: "কথা সহায়ক",
    ai_confirmation_label: "আপনার কথার নিশ্চয়তা",
    confirmation_yes: "✓ হ্যাঁ, এগিয়ে যান",
    confirmation_edit: "✏ সংশোধন করুন",
    record_status_idle: "অভিযোগ রেকর্ড করতে নিচে চাপ দিন",
    record_supported: "হিন্দি, মারাঠি, বাংলা ও ইংরেজিতে বলুন",
    stt_live: "● কথা শনাক্ত হচ্ছে",
    lbl_transcript_input: "নাগরিকের বক্তব্য / টেক্সট লিখুন:",
    btn_search_sources: "🔎 সরকারি তথ্য অনুসন্ধান (SerpApi) →",
    btn_create_app: "📄 আবেদনপত্র প্রস্তুত করুন →",
    btn_download_pdf: "📥 PDF ডাউনলোড করুন (.pdf)"
  },
  en: {
    brand_sub: "AI-Powered Citizen Grievance Documentation & Verification System",
    landing_tagline: "Public Service Citizen Grievance Assistance Platform",
    landing_hero_msg: "State your grievance in your own language. Awaaz Adhikar assists rural operators in structuring statements, finding official government rules, and preparing formal legal petitions.",
    how_it_works_title: "How Awaaz Adhikar Works",
    nav_dashboard: "Operator Dashboard",
    nav_workspace: "Grievance Workspace",
    dash_welcome: "Rural Grievance Documentation Station",
    step1_nav: "1. Tell Your Problem",
    step2_nav: "2. Review Details",
    step3_nav: "3. Find Gov Sources",
    step4_nav: "4. Create Application",
    guide_step1: "Hello. Please tell us your problem.",
    guide_step2: "Please review the extracted factual information and confirm.",
    guide_step3: "We are discovering official government portals and statutory rules.",
    guide_step4: "Your bilingual grievance application is ready for review and export.",
    btn_listen: "Listen",
    ai_voice_guide: "Voice Guide",
    ai_confirmation_label: "Confirm what you said",
    confirmation_yes: "✓ Yes, continue",
    confirmation_edit: "✏ Edit",
    record_status_idle: "Click below to start recording your grievance",
    record_supported: "Speak in English, Hindi, Marathi, or Bengali",
    stt_live: "● Speech recognition active",
    lbl_transcript_input: "Citizen Statement / Text Fallback Input:",
    btn_search_sources: "🔎 Search Official Gov Sources via SerpApi →",
    btn_create_app: "📄 Create Application →",
    btn_download_pdf: "📥 Download Official PDF (.pdf)"
  }
};

const VOICE_COPY = {
  hi: {
    confirmation: "मैंने आपकी बात सुनी। क्या यह सही है?",
    sttUnsupported: "इस डिवाइस पर हिंदी में आवाज़ से लिखना उपलब्ध नहीं है। कृपया अपना संदेश टाइप करें।",
    microphoneUnsupported: "इस ब्राउज़र में माइक्रोफ़ोन उपलब्ध नहीं है। कृपया अपना संदेश टाइप करें।",
    microphoneDenied: "माइक्रोफ़ोन की अनुमति नहीं मिली। कृपया अनुमति दें या अपना संदेश टाइप करें।",
    recording: "रिकॉर्डिंग चल रही है। साफ़ बोलें।",
    recordingFinished: "रिकॉर्डिंग पूरी हुई।",
    consentRequired: "आगे बढ़ने के लिए नागरिक की सहमति आवश्यक है।",
    transcriptRequired: "कृपया पहले अपनी शिकायत बोलें या नीचे लिखें।",
    extractionError: "आपकी बात समझने में समस्या हुई। कृपया फिर कोशिश करें या टाइप करें।",
    textFallbackHint: "कृपया नीचे दिए गए बॉक्स में अपना संदेश लिखें।",
  },
  mr: {
    confirmation: "मी तुमचे म्हणणे ऐकले. हे बरोबर आहे का?",
    sttUnsupported: "या डिव्हाइसवर मराठी आवाज-इनपुट उपलब्ध नाही. कृपया तुमचा संदेश टाइप करा.",
    microphoneUnsupported: "या ब्राउझरमध्ये मायक्रोफोन उपलब्ध नाही. कृपया तुमचा संदेश टाइप करा.",
    microphoneDenied: "मायक्रोफोनची परवानगी मिळाली नाही. कृपया परवानगी द्या किंवा संदेश टाइप करा.",
    recording: "रेकॉर्डिंग सुरू आहे. स्पष्ट बोला.",
    recordingFinished: "रेकॉर्डिंग पूर्ण झाले.",
    consentRequired: "पुढे जाण्यासाठी नागरिकाची संमती आवश्यक आहे.",
    transcriptRequired: "कृपया आधी तुमची तक्रार बोला किंवा टाइप करा.",
    extractionError: "तुमचे म्हणणे समजण्यात अडचण आली. पुन्हा प्रयत्न करा किंवा टाइप करा.",
    textFallbackHint: "कृपया खालील चौकटीत तुमचा संदेश टाइप करा.",
  },
  bn: {
    confirmation: "আমি আপনার কথা শুনেছি। এটি কি ঠিক?",
    sttUnsupported: "এই ডিভাইসে বাংলা কণ্ঠ-ইনপুট পাওয়া যাচ্ছে না। অনুগ্রহ করে বার্তাটি লিখুন।",
    microphoneUnsupported: "এই ব্রাউজারে মাইক্রোফোন সমর্থিত নয়। অনুগ্রহ করে বার্তাটি লিখুন।",
    microphoneDenied: "মাইক্রোফোনের অনুমতি পাওয়া যায়নি। অনুমতি দিন অথবা বার্তাটি লিখুন।",
    recording: "রেকর্ডিং চলছে। স্পষ্ট করে বলুন।",
    recordingFinished: "রেকর্ডিং শেষ হয়েছে।",
    consentRequired: "এগিয়ে যেতে নাগরিকের সম্মতি প্রয়োজন।",
    transcriptRequired: "অনুগ্রহ করে আগে আপনার অভিযোগ বলুন অথবা লিখুন।",
    extractionError: "আপনার কথা বুঝতে সমস্যা হয়েছে। আবার চেষ্টা করুন অথবা লিখুন।",
    textFallbackHint: "অনুগ্রহ করে নিচের ঘরে আপনার বার্তা লিখুন।",
  },
  en: {
    confirmation: "I heard you. Is that correct?",
    sttUnsupported: "English voice input is not supported on this device. Please type your message instead.",
    microphoneUnsupported: "Microphone access is not supported by this browser. Please type your message instead.",
    microphoneDenied: "Microphone permission was denied. Allow microphone access or type your message instead.",
    recording: "Recording in progress. Speak clearly.",
    recordingFinished: "Recording finished.",
    consentRequired: "Citizen consent is required to continue.",
    transcriptRequired: "Please speak or type your complaint first.",
    extractionError: "I could not understand that. Please try again or type your message.",
    textFallbackHint: "Please type your message in the box below.",
  },
};

// ========================================================
// 1. INITIALIZATION & LIFECYCLE
// ========================================================

document.addEventListener("DOMContentLoaded", async () => {
  // Load saved language
  const savedLang = localStorage.getItem("awaaz_lang") || "hi";
  currentCase.language = savedLang;
  const langSel = document.getElementById("lang-select");
  if (langSel) langSel.value = savedLang;

  // Load administrative locations
  await loadAdministrativeLocations();

  // Check auth session
  let hasAuth = checkAuthSession();
  try {
    const verified = await syncAuthSession();
    if (verified) hasAuth = true;
  } catch (e) {}

  // Load stats and demo samples
  loadStats();
  loadDemoSamples();
  setupSpeechRecognition();
  applyLanguage(savedLang);
  checkSerpApiStatus();

  // Initialize Step 1 form gating and step locks
  setupStep1FormListeners();
  updateStepTabLockState();

  // Sync initial view from hash or auth state
  const initialHash = window.location.hash.replace("#", "");
  if (["landing", "login", "dashboard", "workspace"].includes(initialHash)) {
    switchView(initialHash, false);
    if (initialHash === "workspace") {
      restoreStepGatingSession();
      goToStep(currentStep || 1);
    }
  } else {
    switchView(hasAuth ? "dashboard" : "landing", false);
  }
});

async function checkSerpApiStatus() {
  try {
    const res = await fetch("/api/health");
    if (res.ok) {
      const data = await res.json();
      const badge = document.getElementById("serp-badge-status");
      if (badge) {
        if (data.serpapi_configured) {
          badge.innerText = "LIVE";
          badge.className = "bg-emerald-600 text-white text-[10px] px-1.5 py-0.2 rounded font-mono";
        } else {
          badge.innerText = "DEMO MODE";
          badge.className = "bg-blue-600 text-white text-[10px] px-1.5 py-0.2 rounded font-mono";
        }
      }
    }
  } catch (e) {
    console.warn("Failed to check SerpApi status:", e);
  }
}

// Check if operator is already logged in
function checkAuthSession() {
  const sessionStr = localStorage.getItem("awaaz_operator_session");
  if (sessionStr) {
    try {
      const session = JSON.parse(sessionStr);
      if (session && session.token && session.operator) {
        currentUser = session;
        setAuthenticatedUI(session.operator);
        return true;
      }
    } catch (e) {
      console.warn("Session parse failed:", e);
    }
  }
  currentUser = null;
  setGuestUI();
  return false;
}

async function syncAuthSession() {
  const token = getCurrentOperatorToken();
  try {
    const headers = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch("/api/auth/me", {
      headers: headers,
      credentials: "include"
    });
    if (res.ok) {
      const data = await res.json();
      if (data.authenticated && data.operator) {
        if (!currentUser) currentUser = { token: token, operator: data.operator };
        currentUser.operator = data.operator;
        setAuthenticatedUI(data.operator);
        return true;
      }
    }
    // If backend returns not authenticated and we had a stale session in localStorage
    if (currentUser) {
      console.info("Operator session expired or invalid on backend. Clearing stale local state.");
      currentUser = null;
      localStorage.removeItem("awaaz_operator_session");
      setGuestUI();
    }
  } catch (e) {
    console.warn("Session sync check error:", e);
  }
  return false;
}

function setAuthenticatedUI(operator) {
  document.getElementById("header-guest-actions")?.classList.add("hidden");
  document.getElementById("header-auth-actions")?.classList.remove("hidden");
  document.getElementById("authenticated-subnav")?.classList.remove("hidden");
  document.getElementById("header-operator-badge-tag")?.classList.remove("hidden");

  const nameEl = document.getElementById("operator-display-name");
  const centerEl = document.getElementById("operator-display-center");
  if (nameEl) nameEl.innerText = operator.name || "Operator";
  if (centerEl) centerEl.innerText = `● ${operator.center_id || 'CSC Desk'}`;
}

function setGuestUI() {
  document.getElementById("header-guest-actions")?.classList.remove("hidden");
  document.getElementById("header-auth-actions")?.classList.add("hidden");
  document.getElementById("authenticated-subnav")?.classList.add("hidden");
  document.getElementById("header-operator-badge-tag")?.classList.add("hidden");
}

function getStoredOperatorSession() {
  try {
    const sessionStr = localStorage.getItem("awaaz_operator_session");
    if (!sessionStr) return null;
    const parsed = JSON.parse(sessionStr);
    return parsed && parsed.token ? parsed : null;
  } catch (e) {
    return null;
  }
}

function getCurrentOperatorToken() {
  const stored = getStoredOperatorSession();
  if (stored && stored.token) return stored.token;
  if (currentUser && currentUser.token) return currentUser.token;
  return "";
}

function redirectToOperatorLogin(message = "Session expired. Please log in again.") {
  currentUser = null;
  localStorage.removeItem("awaaz_operator_session");
  setGuestUI();
  const alertEl = document.getElementById("login-error-alert");
  if (alertEl) {
    alertEl.textContent = message;
    alertEl.classList.remove("hidden");
  }
  switchView("login", false);
  history.replaceState({}, "", "#login");
}

// ========================================================
// 2. VIEW & AUTH MANAGEMENT
// ========================================================

function switchView(viewName, updateHistory = true) {
  // Route Guard: Protected operator views require active authentication
  if ((viewName === "dashboard" || viewName === "workspace") && !currentUser) {
    console.info("Protected view access requires login. Redirecting to login view.");
    viewName = "login";
  }

  currentView = viewName;
  const views = ["landing", "login", "dashboard", "workspace"];
  
  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (el) {
      if (v === viewName) {
        el.classList.remove("hidden");
      } else {
        el.classList.add("hidden");
      }
    }
  });

  // Navigation tab styling
  const navDash = document.getElementById("nav-dashboard");
  const navWork = document.getElementById("nav-workspace");
  if (navDash && navWork) {
    if (viewName === "dashboard") {
      navDash.className = "py-2.5 px-1 border-b-2 border-gov-700 text-gov-800 text-xs sm:text-sm font-semibold transition flex items-center space-x-1.5";
      navWork.className = "py-2.5 px-1 border-b-2 border-transparent text-slate-600 hover:text-slate-900 text-xs sm:text-sm font-semibold transition flex items-center space-x-1.5";
      loadStats();
      loadRecentCases();
    } else if (viewName === "workspace") {
      navWork.className = "py-2.5 px-1 border-b-2 border-gov-700 text-gov-800 text-xs sm:text-sm font-semibold transition flex items-center space-x-1.5";
      navDash.className = "py-2.5 px-1 border-b-2 border-transparent text-slate-600 hover:text-slate-900 text-xs sm:text-sm font-semibold transition flex items-center space-x-1.5";
    }
  }

  if (viewName === "workspace") {
    updateStepTabLockState();
    goToStep(currentStep || 1);
  }

  if (updateHistory) {
    try {
      history.pushState({ view: viewName, step: currentStep || 1 }, "", `#${viewName}`);
    } catch (e) {}
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

window.addEventListener("popstate", () => {
  const hash = window.location.hash.replace("#", "");
  const targetView = ["landing", "login", "dashboard", "workspace"].includes(hash)
    ? hash
    : (currentUser ? "dashboard" : "landing");
  switchView(targetView, false);
  if (targetView === "workspace") {
    const requestedStep = (history.state && history.state.step) || currentStep || 1;
    goToStep(Math.min(requestedStep, getMaxAllowedStep()));
  }
});

function handleBrandClick() {
  if (currentUser) {
    switchView("dashboard");
  } else {
    switchView("landing");
  }
}

// Handle Operator Login via Email/Password
async function handleOperatorLogin(e) {
  e.preventDefault();
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value.trim();
  const alertEl = document.getElementById("login-error-alert");
  const submitBtn = document.getElementById("btn-submit-login");

  alertEl.classList.add("hidden");
  submitBtn.disabled = true;
  submitBtn.innerText = "Authenticating...";

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.detail || "Invalid login credentials. Please use demo login or check credentials.");
    }

    currentUser = data;
    localStorage.setItem("awaaz_operator_session", JSON.stringify(data));
    setAuthenticatedUI(data.operator);
    switchView("dashboard");
  } catch (err) {
    alertEl.innerText = err.message;
    alertEl.classList.remove("hidden");
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerText = "🔐 Login to Workspace";
    }
  }
}

// Handle Instant Demo Login for Hackathon Judges
async function handleDemoLogin() {
  const btn = document.getElementById("btn-demo-login");
  if (btn) {
    btn.disabled = true;
    btn.innerText = "Logging in as Demo Operator...";
  }

  try {
    const res = await fetch("/api/auth/demo-login", {
      method: "POST",
      credentials: "include"
    });
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error("Demo login failed");

    currentUser = data;
    localStorage.setItem("awaaz_operator_session", JSON.stringify(data));
    setAuthenticatedUI(data.operator);
    switchView("dashboard");
  } catch (err) {
    alert("Demo login error: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerText = "⚡ One-Click Demo Login (CSC Operator #4102)";
    }
  }
}

// Handle Logout
async function handleLogout() {
  try {
    if (currentUser && currentUser.token) {
      await fetch("/api/auth/logout", {
        method: "POST",
        headers: { "Authorization": `Bearer ${currentUser.token}` }
      });
    }
  } catch (e) {
    console.warn("Logout error:", e);
  }
  currentUser = null;
  localStorage.removeItem("awaaz_operator_session");
  setGuestUI();
  startNewCase(false);
  switchView("landing");
}

// Public visitor instant trial
async function launchInteractiveDemo() {
  await handleDemoLogin();
  startNewCase();
}

// ========================================================
// 3. ADMINISTRATIVE LOCATIONS (CASCADING STATE -> DISTRICT)
// ========================================================

async function loadAdministrativeLocations() {
  try {
    const res = await fetch("/api/locations");
    if (!res.ok) return;
    ADMIN_DIVISIONS = await res.json();
    populateStateDropdown();
  } catch (e) {
    console.error("Error loading administrative divisions:", e);
  }
}

function populateStateDropdown() {
  const stateSelect = document.getElementById("field-state-select");
  if (!stateSelect) return;
  stateSelect.innerHTML = '<option value="">Select State / Union Territory</option>';

  const states = [];
  const uts = [];

  Object.keys(ADMIN_DIVISIONS).forEach(name => {
    const item = ADMIN_DIVISIONS[name];
    if (item.type === "UT") {
      uts.push(name);
    } else {
      states.push(name);
    }
  });

  states.sort();
  uts.sort();

  const stateGroup = document.createElement("optgroup");
  stateGroup.label = "States (28)";
  states.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = s;
    stateGroup.appendChild(opt);
  });
  stateSelect.appendChild(stateGroup);

  const utGroup = document.createElement("optgroup");
  utGroup.label = "Union Territories (8)";
  uts.forEach(u => {
    const opt = document.createElement("option");
    opt.value = u;
    opt.textContent = u;
    utGroup.appendChild(opt);
  });
  stateSelect.appendChild(utGroup);
}

function handleStateSelectionChange(selectedState, preserveSearchResults = false) {
  const stateInput = document.getElementById("field-state");
  const distSelect = document.getElementById("field-district-select");
  const distInput = document.getElementById("field-district");
  const mismatchBox = document.getElementById("location-mismatch-box");

  if (mismatchBox) mismatchBox.classList.add("hidden");
  if (!preserveSearchResults && currentCase.extracted_fields.state !== selectedState) {
    clearCurrentSearchResults();
  }

  if (stateInput) stateInput.value = selectedState;
  currentCase.extracted_fields.state = selectedState;

  // Clear previous district on state change
  if (distInput) distInput.value = "";
  currentCase.extracted_fields.district = "";

  if (!selectedState || !ADMIN_DIVISIONS[selectedState]) {
    distSelect.innerHTML = '<option value="">Select District</option>';
    distSelect.disabled = true;
    return;
  }

  // Populate districts for the selected state
  const districts = ADMIN_DIVISIONS[selectedState].districts || [];
  distSelect.innerHTML = '<option value="">Select District</option>';
  districts.forEach(d => {
    const opt = document.createElement("option");
    opt.value = d;
    opt.textContent = d;
    distSelect.appendChild(opt);
  });
  distSelect.disabled = false;

  updateSummaryCard();
}

function handleDistrictSelectionChange(selectedDistrict, preserveSearchResults = false) {
  const distInput = document.getElementById("field-district");
  const stateInput = document.getElementById("field-state");
  const mismatchBox = document.getElementById("location-mismatch-box");

  if (!preserveSearchResults && currentCase.extracted_fields.district !== selectedDistrict) {
    clearCurrentSearchResults();
  }
  if (distInput) distInput.value = selectedDistrict;
  currentCase.extracted_fields.district = selectedDistrict;

  // Consistency validation
  const currentState = stateInput ? stateInput.value : "";
  if (currentState && selectedDistrict && ADMIN_DIVISIONS[currentState]) {
    const validDists = ADMIN_DIVISIONS[currentState].districts || [];
    if (!validDists.includes(selectedDistrict)) {
      if (mismatchBox) {
        document.getElementById("location-mismatch-text").innerText = `District '${selectedDistrict}' does not belong to the selected State '${currentState}'. Please review.`;
        mismatchBox.classList.remove("hidden");
      }
    } else {
      if (mismatchBox) mismatchBox.classList.add("hidden");
    }
  }

  updateSummaryCard();
}

// ========================================================
// 4. 4-STEP STEPPER NAVIGATION
// ========================================================

// Step gate messages for each language
const STEP_GATE_MESSAGES = {
  hi: "कृपया पहले इस चरण को पूरा करें और आगे बढ़ें।",
  mr: "कृपया आधी हा टप्पा पूर्ण करा.",
  bn: "অনুগ্রহ করে আগে এই ধাপটি সম্পন্ন করুন।",
  en: "Please complete the current step before proceeding."
};

function _getStepGateMsg() {
  const lang = document.getElementById("lang-select")?.value || currentCase.language || "hi";
  return STEP_GATE_MESSAGES[lang] || STEP_GATE_MESSAGES.hi;
}

function showStepGateBanner(msg) {
  let banner = document.getElementById("step-gate-banner");
  if (!banner) {
    banner = document.createElement("div");
    banner.id = "step-gate-banner";
    banner.style.cssText = "position:fixed;top:70px;left:50%;transform:translateX(-50%);z-index:9999;background:#dc2626;color:#fff;padding:10px 22px;border-radius:8px;font-size:13px;font-weight:600;box-shadow:0 4px 16px rgba(0,0,0,0.18);pointer-events:none;";
    document.body.appendChild(banner);
  }
  banner.textContent = msg;
  banner.style.display = "block";
  setTimeout(() => { if (banner) banner.style.display = "none"; }, 3000);
}

function isStepCompleted(stepNum) {
  const fields = currentCase.extracted_fields || {};
  if (stepNum === 1) {
    const hasTranscript = Boolean((currentCase.original_transcript || currentCase.edited_transcript || "").trim().length > 0);
    const hasFacts = Boolean(fields.citizen_name || fields.issue_type || fields.state);
    return completedSteps.has(1) && hasTranscript && hasFacts;
  }
  if (stepNum === 2) {
    const hasLocation = Boolean(fields.state && fields.district);
    const hasIdentity = Boolean(fields.citizen_name && (fields.issue_type || fields.scheme));
    return completedSteps.has(2) && isStepCompleted(1) && hasLocation && hasIdentity;
  }
  if (stepNum === 3) {
    const docs = currentCase.generated_documents || {};
    const hasGeneratedDoc = Boolean(docs.english_application || docs.regional_language || docs.hindi_application);
    return completedSteps.has(3) && isStepCompleted(2) && hasGeneratedDoc;
  }
  return false;
}

function getMaxAllowedStep() {
  if (isStepCompleted(3)) return 4;
  if (isStepCompleted(2)) return 3;
  if (isStepCompleted(1)) return 2;
  return 1;
}

function pruneInvalidCompletedSteps() {
  const kept = new Set();
  if (completedSteps.has(1) && isStepCompleted(1)) kept.add(1);
  if (completedSteps.has(2) && isStepCompleted(2)) kept.add(2);
  if (completedSteps.has(3) && isStepCompleted(3)) kept.add(3);
  completedSteps = kept;
}

function applyRestoredCaseToForm() {
  const rawInput = document.getElementById("raw-input-text");
  if (rawInput) rawInput.value = currentCase.original_transcript || currentCase.edited_transcript || "";
  const originalDisplay = document.getElementById("original-transcript-display");
  if (originalDisplay) originalDisplay.innerText = currentCase.original_transcript || "(Waiting for input...)";
  const editedInput = document.getElementById("edited-transcript-input");
  if (editedInput) editedInput.value = currentCase.edited_transcript || currentCase.original_transcript || "";
  populateFormFields(currentCase.extracted_fields || {});
  if (currentCase.sources && currentCase.sources.length) {
    renderSourceReviewCards(currentCase.sources);
  }
  if (currentCase.generated_documents && Object.keys(currentCase.generated_documents).length) {
    renderBilingualPreview(currentCase.generated_documents);
  }
  syncTemplateSelectionUI();
  validateStep1Form();
  updateCaseHeader();
}

function updateStepTabLockState() {
  for (let i = 2; i <= 4; i++) {
    const tab = document.getElementById(`step-tab-${i}`);
    if (!tab) continue;
    const unlocked = isStepCompleted(i - 1);
    if (unlocked) {
      tab.disabled = false;
      tab.style.opacity = "";
      tab.style.pointerEvents = "";
      tab.title = "";
      tab.setAttribute("aria-disabled", "false");
      tab.classList.remove("cursor-not-allowed");
    } else {
      tab.disabled = true;
      tab.style.opacity = "0.45";
      tab.style.pointerEvents = "none";
      tab.title = _getStepGateMsg();
      tab.setAttribute("aria-disabled", "true");
      tab.classList.add("cursor-not-allowed");
    }
  }
}

function validateStep1Form() {
  const consent = document.getElementById("consent-check")?.checked;
  const rawText = (document.getElementById("raw-input-text")?.value || "").trim();
  const isValid = Boolean(consent && rawText.length > 0);

  const nextBtn = document.getElementById("btn-step1-next");
  if (nextBtn) {
    nextBtn.disabled = !isValid;
  }
  const confirmBtn = document.getElementById("btn-confirm-proceed");
  if (confirmBtn) {
    confirmBtn.disabled = !isValid;
  }
  return isValid;
}

function setupStep1FormListeners() {
  const rawInput = document.getElementById("raw-input-text");
  const consentCheck = document.getElementById("consent-check");

  if (rawInput) {
    rawInput.addEventListener("input", validateStep1Form);
    rawInput.addEventListener("change", validateStep1Form);
  }
  if (consentCheck) {
    consentCheck.addEventListener("change", validateStep1Form);
  }
  validateStep1Form();
}

function saveStepGatingSession() {
  try {
    sessionStorage.setItem("awaaz_case_id", currentCase.id || "");
    sessionStorage.setItem("awaaz_completed_steps", JSON.stringify(Array.from(completedSteps)));
    sessionStorage.setItem("awaaz_current_step", String(currentStep));
    sessionStorage.setItem("awaaz_case_data", JSON.stringify(currentCase));
  } catch (e) {}
}

function restoreStepGatingSession() {
  try {
    const savedCaseRaw = sessionStorage.getItem("awaaz_case_data");
    const savedCaseId = sessionStorage.getItem("awaaz_case_id");
    if (savedCaseRaw) {
      const savedCase = JSON.parse(savedCaseRaw);
      if (!savedCase || !savedCase.id) return false;
      if (savedCaseId && savedCaseId !== savedCase.id) return false;
      currentCase = savedCase;
      applyRestoredCaseToForm();
    } else if (!savedCaseId || savedCaseId !== currentCase.id) {
      return false;
    }
    const stepsStr = sessionStorage.getItem("awaaz_completed_steps");
    if (stepsStr) {
      const arr = JSON.parse(stepsStr);
      if (Array.isArray(arr)) {
        completedSteps = new Set(arr.map(n => parseInt(n, 10)).filter(n => n >= 1 && n <= 3));
      }
    }
    pruneInvalidCompletedSteps();
    const allowed = getMaxAllowedStep();
    const stepStr = sessionStorage.getItem("awaaz_current_step");
    let targetStep = parseInt(stepStr, 10);
    if (!(targetStep >= 1 && targetStep <= 4)) targetStep = allowed;
    goToStep(Math.min(targetStep, allowed));
    return true;
  } catch (e) {}
  return false;
}

function clearStepGatingSession() {
  try {
    sessionStorage.removeItem("awaaz_case_id");
    sessionStorage.removeItem("awaaz_completed_steps");
    sessionStorage.removeItem("awaaz_current_step");
    sessionStorage.removeItem("awaaz_case_data");
  } catch (e) {}
}

function goToStep(stepNum) {
  const requestedStep = parseInt(stepNum, 10);
  stepNum = Number.isInteger(requestedStep) ? requestedStep : 1;
  if (stepNum < 1) stepNum = 1;
  if (stepNum > 4) stepNum = 4;

  const allowed = getMaxAllowedStep();
  if (stepNum > allowed) {
    showStepGateBanner(_getStepGateMsg());
    stepNum = allowed;
  }

  currentStep = stepNum;

  // Toggle 4 panels
  for (let i = 1; i <= 4; i++) {
    const panel = document.getElementById(`step-panel-${i}`);
    const tab = document.getElementById(`step-tab-${i}`);
    const line = document.getElementById(`line-${i - 1}`);

    if (panel) {
      if (i === stepNum) {
        panel.classList.remove("hidden");
      } else {
        panel.classList.add("hidden");
      }
    }

    if (tab) {
      const circle = tab.querySelector("span:first-child");
      if (i === stepNum) {
        tab.className = "step-btn flex items-center space-x-1.5 text-gov-700 font-bold whitespace-nowrap";
        if (circle) circle.className = "w-6 h-6 rounded-full bg-gov-700 text-white flex items-center justify-center text-xs";
      } else if (i < stepNum || isStepCompleted(i)) {
        tab.className = "step-btn flex items-center space-x-1.5 text-emerald-700 font-semibold whitespace-nowrap";
        if (circle) circle.className = "w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs";
      } else {
        tab.className = "step-btn flex items-center space-x-1.5 text-slate-400 whitespace-nowrap";
        if (circle) circle.className = "w-6 h-6 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center text-xs";
      }
    }

    if (line) {
      if (i - 1 < stepNum) {
        line.classList.add("active");
      } else {
        line.classList.remove("active");
      }
    }
  }

  updateStepTabLockState();
  saveStepGatingSession();
  try {
    history.replaceState({ view: currentView || "workspace", step: currentStep }, "", `#${currentView || "workspace"}`);
  } catch (e) {}
  window.scrollTo({ top: 0, behavior: "smooth" });
}


// ========================================================
// 5. LANGUAGE SYSTEM & REAL I18N
// ========================================================

function changeLanguage(langCode) {
  currentCase.language = langCode;
  localStorage.setItem("awaaz_lang", langCode);

  const langSelect = document.getElementById("lang-select");
  if (langSelect) langSelect.value = langCode;

  applyLanguage(langCode);
  updateSpeechRecognitionLanguage();
  if (!document.getElementById("understood-confirm-box")?.classList.contains("hidden")) {
    showUnderstoodConfirm();
  }
}

function getVoiceCopy(key) {
  return (VOICE_COPY[currentCase.language] || VOICE_COPY.en)[key] || VOICE_COPY.en[key];
}

function updateVoiceGuideResponse() {
  const guide = document.getElementById("guide-step2-text");
  if (!guide) return;
  const selectedLanguage = document.getElementById("lang-select")?.value;
  const language = VOICE_COPY[selectedLanguage]
    ? selectedLanguage
    : (VOICE_COPY[currentCase.language] ? currentCase.language : "en");
  const fields = currentCase.extracted_fields || {};
  const schemeCode = (fields.scheme_code || "").toLowerCase();
  const hasFacts = Boolean(fields.citizen_name || fields.issue_type || fields.state || fields.district);
  if (!hasFacts) {
    guide.innerText = (TRANSLATIONS[language] || TRANSLATIONS.en).guide_step2;
    return;
  }

  const issueLabels = {
    hi: { electricity: "बिजली आपूर्ति की", water: "पानी की आपूर्ति की", pension: "पेंशन की", ration: "राशन वितरण की", other: "नागरिक शिकायत की" },
    mr: { electricity: "वीजपुरवठ्याबाबतची", water: "पाणीपुरवठ्याबाबतची", pension: "पेन्शनबाबतची", ration: "रेशन वितरणाबाबतची", other: "नागरिक तक्रारीची" },
    bn: { electricity: "বিদ্যুৎ সরবরাহের", water: "জল সরবরাহের", pension: "পেনশনের", ration: "রেশন বিতরণের", other: "নাগরিক অভিযোগের" },
    en: { electricity: "electricity supply", water: "water supply", pension: "pension", ration: "ration distribution", other: "public grievance" },
  };
  const category = ["electricity", "water", "pension", "ration"].includes(schemeCode) ? schemeCode : "other";
  const issue = issueLabels[language][category];
  const name = (fields.citizen_name || "").trim().replace(/[.!?।]+$/u, "");
  const responses = {
    hi: "मैंने " + (name ? name + " की" : "आपकी") + " " + issue + " शिकायत दर्ज की है। कृपया जानकारी जाँचें। सही होने पर आगे बढ़ें।",
    mr: "मी " + (name ? name + " यांची" : "आपली") + " " + issue + " तक्रार नोंदवली आहे. कृपया माहिती तपासा. योग्य असल्यास पुढे जा.",
    bn: "আমি " + (name ? name + "-এর" : "আপনার") + " " + issue + " অভিযোগ নথিভুক্ত করেছি। অনুগ্রহ করে তথ্য দেখুন। ঠিক থাকলে এগিয়ে যান।",
    en: "I recorded " + (name ? name + "'s" : "your") + " " + issue + " complaint. Please review the details and continue if they are correct.",
  };
  guide.innerText = responses[language];
}

function applyLanguage(langCode) {
  const dict = TRANSLATIONS[langCode] || TRANSLATIONS.hi;

  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) {
      el.innerText = dict[key];
    }
  });

  // Update voice guide texts
  const g1 = document.getElementById("guide-step1-text");
  const g2 = document.getElementById("guide-step2-text");
  const g3 = document.getElementById("guide-step3-text");
  const g4 = document.getElementById("guide-step4-text");

  if (g1) g1.innerText = dict.guide_step1;
  if (g2) g2.innerText = dict.guide_step2;
  if (g3) g3.innerText = dict.guide_step3;
  if (g4) g4.innerText = dict.guide_step4;

  // Update localized placeholder
  const rawInput = document.getElementById("raw-input-text");
  if (rawInput) {
    const placeholders = {
      hi: "उदाहरण: मेरा नाम रमेश कुमार है। मुझे 3 महीने से वृद्धावस्था पेंशन नहीं मिली है। मैं रामपुर गाँव, जिला सीतापुर, उत्तर प्रदेश से हूँ।",
      mr: "उदाहरण: माझे नाव तुकाराम पाटील आहे. मला ३ महिन्यांपासून पेन्शन मिळाली नाही. मी सोलापूर जिल्ह्यातील आहे.",
      bn: "উদাহরণ: আমার নাম পরিমল বিশ্বাস। ৩ মাস ধরে রেশন পাচ্ছি না। আমি নদীয়া জেলার বাসিন্দা।",
      en: "Example: My name is Ramesh Kumar. I have not received my old age pension for 3 months. I am from Rampur village, Sitapur district, Uttar Pradesh."
    };
    rawInput.placeholder = placeholders[langCode] || placeholders.hi;
  }

  // Update button texts
  const serpBtnText = document.getElementById("serpapi-btn-text");
  if (serpBtnText && dict.btn_search_sources) {
    serpBtnText.innerText = dict.btn_search_sources;
  }
  updateVoiceGuideResponse();
}

function speakVoiceGuide(textElementId) {
  const el = document.getElementById(textElementId);
  if (!el) return;
  const text = el.innerText.trim();
  if (!text) return;

  const synthesis = window.speechSynthesis;
  if (!synthesis || typeof SpeechSynthesisUtterance === "undefined") {
    console.warn("SpeechSynthesis not supported by this browser.");
    const note = document.querySelector(`[data-tts-note-for="${textElementId}"]`);
    if (note) note.innerText = "Voice not available for this language on this device.";
    return;
  }

  // Cancel any ongoing utterance immediately
  try { synthesis.cancel(); } catch (e) {}

  // 1. Read CURRENT visible text and CURRENT selected language dynamically
  const selectedLang = document.getElementById("lang-select")?.value || currentCase.language || "hi";
  const locale = getSpeechLocale(selectedLang) || (selectedLang === "en" ? "en-IN" : `${selectedLang}-IN`);
  const note = document.querySelector(`[data-tts-note-for="${textElementId}"]`);

  const setFallback = (message) => {
    if (note) note.innerText = message;
    el.style.fontSize = "1.125rem";
    el.style.lineHeight = "1.6";
  };

  const clearFallback = () => {
    if (note) note.innerText = "";
    el.style.fontSize = "";
    el.style.lineHeight = "";
  };

  // Helper to pick matching voice from voice list
  const pickVoice = (voices) => {
    if (!voices || voices.length === 0) return { voice: null, isMarathiHindiFallback: false };

    const normalize = (s) => (s || "").toLowerCase().replace(/_/g, "-");
    const targetLocale = locale.toLowerCase();

    // 1. Exact locale match (e.g. en-in, hi-in, mr-in, bn-in)
    let matched = voices.find(v => normalize(v.lang) === targetLocale);

    // 2. Same language prefix match (e.g. hi-, mr-, bn-, en-)
    if (!matched) {
      matched = voices.find(v => {
        const l = normalize(v.lang);
        return l === selectedLang || l.startsWith(`${selectedLang}-`);
      });
    }

    // 3. Name contains language name (Hindi, Marathi, Bengali, English)
    const langNames = {
      hi: ["hindi", "devanagari"],
      mr: ["marathi"],
      bn: ["bengali", "bangla"],
      en: ["english", "indian english"]
    };
    if (!matched && langNames[selectedLang]) {
      const names = langNames[selectedLang];
      matched = voices.find(v => {
        const name = (v.name || "").toLowerCase();
        return names.some(n => name.includes(n));
      });
    }

    // English regional fallback order: en-IN -> en-US -> en-GB -> any en
    if (!matched && selectedLang === "en") {
      matched = voices.find(v => normalize(v.lang) === "en-us") ||
                voices.find(v => normalize(v.lang) === "en-gb") ||
                voices.find(v => normalize(v.lang).startsWith("en"));
    }

    // Marathi fallback: prefer mr-IN. If missing and a Hindi voice exists, use Hindi voice with note
    let isMarathiHindiFallback = false;
    if (!matched && selectedLang === "mr") {
      matched = voices.find(v => normalize(v.lang) === "hi-in" || normalize(v.lang).startsWith("hi")) ||
                voices.find(v => (v.name || "").toLowerCase().includes("hindi"));
      if (matched) {
        isMarathiHindiFallback = true;
      }
    }

    // CRITICAL: NEVER speak English for hi/mr/bn
    if (matched && selectedLang !== "en") {
      const matchedLang = normalize(matched.lang);
      if (matchedLang.startsWith("en")) {
        matched = null;
        isMarathiHindiFallback = false;
      }
    }

    return { voice: matched, isMarathiHindiFallback };
  };

  const executeSpeak = (voices) => {
    const { voice, isMarathiHindiFallback } = pickVoice(voices);

    const utterance = new SpeechSynthesisUtterance(text);
    // Utterance lang is ALWAYS set to locale (or Hindi voice lang if Marathi-Hindi fallback)
    if (isMarathiHindiFallback && voice) {
      utterance.lang = voice.lang || "hi-IN";
      if (note) note.innerText = "Marathi voice not available on this device. Hindi voice is being used.";
    } else {
      utterance.lang = locale;
      if (note && note.innerText.includes("Marathi")) {
        note.innerText = "";
      }
    }

    if (voice) {
      utterance.voice = voice;
    }
    utterance.rate = 0.95;

    let hasStarted = false;
    let hasEnded = false;

    // Timeout: if onstart has not fired within ~2 seconds after speak(), show fallback warning
    const startTimeout = setTimeout(() => {
      if (!hasStarted && !hasEnded) {
        console.warn(`SpeechSynthesis onstart did not fire within 2s for ${locale}. Showing fallback note.`);
        setFallback("Voice not available for this language on this device.");
      }
    }, 2000);

    utterance.onstart = () => {
      hasStarted = true;
      clearTimeout(startTimeout);
      if (!isMarathiHindiFallback) {
        clearFallback();
      }
      console.log(`SpeechSynthesis started for lang: ${utterance.lang}, voice: ${voice ? voice.name : "default/system"}`);
    };

    utterance.onend = () => {
      hasEnded = true;
      clearTimeout(startTimeout);
      console.log("SpeechSynthesis completed.");
    };

    utterance.onerror = (e) => {
      hasEnded = true;
      clearTimeout(startTimeout);
      console.error("SpeechSynthesis onerror fired:", e);
      if (e.error !== "canceled" && e.error !== "interrupted") {
        setFallback("Voice not available for this language on this device.");
      }
    };

    // Chrome cancel/speak timing fix: cancel first, wait ~100ms, resume(), then speak()
    setTimeout(() => {
      try {
        synthesis.resume();
        synthesis.speak(utterance);
        console.log(`Called synthesis.speak() for locale: ${utterance.lang}`);
      } catch (err) {
        console.error("SpeechSynthesis speak exception:", err);
        clearTimeout(startTimeout);
        setFallback("Voice not available for this language on this device.");
      }
    }, 100);
  };

  // 3. VOICE LOADING + MATCHING: Wait for voices or speak via system engine
  let initialVoices = synthesis.getVoices() || [];
  if (initialVoices.length > 0) {
    executeSpeak(initialVoices);
  } else {
    let handled = false;
    let retryInterval = null;
    let maxWaitTimeout = null;

    const cleanup = () => {
      if (retryInterval) clearInterval(retryInterval);
      if (maxWaitTimeout) clearTimeout(maxWaitTimeout);
      synthesis.removeEventListener("voiceschanged", onVoicesChanged);
    };

    const triggerOnce = () => {
      if (handled) return;
      handled = true;
      cleanup();
      const loadedVoices = synthesis.getVoices() || [];
      // Even if loadedVoices is empty, STILL call executeSpeak so system engine handles it!
      executeSpeak(loadedVoices);
    };

    const onVoicesChanged = () => {
      triggerOnce();
    };

    synthesis.addEventListener("voiceschanged", onVoicesChanged);

    retryInterval = setInterval(() => {
      const v = synthesis.getVoices() || [];
      if (v.length > 0) {
        triggerOnce();
      }
    }, 100);

    // After 600ms max wait, execute speak anyway with system engine
    maxWaitTimeout = setTimeout(() => {
      triggerOnce();
    }, 600);
  }
}


// ========================================================
// 6. VOICE RECORDING (MEDIARECORDER + STT)
// ========================================================

// Accumulated speech transcript state (preserved across onresult events, silence pauses, and onend)
let _sttPrefixTranscript = "";
window._resetSttTranscript = function() {
  _sttPrefixTranscript = "";
  const r = document.getElementById("raw-input-text");
  if (r) r.value = "";
};

function setupSpeechRecognition() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    recognition = null;
    return;
  }

  try {
    if (recognition) {
      try { recognition.abort(); } catch (e) {}
      recognition.onresult = null;
      recognition.onerror = null;
      recognition.onend = null;
    }
  } catch (e) {}

  recognition = new SpeechRec();
  recognition.continuous = true;
  recognition.interimResults = true;
  const activeLang = document.getElementById("lang-select")?.value || currentCase.language || "hi";
  recognition.lang = getSpeechLocale(activeLang) || "hi-IN";

  recognition.onresult = (event) => {
    let sessionFinal = "";
    let interim = "";
    for (let i = 0; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        const trans = (event.results[i][0].transcript || "").trim();
        if (trans) sessionFinal += trans + " ";
      } else {
        interim += event.results[i][0].transcript;
      }
    }
    const rawInput = document.getElementById("raw-input-text");
    if (rawInput) {
      const fullText = (_sttPrefixTranscript + sessionFinal + interim).trim();
      if (fullText) {
        rawInput.value = fullText;
        currentCase.original_transcript = fullText;
        currentCase.edited_transcript = fullText;
        validateStep1Form();
      }
    }
  };

  recognition.onend = () => {
    // If still actively recording, preserve current transcript and restart recognition immediately
    if (isRecording) {
      const rawInput = document.getElementById("raw-input-text");
      if (rawInput && rawInput.value.trim()) {
        _sttPrefixTranscript = rawInput.value.trim() + " ";
      }
      try {
        recognition.start();
        return;
      } catch (err) {
        console.warn("Speech recognition restart notice:", err);
      }
    }

    // Normal end of recording: preserve final transcript
    const rawInput = document.getElementById("raw-input-text");
    if (rawInput && rawInput.value.trim()) {
      currentCase.original_transcript = rawInput.value.trim();
      currentCase.edited_transcript = rawInput.value.trim();
      validateStep1Form();
    }
    document.getElementById("stt-live-indicator")?.classList.add("hidden");
  };

  recognition.onerror = (e) => {
    console.warn("Speech recognition warning:", e.error);
    if (e.error === "no-speech") {
      // Normal pause during speech — onend handles restart if still recording
      return;
    }
    if (e.error === "language-not-supported") {
      showRecordError(getVoiceCopy("sttUnsupported"));
      document.getElementById("raw-input-text")?.focus();
    } else if (e.error === "not-allowed" || e.error === "service-not-allowed") {
      showRecordError(getVoiceCopy("microphoneDenied"));
    }
  };
}


function getSpeechLocale(language) {
  return { en: "en-IN", hi: "hi-IN", mr: "mr-IN", bn: "bn-IN" }[language] || null;
}

function updateSpeechRecognitionLanguage() {
  if (!recognition) return;
  const activeLang = document.getElementById("lang-select")?.value || currentCase.language || "hi";
  currentCase.language = activeLang;
  const locale = getSpeechLocale(activeLang);
  if (!locale) {
    showRecordError(getVoiceCopy("sttUnsupported"));
    return;
  }
  const restart = isRecording;
  if (restart) {
    try { recognition.stop(); } catch (err) {}
  }
  recognition.lang = locale;
  if (restart) {
    setTimeout(() => {
      try { recognition.start(); } catch (err) { showRecordError(getVoiceCopy("sttUnsupported")); }
    }, 100);
  }
}

async function startVoiceRecording() {
  dismissRecordError();
  recordedAudioChunks = [];
  recordSeconds = 0;
  _sttPrefixTranscript = ""; // Reset accumulated transcript for new recording

  setupSpeechRecognition();
  // If browser Web Speech is unavailable, proceed anyway: MediaRecorder captures audio for backend STT!

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showRecordError(getVoiceCopy("microphoneUnsupported"));
    document.getElementById("raw-input-text")?.focus();
    return;
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // Choose supported mimeType
    let mimeType = "audio/webm";
    if (!MediaRecorder.isTypeSupported("audio/webm")) {
      if (MediaRecorder.isTypeSupported("audio/mp4")) mimeType = "audio/mp4";
      else if (MediaRecorder.isTypeSupported("audio/ogg")) mimeType = "audio/ogg";
      else mimeType = "";
    }

    mediaRecorder = mimeType ? new MediaRecorder(mediaStream, { mimeType }) : new MediaRecorder(mediaStream);

    mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        recordedAudioChunks.push(e.data);
      }
    };

    mediaRecorder.onstop = async () => {
      recordedAudioBlob = new Blob(recordedAudioChunks, { type: mediaRecorder.mimeType || "audio/webm" });
      recordedAudioUrl = URL.createObjectURL(recordedAudioBlob);

      const player = document.getElementById("recorded-audio-player");
      const previewBox = document.getElementById("audio-preview-box");
      const downloadLink = document.getElementById("audio-download-link");
      const durationTag = document.getElementById("audio-duration-tag");

      if (player) player.src = recordedAudioUrl;
      if (previewBox) previewBox.classList.remove("hidden");
      if (downloadLink) downloadLink.href = recordedAudioUrl;
      if (durationTag) durationTag.innerText = `(${formatTimer(recordSeconds)})`;

      // Upload audio to backend & perform STT transcription
      await uploadAudioBlob(recordedAudioBlob);

      // Trigger AI confirmation prompt
      showUnderstoodConfirm();
    };

    mediaRecorder.start(250);
    isRecording = true;

    // Start STT if available
    if (recognition) {
      try {
        const activeLang = document.getElementById("lang-select")?.value || currentCase.language || "hi";
        currentCase.language = activeLang;
        const locale = getSpeechLocale(activeLang) || "hi-IN";
        recognition.lang = locale;
        recognition.start();
        document.getElementById("stt-live-indicator")?.classList.remove("hidden");
      } catch (err) {
        console.warn("Speech recognition start warning:", err);
      }
    }

    // UI Updates
    document.getElementById("btn-start-record")?.classList.add("hidden");
    document.getElementById("btn-stop-record")?.classList.remove("hidden");
    document.getElementById("btn-rerecord")?.classList.add("hidden");
    document.getElementById("waveform")?.classList.remove("hidden");
    document.getElementById("mic-icon-container").className = "w-20 h-20 mx-auto rounded-full bg-rose-50 flex items-center justify-center text-3xl shadow-sm text-rose-600 animate-pulse transition";
    document.getElementById("record-status-text").innerText = getVoiceCopy("recording");

    // Timer
    recordTimerInterval = setInterval(() => {
      recordSeconds++;
      document.getElementById("record-timer").innerText = formatTimer(recordSeconds);
    }, 1000);

  } catch (err) {
    console.error("Microphone error:", err);
    if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
      showRecordError(getVoiceCopy("microphoneDenied"));
    } else {
      showRecordError(`${getVoiceCopy("microphoneUnsupported")} ${err.message}`);
    }
  }
}

function stopVoiceRecording() {
  isRecording = false; // Disable recording flag first to prevent onend auto-restarts
  if (recognition) {
    try { recognition.stop(); } catch (err) {}
    document.getElementById("stt-live-indicator")?.classList.add("hidden");
  }
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    try { mediaRecorder.stop(); } catch (e) {}
  }
  setTimeout(() => {
    if (mediaStream) {
      mediaStream.getTracks().forEach(t => t.stop());
    }
  }, 250);

  const rawInput = document.getElementById("raw-input-text");
  if (rawInput && rawInput.value.trim()) {
    currentCase.original_transcript = rawInput.value.trim();
    currentCase.edited_transcript = rawInput.value.trim();
    validateStep1Form();
  }

  clearInterval(recordTimerInterval);

  // UI Updates
  document.getElementById("btn-stop-record")?.classList.add("hidden");
  document.getElementById("btn-start-record")?.classList.remove("hidden");
  document.getElementById("btn-rerecord")?.classList.remove("hidden");
  document.getElementById("waveform")?.classList.add("hidden");
  const micContainer = document.getElementById("mic-icon-container");
  if (micContainer) micContainer.className = "w-20 h-20 mx-auto rounded-full bg-gov-50 flex items-center justify-center text-3xl shadow-sm text-gov-700 transition";
  const hasTranscript = rawInput && rawInput.value.trim();
  const statusEl = document.getElementById("record-status-text");
  if (statusEl) {
    statusEl.innerText = hasTranscript ? getVoiceCopy("recordingFinished") : "Transcribing speech...";
  }
}

function rerecordVoice() {
  stopVoiceRecording();
  _sttPrefixTranscript = "";
  const rawInput = document.getElementById("raw-input-text");
  if (rawInput) rawInput.value = "";
  document.getElementById("audio-preview-box")?.classList.add("hidden");
  document.getElementById("btn-rerecord")?.classList.add("hidden");
  document.getElementById("understood-confirm-box")?.classList.add("hidden");
  document.getElementById("record-timer").innerText = "00:00";
  recordSeconds = 0;
  startVoiceRecording();
}

function formatTimer(sec) {
  const m = Math.floor(sec / 60).toString().padStart(2, "0");
  const s = (sec % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

function showRecordError(msg) {
  const banner = document.getElementById("record-error-banner");
  const msgEl = document.getElementById("record-error-message");
  const hintEl = document.getElementById("record-error-hint");

  if (banner && msgEl) {
    msgEl.innerText = msg;
    if (hintEl) {
      hintEl.innerText = getVoiceCopy("textFallbackHint");
    }
    banner.classList.remove("hidden");
  }
}

function dismissRecordError() {
  document.getElementById("record-error-banner")?.classList.add("hidden");
}

// Native 16kHz mono 16-bit PCM WAV converter for high-fidelity speech recognition
async function convertAudioBlobTo16kHzWav(blob) {
  try {
    const arrayBuffer = await blob.arrayBuffer();
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return blob;
    const audioCtx = new AudioContextClass();
    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

    const targetSampleRate = 16000;
    const targetLength = Math.max(1, Math.ceil(audioBuffer.duration * targetSampleRate));
    const offlineCtx = new OfflineAudioContext(1, targetLength, targetSampleRate);
    const source = offlineCtx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(offlineCtx.destination);
    source.start(0);
    const renderedBuffer = await offlineCtx.startRendering();

    const samples = renderedBuffer.getChannelData(0);
    const bufferLength = samples.length;
    const wavBuffer = new ArrayBuffer(44 + bufferLength * 2);
    const view = new DataView(wavBuffer);

    function writeStr(offset, str) {
      for (let i = 0; i < str.length; i++) {
        view.setUint8(offset + i, str.charCodeAt(i));
      }
    }

    writeStr(0, 'RIFF');
    view.setUint32(4, 36 + bufferLength * 2, true);
    writeStr(8, 'WAVE');
    writeStr(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, targetSampleRate, true);
    view.setUint32(28, targetSampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeStr(36, 'data');
    view.setUint32(40, bufferLength * 2, true);

    let offset = 44;
    for (let i = 0; i < bufferLength; i++, offset += 2) {
      let s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }

    return new Blob([wavBuffer], { type: 'audio/wav' });
  } catch (err) {
    console.warn("WAV conversion fallback to original blob:", err);
    return blob;
  }
}

async function uploadAudioBlob(blob) {
  const statusText = document.getElementById("record-status-text");
  try {
    if (!blob || blob.size < 50) {
      console.warn("Recorded audio blob is empty.");
      return;
    }

    if (statusText) statusText.innerText = "Transcribing speech...";

    const activeLang = document.getElementById("lang-select")?.value || currentCase.language || "hi";
    
    // Convert to 16kHz WAV for high-accuracy backend STT recognition
    let audioToSend = blob;
    try {
      audioToSend = await convertAudioBlobTo16kHzWav(blob);
    } catch (convErr) {
      console.warn("Audio conversion fallback to original blob:", convErr);
      audioToSend = blob;
    }

    const isWav = audioToSend.type === "audio/wav";
    const filename = `audio_${currentCase.id || "CASE"}.${isWav ? "wav" : "webm"}`;

    const formData = new FormData();
    formData.append("file", audioToSend, filename);
    formData.append("case_id", currentCase.id || "CASE");
    formData.append("language", activeLang);

    const headers = {};
    const token = getCurrentOperatorToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch("/api/upload-audio", {
      method: "POST",
      headers: headers,
      body: formData
    });

    if (res.ok) {
      const data = await res.json();
      if (data.url) currentCase.audio_file = data.url;

      // CRITICAL SPEECH-TO-TEXT SYNC:
      // Populate the EXISTING textarea immediately with the real transcription
      if (data.transcript && data.transcript.trim()) {
        const rawInput = document.getElementById("raw-input-text");
        if (rawInput) {
          rawInput.value = data.transcript.trim();
          currentCase.original_transcript = rawInput.value;
          currentCase.edited_transcript = rawInput.value;
          validateStep1Form();
          showUnderstoodConfirm();
        }
      } else {
        const rawInput = document.getElementById("raw-input-text");
        if (rawInput && !rawInput.value.trim()) {
          showRecordError("No speech detected in audio. Please speak clearly into microphone or type your statement.");
        }
      }
    } else {
      console.warn("Audio upload returned status:", res.status);
      const rawInput = document.getElementById("raw-input-text");
      if (rawInput && !rawInput.value.trim()) {
        showRecordError("Could not process audio. Please enter statement in textbox.");
      }
    }
  } catch (err) {
    console.warn("Audio upload background notice:", err);
    const rawInput = document.getElementById("raw-input-text");
    if (rawInput && !rawInput.value.trim()) {
      showRecordError("Network notice during audio upload. Please type statement in textbox.");
    }
  } finally {
    // ALWAYS clear the transcribing state in all paths
    if (statusText) {
      statusText.innerText = getVoiceCopy("recordingFinished");
    }
  }
}

function showUnderstoodConfirm() {
  const text = document.getElementById("raw-input-text")?.value.trim();
  const box = document.getElementById("understood-confirm-box");
  const confirmText = document.getElementById("understood-confirm-text");

  if (text && box && confirmText) {
    confirmText.innerText = getVoiceCopy("confirmation");
    box.classList.remove("hidden");
  }
}

function confirmAndProceedToStep2() {
  processVoiceOrTextInput();
}

function focusTranscriptEdit() {
  const input = document.getElementById("raw-input-text");
  if (input) {
    input.focus();
    input.scrollIntoView({ behavior: "smooth" });
  }
}

// ========================================================
// 7. STEP 1 -> STEP 2: FACT EXTRACTION & REVIEW
// ========================================================

async function processVoiceOrTextInput() {
  const consent = document.getElementById("consent-check")?.checked;
  if (!consent) {
    alert(getVoiceCopy("consentRequired"));
    return;
  }

  const rawText = document.getElementById("raw-input-text")?.value.trim();
  if (!rawText) {
    alert(getVoiceCopy("transcriptRequired"));
    return;
  }

  const extractionCaseId = currentCase.id;
  const extractionRequestId = ++extractionRequestGeneration;
  const extractionLanguage = currentCase.language;
  currentCase.original_transcript = rawText;
  currentCase.edited_transcript = rawText;

  document.getElementById("original-transcript-display").innerText = rawText;
  document.getElementById("edited-transcript-input").value = rawText;

  // Run fact extraction via backend
  try {
    const res = await fetch("/api/extract", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        transcript: rawText,
        language: extractionLanguage
      })
    });

    if (!res.ok) throw new Error("Fact extraction failed");
    const data = await res.json();
    if (currentCase.id !== extractionCaseId || extractionRequestGeneration !== extractionRequestId) return;

    currentCase.extracted_fields = data.extracted_fields || {};
    currentCase.missing_fields = data.missing_fields || [];
    currentCase.contradictions = data.contradictions || [];
    currentCase.template_type = data.recommended_template || "general";
    syncTemplateSelectionUI();
    updateVoiceGuideResponse();

    populateFormFields(currentCase.extracted_fields);
    renderMissingFieldsAlert(currentCase.missing_fields);
    renderContradictionAlert(currentCase.contradictions);
    updateSummaryCard();

    // Advance to Step 2 — mark Step 1 as complete first
    completedSteps.add(1);
    goToStep(2);
  } catch (err) {
    if (currentCase.id !== extractionCaseId || extractionRequestGeneration !== extractionRequestId) return;
    console.error("Extraction error:", err);
    alert(`${getVoiceCopy("extractionError")} ${err.message}`);
  }
}

function populateFormFields(fields) {
  document.getElementById("field-name").value = fields.citizen_name || "";
  document.getElementById("field-village").value = fields.village || "";
  document.getElementById("field-duration").value = fields.duration || "";
  document.getElementById("field-scheme").value = fields.scheme || "";
  document.getElementById("field-issue").value = fields.issue_type || "";
  document.getElementById("field-department").value = fields.department || "";

  // Set cascading state dropdown
  const stateSelect = document.getElementById("field-state-select");
  if (stateSelect && fields.state) {
    let matchedState = Object.keys(ADMIN_DIVISIONS).find(
      s => s.toLowerCase() === fields.state.toLowerCase()
    ) || fields.state;
    if (ADMIN_DIVISIONS[matchedState]) {
      stateSelect.value = matchedState;
      handleStateSelectionChange(matchedState, true);

      // Set cascading district dropdown
      const distSelect = document.getElementById("field-district-select");
      if (distSelect && fields.district) {
        let matchedDist = (ADMIN_DIVISIONS[matchedState].districts || []).find(
          d => d.toLowerCase() === fields.district.toLowerCase()
        ) || fields.district;
        distSelect.value = matchedDist;
        handleDistrictSelectionChange(matchedDist, true);
      }
    } else {
      document.getElementById("field-state").value = fields.state || "";
      document.getElementById("field-district").value = fields.district || "";
    }
  } else {
    document.getElementById("field-state").value = fields.state || "";
    document.getElementById("field-district").value = fields.district || "";
  }

  // Update header name
  const citNameEl = document.getElementById("current-citizen-name");
  if (citNameEl) citNameEl.innerText = fields.citizen_name || "Pending Input";
}

function renderMissingFieldsAlert(missingList) {
  const box = document.getElementById("missing-fields-box");
  const list = document.getElementById("missing-fields-list");
  if (!box || !list) return;

  list.innerHTML = "";
  clearMissingHighlights();

  if (missingList && missingList.length > 0) {
    missingList.forEach(m => {
      const li = document.createElement("li");
      li.innerText = m;
      list.appendChild(li);

      // Highlight input
      if (m.toLowerCase().includes("name")) highlightMissingField("field-name");
      if (m.toLowerCase().includes("village")) highlightMissingField("field-village");
      if (m.toLowerCase().includes("state")) highlightMissingField("field-state-select");
      if (m.toLowerCase().includes("district")) highlightMissingField("field-district-select");
      if (m.toLowerCase().includes("duration")) highlightMissingField("field-duration");
    });
    box.classList.remove("hidden");
  } else {
    box.classList.add("hidden");
  }
}

function highlightMissingField(elementId) {
  const el = document.getElementById(elementId);
  if (el) el.classList.add("field-missing-highlight");
}

function clearMissingHighlights() {
  document.querySelectorAll(".field-missing-highlight").forEach(el => {
    el.classList.remove("field-missing-highlight");
  });
}

function renderContradictionAlert(contradictions) {
  const box = document.getElementById("contradiction-alert-box");
  const list = document.getElementById("contradiction-list");
  if (!box || !list) return;

  list.innerHTML = "";
  if (contradictions && contradictions.length > 0) {
    contradictions.forEach(c => {
      const li = document.createElement("li");
      li.innerText = c;
      list.appendChild(li);
    });
    box.classList.remove("hidden");
  } else {
    box.classList.add("hidden");
  }
}

function dismissContradictionAlert() {
  document.getElementById("contradiction-alert-box")?.classList.add("hidden");
}

function focusFirstContradictionField() {
  document.getElementById("field-village")?.focus();
}

function updateSummaryCard() {
  const container = document.getElementById("summary-badge-grid");
  if (!container) return;

  const f = currentCase.extracted_fields;
  container.innerHTML = `
    <div class="p-2 bg-white rounded border border-slate-200">
      <div class="text-[10px] text-slate-400">Citizen:</div>
      <strong class="text-slate-900 truncate block">${f.citizen_name || 'Missing'}</strong>
    </div>
    <div class="p-2 bg-white rounded border border-slate-200">
      <div class="text-[10px] text-slate-400">Location:</div>
      <strong class="text-slate-900 truncate block">${f.village || 'Village'}, ${f.district || 'District'}</strong>
    </div>
    <div class="p-2 bg-white rounded border border-slate-200">
      <div class="text-[10px] text-slate-400">State / UT:</div>
      <strong class="text-slate-900 truncate block">${f.state || 'Select State'}</strong>
    </div>
    <div class="p-2 bg-white rounded border border-slate-200">
      <div class="text-[10px] text-slate-400">Duration:</div>
      <strong class="text-slate-900 truncate block">${f.duration || 'Unspecified'}</strong>
    </div>
  `;
}

function syncFormFieldsToState() {
  const f = currentCase.extracted_fields;
  const previousSearchContext = [f.state, f.district, f.issue_type, f.scheme, f.department].join("|");
  f.citizen_name = document.getElementById("field-name").value.trim();
  f.village = document.getElementById("field-village").value.trim();
  f.state = document.getElementById("field-state-select").value || document.getElementById("field-state").value;
  f.district = document.getElementById("field-district-select").value || document.getElementById("field-district").value;
  f.duration = document.getElementById("field-duration").value.trim();
  f.scheme = document.getElementById("field-scheme").value.trim();
  f.issue_type = document.getElementById("field-issue").value.trim();
  f.department = document.getElementById("field-department").value.trim();
  if (previousSearchContext !== [f.state, f.district, f.issue_type, f.scheme, f.department].join("|")) {
    clearCurrentSearchResults();
  }

  currentCase.edited_transcript = document.getElementById("edited-transcript-input").value.trim();
  currentCase.citizen_name = f.citizen_name;

  const mobileEl = document.getElementById('field-citizen-mobile');
  if (mobileEl && mobileEl.value) currentCase.citizen_mobile = mobileEl.value.replace(/\D/g, '');

  const nameEl = document.getElementById("current-citizen-name");
  if (nameEl) nameEl.innerText = f.citizen_name || "Pending Input";
}

// ========================================================
// 8. STEP 2 -> STEP 3: SEARCH OFFICIAL GOV SOURCES (SERPAPI)
// ========================================================

async function handleSearchOfficialGovSources() {
  if (!isStepCompleted(1)) {
    showStepGateBanner(_getStepGateMsg());
    goToStep(1);
    return;
  }
  syncFormFieldsToState();
  const f = currentCase.extracted_fields;

  // Validation
  const missing = [];
  if (!f.citizen_name) missing.push("Citizen Name is required.");
  if (!f.state) missing.push("State / Union Territory is required. Please select your State.");
  if (!f.district) missing.push("District is required. Please select your District.");
  if (!f.issue_type && !f.scheme) missing.push("Problem / Scheme description is required.");

  if (missing.length > 0) {
    renderMissingFieldsAlert(missing);
    const box = document.getElementById("missing-fields-box");
    if (box) box.scrollIntoView({ behavior: "smooth" });
    return;
  }

  // Location consistency validation
  if (f.state && f.district && ADMIN_DIVISIONS[f.state]) {
    const validDists = ADMIN_DIVISIONS[f.state].districts || [];
    if (!validDists.includes(f.district)) {
      const mismatchBox = document.getElementById("location-mismatch-box");
      if (mismatchBox) {
        document.getElementById("location-mismatch-text").innerText = `District '${f.district}' does not belong to the selected State '${f.state}'. Please review.`;
        mismatchBox.classList.remove("hidden");
        mismatchBox.scrollIntoView({ behavior: "smooth" });
      }
      return;
    }
  }

  // Build clean search query
  const query = buildGovernmentSearchQuery(f);
  document.getElementById("serp-query-input").value = query;
  currentCase.search_query = query;

  // Button spinner & duplicate request prevention
  const btn = document.getElementById("btn-serpapi-search");
  const spinner = document.getElementById("serpapi-btn-spinner");
  const btnText = document.getElementById("serpapi-btn-text");

  if (btn) btn.disabled = true;
  if (spinner) spinner.classList.remove("hidden");
  if (btnText) btnText.innerText = "Searching Official Gov Portals...";

  // Advance to Step 3 — mark Step 2 as complete first
  completedSteps.add(2);
  goToStep(3);

  // Execute SerpApi search
  await executeSerpSearchManual();

  // Reset button state
  if (btn) btn.disabled = false;
  if (spinner) spinner.classList.add("hidden");
  if (btnText) btnText.innerText = "🔎 Search Official Gov Sources via SerpApi →";
}

async function executeSerpSearchManual() {
  syncFormFieldsToState();
  const caseId = currentCase.id;
  const extractedFields = { ...currentCase.extracted_fields };
  const query = buildGovernmentSearchQuery(extractedFields);
  const requestGeneration = ++sourceSearchGeneration;
  if (sourceSearchController) sourceSearchController.abort();
  sourceSearchController = new AbortController();
  const requestController = sourceSearchController;
  const loading = document.getElementById("serp-loading");
  const container = document.getElementById("source-review-cards");
  const btn = document.getElementById("btn-manual-serp-search");

  currentCase.sources = [];
  currentCase.search_query = query;
  currentCase.discovered_portal = null;
  currentCase.selected_source = null;
  currentCase.claim_source_mappings = [];
  document.getElementById("serp-query-input").value = query;
  if (container) container.innerHTML = "";

  const linkEl = document.getElementById('submit-portal-external-link');
  if (linkEl) {
    linkEl.href = "#";
    linkEl.innerText = "";
    linkEl.classList.add('hidden');
  }
  const noticeEl = document.getElementById('route2-no-source-notice');
  if (noticeEl) noticeEl.classList.add('hidden');
  const tbody = document.getElementById("claim-mapping-tbody");
  if (tbody) tbody.innerHTML = "";

  if (loading) loading.classList.remove("hidden");
  if (btn) {
    btn.disabled = true;
    btn.innerText = "Searching...";
  }

  try {
    const res = await fetch("/api/search-sources", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query,
        extracted_fields: extractedFields
      }),
      signal: requestController.signal
    });

    if (!res.ok) throw new Error("Search request failed");
    const data = await res.json();
    if (requestGeneration !== sourceSearchGeneration || currentCase.id !== caseId) return;

    if (data.is_vague) {
      currentCase.sources = [];
      document.getElementById("serp-total-count").innerText = 0;
      document.getElementById("serp-gov-count").innerText = "0 Official Gov Domains";
      const engineTag = document.getElementById("serp-engine-tag");
      if (engineTag) {
        engineTag.innerHTML = `<span class="bg-amber-100 text-amber-900 border border-amber-300 px-2 py-0.5 rounded font-bold font-mono">SPECIFICATION REQUIRED</span>`;
      }
      if (container) {
        container.innerHTML = `
          <div class="p-4 bg-amber-50 border border-amber-300 rounded-xl text-xs text-amber-900 font-medium space-y-1">
            <div class="flex items-center space-x-1.5 font-bold text-amber-950">
              <span class="text-sm">⚠️</span>
              <span>Operator Note:</span>
            </div>
            <p>${data.vague_note || "Please specify the exact type (for example income certificate)."}</p>
          </div>
        `;
      }
      if (linkEl) {
        linkEl.href = "#";
        linkEl.innerText = "";
        linkEl.classList.add("hidden");
      }
      if (noticeEl) noticeEl.classList.add("hidden");
      return;
    }

    currentCase.sources = data.sources || [];
    currentCase.search_query = data.query;
    currentCase.is_national_fallback = data.is_national_fallback || false;
    document.getElementById("serp-query-input").value = data.query;

    document.getElementById("serp-total-count").innerText = data.total_results || 0;
    document.getElementById("serp-gov-count").innerText = `${data.official_sources_count || 0} Official Gov Domains`;

    // Engine badge & DEMO MODE tag
    const engineTag = document.getElementById("serp-engine-tag");
    if (data.is_demo_mode) {
      engineTag.innerHTML = `<span class="bg-amber-100 text-amber-900 border border-amber-300 px-2 py-0.5 rounded font-bold font-mono">DEMO MODE</span> <span class="text-slate-500">${data.engine}</span>`;
    } else {
      engineTag.innerHTML = `<span class="bg-emerald-100 text-emerald-900 border border-emerald-300 px-2 py-0.5 rounded font-bold font-mono">LIVE SERPAPI</span> <span class="text-slate-500">${data.engine}</span>`;
    }

    if (currentCase.sources.length === 0) {
      currentCase.discovered_portal = null;
      currentCase.selected_source = null;
      if (linkEl) {
        linkEl.href = "#";
        linkEl.innerText = "";
        linkEl.classList.add('hidden');
      }
      if (noticeEl) noticeEl.classList.remove('hidden');
    } else {
      const top = currentCase.sources[0];
      currentCase.discovered_portal = top;
      if (linkEl && top && top.url) {
        linkEl.href = top.url;
        linkEl.innerText = `Open Discovered Portal: ${top.title || top.domain} ↗`;
        linkEl.classList.remove('hidden');
      }
      if (noticeEl) noticeEl.classList.add('hidden');
    }

    renderSourceReviewCards(currentCase.sources);
    await loadClaimMappings();
    if (requestGeneration !== sourceSearchGeneration || currentCase.id !== caseId) return;
    saveCurrentCaseState();
  } catch (err) {
    if (requestGeneration !== sourceSearchGeneration || currentCase.id !== caseId || err.name === "AbortError") return;
    console.error("Search error:", err);
    if (container) {
      container.innerHTML = `<div class="p-4 bg-rose-50 border border-rose-200 rounded text-xs text-rose-700">Search error: ${err.message}. Please retry or check network connection.</div>`;
    }
  } finally {
    if (requestGeneration === sourceSearchGeneration && currentCase.id === caseId) {
      if (sourceSearchController === requestController) sourceSearchController = null;
      if (loading) loading.classList.add("hidden");
      if (btn) {
        btn.disabled = false;
        btn.innerText = "🔍 Re-Search Sources";
      }
    }
  }
}

function buildGovernmentSearchQuery(fields) {
  let service = (fields.service_intent || "").trim();
  
  // If no clean service_intent or contains non-ASCII characters, derive it
  if (!service || /[^\x00-\x7F]/.test(service)) {
    const text = ((fields.issue_type || "") + " " + (fields.scheme || "") + " " + (fields.problem_description || "")).toLowerCase();
    if (text.includes("scholarship") || text.includes("student") || text.includes("छात्रवृत्ति") || text.includes("शिक्षাবৃত্তি")) {
      service = "scholarship disbursement delay";
    } else if (text.includes("land") || text.includes("mutation") || text.includes("dakhil") || text.includes("जमीन") || text.includes("दाखिल खारिज")) {
      service = "land mutation revenue dispute";
    } else if (text.includes("praman") || text.includes("certificate") || text.includes("dakhla") || text.includes("प्रमाण") || text.includes("সার্টিফিকেট")) {
      if (text.includes("income") || text.includes("aay") || text.includes("आय") || text.includes("उत्पन्न")) {
        service = "income certificate delay";
      } else if (text.includes("caste") || text.includes("jati") || text.includes("जाति")) {
        service = "caste certificate delay";
      } else if (text.includes("birth") || text.includes("janam") || text.includes("जन्म")) {
        service = "birth certificate delay";
      } else if (text.includes("death") || text.includes("mrityu") || text.includes("मृत्यु")) {
        service = "death certificate delay";
      } else {
        service = "certificate issuance delay";
      }
    } else if (text.includes("road") || text.includes("pothole") || text.includes("drainage") || text.includes("सड़क") || text.includes("सड़क") || text.includes("नाली")) {
      service = "road repair drainage maintenance";
    } else if (text.includes("ration") || text.includes("pds") || text.includes("food") || text.includes("राशन") || text.includes("রেশন")) {
      service = "ration food grain distribution";
    } else if (text.includes("electric") || text.includes("power") || text.includes("bijli") || text.includes("बिजली") || text.includes("विद्युत")) {
      service = "electricity power outage complaint";
    } else if (text.includes("water") || text.includes("jal") || text.includes("pani") || text.includes("पानी") || text.includes("जल")) {
      service = "drinking water supply disruption";
    } else if (text.includes("pension") || text.includes("पेंशन") || text.includes("পেনশন")) {
      service = "social security pension delay";
    } else if (text.includes("kisan") || text.includes("किसान") || text.includes("কৃষक")) {
      service = "PM Kisan installment delay";
    } else if (fields.issue_type && !["general public grievance", "general grievance"].includes(fields.issue_type.toLowerCase()) && !/[^\x00-\x7F]/.test(fields.issue_type)) {
      service = fields.issue_type.trim();
    } else {
      // Clean English words only
      const desc = (fields.problem_description || "").trim();
      const englishTokens = desc.match(/[A-Za-z]{3,}/g) || [];
      const filler = new Set(["mera", "naam", "hai", "main", "from", "this", "that", "please", "help", "aavedan", "complaint", "issue", "problem", "portal"]);
      const filtered = englishTokens.filter(w => !filler.has(w.toLowerCase()));
      service = filtered.length > 0 ? filtered.slice(0, 3).join(" ") + " grievance" : "public grievance redressal";
    }
  }

  // Pure English query without site operator: service + state + district
  const parts = [service];
  if (fields.state && !["none", "unknown", "missing", "india", "select state"].includes(fields.state.toLowerCase())) {
    parts.push(fields.state);
  }
  if (fields.district && !["none", "unknown", "missing", "select district"].includes(fields.district.toLowerCase())) {
    parts.push(fields.district);
  }
  return parts.join(" ").replace(/[^\x00-\x7F]+/g, " ").replace(/\s+/g, " ").trim();
}

function renderSourceReviewCards(sources) {
  const container = document.getElementById("source-review-cards");
  if (!container) return;
  container.innerHTML = "";

  if (!sources || sources.length === 0) {
    container.innerHTML = `<div class="p-4 bg-amber-50 border border-amber-200 rounded text-xs text-amber-800 font-medium">⚠️ No sufficiently relevant official government source found for this grievance. Please refine the search query or verify details directly with the citizen.</div>`;
    return;
  }

  const hasDirectSolution = sources.some(s => s.classification === "DIRECT SOLUTION" || (s.relevance_status && s.relevance_status.startsWith("Direct Procedure Match") && !s.is_national_fallback && !s.relevance_status.includes("National reference")));

  if (!hasDirectSolution) {
    const notice = document.createElement("div");
    notice.className = "p-3 mb-3 bg-amber-50 border border-amber-300 rounded-lg text-xs text-amber-900 font-medium flex items-center space-x-2";
    notice.innerHTML = `<span class="text-base">⚠️</span><span><strong>Notice:</strong> No sufficiently relevant official government source found for this grievance. National reference portals are provided below. Operator to verify the exact state/local service.</span>`;
    container.appendChild(notice);
  }

  sources.forEach((s, idx) => {
    const card = document.createElement("div");
    card.className = "p-4 bg-white rounded-xl border border-slate-200 shadow-2xs space-y-2.5 hover:border-slate-300 transition";

    const isDirect = s.classification === "DIRECT SOLUTION" || (s.relevance_status && s.relevance_status.startsWith("Direct Procedure Match") && !s.is_national_fallback && !s.relevance_status.includes("National reference"));
    const isNational = s.classification === "NATIONAL REFERENCE" || s.is_national_fallback || (s.relevance_status && s.relevance_status.includes("National reference"));
    const isRelated = s.classification === "RELATED OFFICIAL INFORMATION" || (s.relevance_status && s.relevance_status.includes("Related Official Information"));

    let officialBadge = `<span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold font-mono text-[10px]">Official Gov Domain (.gov.in)</span>`;
    let statusLabel = s.relevance_status || "Procedure Reference";

    if (s.is_demoted || s.classification === "IRRELEVANT") {
      officialBadge = `<span class="px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-300 font-semibold font-mono text-[10px]">Demoted (Unrelated / Irrelevant)</span>`;
      card.className = "p-4 bg-slate-50/70 rounded-xl border border-slate-200 space-y-2.5 opacity-70";
    } else if (isNational) {
      officialBadge = `<span class="px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-semibold font-mono text-[10px]">National Reference (.gov.in)</span>`;
      statusLabel = "National reference. Operator to verify the exact state/local service.";
    } else if (isDirect) {
      officialBadge = `<span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300 font-semibold font-mono text-[10px]">Direct Solution</span>`;
    } else if (isRelated) {
      officialBadge = `<span class="px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 font-semibold font-mono text-[10px]">Related Official Information</span>`;
      statusLabel = "Related Official Information";
    } else if (!s.is_official) {
      officialBadge = `<span class="px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-semibold font-mono text-[10px]">Third-Party / Public Reference</span>`;
    }

    const verifiedBtnClass = s.operator_verified
      ? "bg-emerald-700 text-white font-bold"
      : "bg-white border border-slate-300 text-slate-700 hover:bg-slate-50";

    const verifiedLabel = s.operator_verified ? "✓ Operator Verified" : "Verify Source";

    const portalLink = isDirect
      ? `<a href="${s.url}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center space-x-1 px-3 py-1 bg-gov-700 hover:bg-gov-800 text-white rounded text-xs font-semibold shadow-2xs transition"><span>Open Official Portal</span> <span>↗</span></a>`
      : `<a href="${s.url}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center space-x-1 text-xs text-blue-700 hover:underline font-semibold"><span>View Portal</span> <span>↗</span></a>`;

    card.innerHTML = `
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
        <div class="flex items-center space-x-2">
          <span class="text-xs font-bold text-slate-500 font-mono">#${idx + 1}</span>
          <a href="${s.url}" target="_blank" rel="noopener noreferrer" class="text-xs font-bold text-blue-700 hover:underline">
            ${s.title} ↗
          </a>
        </div>
        <div class="flex items-center space-x-2">
          ${officialBadge}
          <button onclick="toggleVerifySource('${s.id}')" class="px-2.5 py-1 rounded text-[11px] transition ${verifiedBtnClass}">
            ${verifiedLabel}
          </button>
        </div>
      </div>

      <p class="text-xs text-slate-600 leading-relaxed">${s.snippet || 'No description provided'}</p>

      ${isDirect ? `
      <div class="p-3 bg-emerald-50/70 border border-emerald-200 rounded-lg text-xs space-y-1 text-slate-800">
        <div><strong class="text-slate-900">SOURCE:</strong> <span class="font-mono text-gov-800 font-semibold">${s.domain || s.title}</span></div>
        <div><strong class="text-slate-900">AUTHORITY:</strong> <span>${s.authority || "Operator to verify"}</span></div>
        <div><strong class="text-slate-900">WHY THIS IS RELEVANT:</strong> <span>${s.why_relevant || s.relevance_reason}</span></div>
        <div><strong class="text-slate-900">NEXT ACTION:</strong> <span>${s.next_action || "Operator to verify"}</span></div>
        <div class="pt-1.5">${portalLink}</div>
      </div>
      ` : `
      ${s.relevance_reason ? `<div class="p-2 bg-blue-50/80 border border-blue-100 rounded text-[11px] text-blue-900 font-medium leading-relaxed">💡 <strong>Relevance Rationale:</strong> ${s.relevance_reason}</div>` : ''}
      `}

      <div class="flex flex-wrap items-center justify-between text-[10px] text-slate-400 font-mono pt-1 border-t border-slate-50">
        <span>Domain: ${s.domain}</span>
        <span>Relevance: ${statusLabel}</span>
      </div>
    `;

    container.appendChild(card);
  });
}

function toggleVerifySource(sourceId) {
  const s = currentCase.sources.find(x => x.id === sourceId);
  if (s) {
    s.operator_verified = !s.operator_verified;
    renderSourceReviewCards(currentCase.sources);
    loadClaimMappings();
    saveCurrentCaseState();
  }
}

async function loadClaimMappings() {
  const caseId = currentCase.id;
  const requestGeneration = sourceSearchGeneration;
  const extractedFields = { ...currentCase.extracted_fields };
  const sources = [...currentCase.sources];
  try {
    const res = await fetch("/api/mappings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        extracted_fields: extractedFields,
        sources: sources
      })
    });

    if (!res.ok) return;
    const mappings = await res.json();
    if (currentCase.id !== caseId || sourceSearchGeneration !== requestGeneration) return;
    currentCase.claim_source_mappings = mappings;

    const tbody = document.getElementById("claim-mapping-tbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    mappings.forEach(m => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50";

      const badge = m.is_official_source
        ? `<span class="px-1.5 py-0.5 rounded bg-blue-50 text-blue-800 font-mono text-[10px]">${m.verification_status}</span>`
        : `<span class="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[10px]">${m.verification_status}</span>`;

      tr.innerHTML = `
        <td class="px-4 py-2 font-medium text-slate-900">${m.claim_text}</td>
        <td class="px-4 py-2 text-slate-500">${m.claim_type}</td>
        <td class="px-4 py-2 text-blue-700 font-mono text-[11px] truncate max-w-xs">${m.source_reference}</td>
        <td class="px-4 py-2">${badge}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Mapping error:", err);
  }
}

// ========================================================
// 9. OPERATOR VERIFICATION CHECKLIST
// ========================================================

function evaluateChecklist() {
  const chks = [
    "chk-citizen", "chk-transcript", "chk-required", "chk-contradiction",
    "chk-source", "chk-reviewed", "chk-template", "chk-final"
  ];
  let allChecked = true;
  chks.forEach(id => {
    const el = document.getElementById(id);
    if (el && !el.checked) allChecked = false;
  });

  const banner = document.getElementById("checklist-status-banner");
  if (banner) {
    if (allChecked) {
      banner.className = "p-3 bg-emerald-50 border border-emerald-300 rounded-lg text-xs text-emerald-900 font-bold flex items-center justify-between";
      banner.innerHTML = "<span>✓ All 8 Operator Verification Checkpoints Completed. Authorization Granted.</span>";
      currentCase.verification_status = "Operator Verified";
    } else {
      banner.className = "p-3 bg-amber-50 border border-amber-300 rounded-lg text-xs text-amber-900";
      banner.innerHTML = "<span>⚠️ Required operator verification checklist is currently pending. Please verify criteria below.</span>";
      currentCase.verification_status = "Needs Review";
    }
  }

  const statEl = document.getElementById("current-case-status");
  if (statEl) {
    statEl.className = allChecked
      ? "px-2 py-0.5 rounded font-semibold bg-emerald-100 text-emerald-800"
      : "px-2 py-0.5 rounded font-semibold bg-amber-100 text-amber-800";
    statEl.innerText = currentCase.verification_status;
  }
}

function quickVerifyAllChecklist() {
  const chks = [
    "chk-citizen", "chk-transcript", "chk-required", "chk-contradiction",
    "chk-source", "chk-reviewed", "chk-template", "chk-final"
  ];
  chks.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.checked = true;
  });
  evaluateChecklist();
}

async function handleProceedToCreateApplication() {
  if (!isStepCompleted(2)) {
    showStepGateBanner(_getStepGateMsg());
    goToStep(getMaxAllowedStep());
    return;
  }
  // Ensure checklist or prompt
  const chks = ["chk-citizen", "chk-required", "chk-source"];
  const missing = chks.some(id => !document.getElementById(id)?.checked);
  if (missing) {
    if (!confirm("Some operator verification checkpoints are pending. Would you like to quick-verify and proceed to generate the application?")) {
      return;
    }
    quickVerifyAllChecklist();
  }

  // Generate document via backend
  const generated = await generateFinalBilingualDocument();
  if (!generated) return;
  completedSteps.add(3);
  goToStep(4);
}

// ========================================================
// 10. STEP 4: DOCUMENT GENERATION & PDF EXPORT
// ========================================================

function syncTemplateSelectionUI() {
  const selected = (currentCase.template_type || "general").toString().toLowerCase();
  ["pension", "water", "general"].forEach(t => {
    const card = document.getElementById(`tmpl-card-${t}`);
    if (!card) return;
    const badge = card.querySelector("span.font-mono");
    if (t === selected) {
      card.className = "border-2 border-gov-700 bg-gov-50/40 rounded-xl p-3.5 cursor-pointer hover:shadow-xs transition";
      if (badge) {
        badge.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-gov-700 text-white font-bold";
        badge.innerText = "Selected";
      }
    } else {
      card.className = "border border-slate-200 bg-white rounded-xl p-3.5 cursor-pointer hover:shadow-xs transition";
      if (badge) {
        badge.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600";
        badge.innerText = "Standard";
      }
    }
  });
}

function selectTemplate(templateType) {
  currentCase.template_type = templateType;
  syncTemplateSelectionUI();
  generateFinalBilingualDocument();
}

async function generateFinalBilingualDocument() {
  syncFormFieldsToState();

  try {
    const headers = { "Content-Type": "application/json" };
    const token = getCurrentOperatorToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch("/api/generate-document", {
      method: "POST",
      headers: headers,
      body: JSON.stringify({
        case_data: currentCase
      })
    });

    if (res.status === 401) {
      redirectToOperatorLogin("Operator session expired. Please log in again to create the application.");
      return false;
    }
    if (!res.ok) throw new Error("Document generation failed");
    const docData = await res.json();
    currentCase.generated_documents = docData;

    renderBilingualPreview(docData);
    saveCurrentCaseState();

    // Show review modal (with validation result) before allowing PDF
    openDocReviewModal(docData, currentCase);
    return true;
  } catch (err) {
    console.error("Document generation error:", err);
    const errMsg = document.getElementById("doc-gen-error") || null;
    if (errMsg) { errMsg.textContent = "Document generation failed: " + err.message; errMsg.classList.remove("hidden"); }
    return false;
  }
}

function renderBilingualPreview(docData) {
  const regional = docData.regional_language || docData.hindi_application || {};
  const en = docData.english_application || {};

  document.getElementById("hi-doc-title").innerText = regional.title || "Grievance Application";
  document.getElementById("hi-doc-body-edit").value = regional.body || "";
  document.getElementById("hi-doc-sources").innerText = regional.sources_reference || "";
  document.getElementById("hi-doc-disclaimer").innerText = regional.disclaimer || "";

  document.getElementById("en-doc-title").innerText = en.title || "Grievance Application";
  document.getElementById("en-doc-body-edit").value = en.body || "";
  document.getElementById("en-doc-sources").innerText = en.sources_reference || "";
  document.getElementById("en-doc-disclaimer").innerText = en.disclaimer || "";
}

function switchDocTab(tabName) {
  const btnHi = document.getElementById("tab-btn-hi");
  const btnEn = document.getElementById("tab-btn-en");
  const btnSplit = document.getElementById("tab-btn-split");

  const viewHi = document.getElementById("doc-view-hi");
  const viewEn = document.getElementById("doc-view-en");
  const viewSplit = document.getElementById("doc-view-split");

  btnHi.className = "py-2 px-3 border-b-2 border-transparent text-slate-500 hover:text-slate-800 font-semibold text-xs";
  btnEn.className = "py-2 px-3 border-b-2 border-transparent text-slate-500 hover:text-slate-800 font-semibold text-xs";
  btnSplit.className = "py-2 px-3 border-b-2 border-transparent text-slate-500 hover:text-slate-800 font-semibold text-xs hidden md:block";

  viewHi.classList.add("hidden");
  viewEn.classList.add("hidden");
  viewSplit.classList.add("hidden");

  if (tabName === "hi") {
    btnHi.className = "py-2 px-3 border-b-2 border-gov-700 text-gov-800 font-bold text-xs";
    viewHi.classList.remove("hidden");
  } else if (tabName === "en") {
    btnEn.className = "py-2 px-3 border-b-2 border-gov-700 text-gov-800 font-bold text-xs";
    viewEn.classList.remove("hidden");
  } else if (tabName === "split") {
    btnSplit.className = "py-2 px-3 border-b-2 border-gov-700 text-gov-800 font-bold text-xs hidden md:block";
    viewSplit.classList.remove("hidden");
    viewSplit.innerHTML = `
      <div class="doc-sheet rounded-xl p-4 border border-slate-200 bg-white space-y-3">
        <h5 class="font-bold text-xs text-gov-800 font-regional">${document.getElementById("hi-doc-title").innerText}</h5>
        <div class="text-xs font-regional text-slate-700 whitespace-pre-wrap leading-relaxed">${document.getElementById("hi-doc-body-edit").value}</div>
      </div>
      <div class="doc-sheet rounded-xl p-4 border border-slate-200 bg-white space-y-3">
        <h5 class="font-bold text-xs text-gov-800">${document.getElementById("en-doc-title").innerText}</h5>
        <div class="text-xs text-slate-700 whitespace-pre-wrap leading-relaxed">${document.getElementById("en-doc-body-edit").value}</div>
      </div>
    `;
  }
}

function regenerateDocument() {
  generateFinalBilingualDocument();
}

function openPrintableWindow() {
  saveCurrentCaseState();
  const tokenParam = currentUser && currentUser.token ? `?token=${encodeURIComponent(currentUser.token)}` : "";
  window.open(`/document/${currentCase.id}${tokenParam}`, "_blank");
}

function downloadDocumentPDF() {
  saveCurrentCaseState();
  const regionalTitle = document.getElementById("hi-doc-title")?.innerText || "Grievance";
  const regionalBody = document.getElementById("hi-doc-body-edit")?.value || "";
  const regionalSources = document.getElementById("hi-doc-sources")?.innerText || "";
  const regionalDisclaimer = document.getElementById("hi-doc-disclaimer")?.innerText || "";

  const enTitle = document.getElementById("en-doc-title")?.innerText || "Grievance";
  const enBody = document.getElementById("en-doc-body-edit")?.value || "";
  const enSources = document.getElementById("en-doc-sources")?.innerText || "";
  const enDisclaimer = document.getElementById("en-doc-disclaimer")?.innerText || "";

  const citizen = currentCase.extracted_fields.citizen_name || "Citizen";
  const location = `${currentCase.extracted_fields.village || ''}, ${currentCase.extracted_fields.district || ''} (${currentCase.extracted_fields.state || ''})`;

  const container = document.createElement("div");
  container.style.padding = "24px";
  container.style.fontFamily = "'Inter', 'Noto Sans Devanagari', 'Noto Sans Bengali', sans-serif";
  container.style.color = "#1e293b";
  container.style.background = "#ffffff";

  container.innerHTML = `
    <div style="border-bottom: 2px solid #0f766e; padding-bottom: 8px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <h2 style="margin: 0; color: #0f766e; font-size: 18px; font-weight: bold;">आवाज़ अधिकार (Awaaz Adhikar)</h2>
        <div style="font-size: 10px; color: #64748b;">Citizen Grievance Documentation & Verification System</div>
      </div>
      <div style="text-align: right; font-size: 11px;">
        <div><strong>Case ID:</strong> ${currentCase.id}</div>
        <div style="color: #15803d; font-weight: bold;">✓ Operator Verified & Source-Backed</div>
      </div>
    </div>

    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 14px; margin-bottom: 16px; font-size: 11px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
      <div><strong>Citizen:</strong> ${citizen}</div>
      <div><strong>Location:</strong> ${location}</div>
    </div>

    <!-- Section 1 Regional -->
    <div style="margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px dashed #cbd5e1;">
      <h3 style="font-size: 13px; color: #0f172a; margin: 0 0 10px 0; background: #f1f5f9; padding: 4px 8px; border-left: 3px solid #0f766e;">
        SECTION 1: ${regionalTitle}
      </h3>
      <div style="font-size: 11px; white-space: pre-wrap; line-height: 1.6; color: #334155;">${regionalBody}</div>
      <div style="margin-top: 10px; padding: 8px 10px; background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 4px; font-size: 10px; color: #0369a1;">
        <strong>📌 Information References (आधिकारिक पोर्टल संदर्भ):</strong>
        <div style="white-space: pre-wrap; margin-top: 4px;">${regionalSources}</div>
      </div>
      <div style="margin-top: 6px; font-size: 9px; color: #64748b; font-style: italic;">${regionalDisclaimer}</div>
    </div>

    <!-- Section 2 English -->
    <div>
      <h3 style="font-size: 13px; color: #0f172a; margin: 0 0 10px 0; background: #f1f5f9; padding: 4px 8px; border-left: 3px solid #0f766e;">
        SECTION 2: Formal English Grievance Application
      </h3>
      <div style="font-size: 11px; white-space: pre-wrap; line-height: 1.6; color: #334155;">${enBody}</div>
      <div style="margin-top: 10px; padding: 8px 10px; background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 4px; font-size: 10px; color: #0369a1;">
        <strong>📌 Information References (Official Government Portals):</strong>
        <div style="white-space: pre-wrap; margin-top: 4px;">${enSources}</div>
      </div>
      <div style="margin-top: 6px; font-size: 9px; color: #64748b; font-style: italic;">${enDisclaimer}</div>
    </div>
  `;

  const opt = {
    margin: 10,
    filename: `AwaazAdhikar_${currentCase.id}.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2 },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
  };

  html2pdf().set(opt).from(container).save();
}

// ========================================================
// 11. CASE STATE & DASHBOARD CRUD
// ========================================================

function resetSearchResultsUI() {
  const queryInput = document.getElementById("serp-query-input");
  if (queryInput) queryInput.value = "";

  const container = document.getElementById("source-review-cards");
  if (container) container.innerHTML = "";

  const totalEl = document.getElementById("serp-total-count");
  if (totalEl) totalEl.innerText = "0";

  const govEl = document.getElementById("serp-gov-count");
  if (govEl) govEl.innerText = "0 Official Gov Domains";

  const engineTag = document.getElementById("serp-engine-tag");
  if (engineTag) {
    engineTag.innerHTML = '<span class="bg-slate-100 text-slate-600 border border-slate-300 px-2 py-0.5 rounded font-bold font-mono">WAITING</span>';
  }

  const tbody = document.getElementById("claim-mapping-tbody");
  if (tbody) tbody.innerHTML = "";

  const linkEl = document.getElementById('submit-portal-external-link');
  if (linkEl) {
    linkEl.href = "#";
    linkEl.innerText = "";
    linkEl.classList.add('hidden');
  }

  const noticeEl = document.getElementById('route2-no-source-notice');
  if (noticeEl) noticeEl.classList.add('hidden');

  const docErr = document.getElementById("doc-gen-error");
  if (docErr) docErr.classList.add("hidden");
}

function clearCurrentSearchResults() {
  sourceSearchGeneration += 1;
  if (sourceSearchController) {
    sourceSearchController.abort();
    sourceSearchController = null;
  }
  currentCase.sources = [];
  currentCase.search_query = "";
  currentCase.claim_source_mappings = [];
  currentCase.discovered_portal = null;
  currentCase.selected_source = null;
  resetSearchResultsUI();
  document.getElementById("serp-loading")?.classList.add("hidden");
  const manualSearchButton = document.getElementById("btn-manual-serp-search");
  if (manualSearchButton) {
    manualSearchButton.disabled = false;
    manualSearchButton.innerText = "🔍 Re-Search Sources";
  }
  const searchButton = document.getElementById("btn-serpapi-search");
  if (searchButton) searchButton.disabled = false;
  document.getElementById("serpapi-btn-spinner")?.classList.add("hidden");
}

function handleSearchContextChange() {
  clearCurrentSearchResults();
}

function startNewCase(switchToWorkspace = true) {
  extractionRequestGeneration += 1;
  completedSteps = new Set();
  _sttPrefixTranscript = "";
  clearStepGatingSession();

  currentCase = {
    id: `CASE-${Math.floor(1000 + Math.random() * 9000)}`,
    language: localStorage.getItem("awaaz_lang") || "hi",
    consent: true,
    citizen_name: "",
    original_transcript: "",
    edited_transcript: "",
    extracted_fields: {
      citizen_name: "",
      village: "",
      state: "",
      district: "",
      duration: "",
      issue_type: "",
      scheme: "",
      department: ""
    },
    missing_fields: [],
    contradictions: [],
    search_query: "",
    sources: [],
    claim_source_mappings: [],
    verification_status: "Needs Review",
    checklist_state: {},
    template_type: "general",
    template_version: "",
    generated_documents: {},
    audio_file: null,
    discovered_portal: null,
    selected_source: null
  };

  currentCase.sources = [];
  currentCase.search_query = "";
  currentCase.claim_source_mappings = [];
  currentCase.discovered_portal = null;
  currentCase.selected_source = null;
  currentCase.generated_documents = {};
  updateVoiceGuideResponse();
  renderBilingualPreview({ regional_language: {}, english_application: {} });

  document.getElementById("raw-input-text").value = "";
  document.getElementById("original-transcript-display").innerText = "(Waiting for input...)";
  document.getElementById("edited-transcript-input").value = "";
  document.getElementById("audio-preview-box")?.classList.add("hidden");
  document.getElementById("understood-confirm-box")?.classList.add("hidden");
  dismissRecordError();
  clearCurrentSearchResults();
  clearFormFields();
  syncTemplateSelectionUI();
  updateCaseHeader();
  validateStep1Form();
  updateStepTabLockState();

  if (switchToWorkspace) {
    switchView("workspace");
    goToStep(1);
  }
}

function clearFormFields() {
  document.getElementById("field-name").value = "";
  document.getElementById("field-village").value = "";
  document.getElementById("field-state-select").value = "";
  document.getElementById("field-state").value = "";
  document.getElementById("field-district-select").innerHTML = '<option value="">Select District</option>';
  document.getElementById("field-district-select").disabled = true;
  document.getElementById("field-district").value = "";
  document.getElementById("field-duration").value = "";
  document.getElementById("field-scheme").value = "";
  document.getElementById("field-issue").value = "";
  document.getElementById("field-department").value = "";
  const mobileEl = document.getElementById('field-citizen-mobile');
  if (mobileEl) { mobileEl.value = ''; mobileEl.readOnly = false; }
  const otpEl = document.getElementById('field-case-otp');
  if (otpEl) otpEl.value = '';
  const otpSection = document.getElementById('case-otp-verification-section');
  if (otpSection) otpSection.classList.add('hidden');
  const badge = document.getElementById('mobile-verification-badge');
  if (badge) { badge.innerText = 'Pending'; badge.className = 'text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300'; }
  const sendBtn = document.getElementById('btn-send-case-otp');
  if (sendBtn) { sendBtn.innerText = 'Send OTP'; sendBtn.disabled = false; }
  const verifyBtn = document.getElementById('btn-verify-case-otp');
  if (verifyBtn) { verifyBtn.innerText = 'Verify OTP'; verifyBtn.disabled = false; }
  const msg = document.getElementById('case-otp-msg');
  if (msg) msg.innerText = '';
  _caseOtpVerified = false;
  clearMissingHighlights();
}

function updateCaseHeader() {
  const idEl = document.getElementById("current-case-id");
  const nameEl = document.getElementById("current-citizen-name");
  const statEl = document.getElementById("current-case-status");

  if (idEl) idEl.innerText = currentCase.id;
  if (nameEl) nameEl.innerText = currentCase.citizen_name || "Pending Input";
  if (statEl) {
    statEl.innerText = currentCase.verification_status;
    statEl.className = currentCase.verification_status === "Operator Verified"
      ? "px-2 py-0.5 rounded font-semibold bg-emerald-100 text-emerald-800"
      : "px-2 py-0.5 rounded font-semibold bg-amber-100 text-amber-800";
  }
}

async function saveCurrentCaseState() {
  syncFormFieldsToState();
  const caseId = currentCase.id;
  const requestGeneration = sourceSearchGeneration;
  const caseSnapshot = JSON.stringify(currentCase);
  try {
    const headers = { "Content-Type": "application/json" };
    if (currentUser && currentUser.token) {
      headers["Authorization"] = `Bearer ${currentUser.token}`;
    }
    const res = await fetch("/api/cases", {
      method: "POST",
      headers: headers,
      body: caseSnapshot
    });
    if (res.ok) {
      const data = await res.json();
      if (currentCase.id === caseId && sourceSearchGeneration === requestGeneration) {
        currentCase = data;
        updateCaseHeader();
      }
    }
  } catch (err) {
    console.error("Save error:", err);
  }
}

async function loadStats() {
  try {
    const headers = {};
    const token = getCurrentOperatorToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch("/api/stats", { headers });
    if (res.ok) {
      const data = await res.json();
      document.getElementById("stat-total").innerText = data.total_cases || 0;
      document.getElementById("stat-in-review").innerText = data.in_review || 0;
      document.getElementById("stat-verified").innerText = data.verified || 0;
      document.getElementById("stat-generated").innerText = data.generated_documents || 0;
    }
  } catch (err) {
    console.error("Stats error:", err);
  }
}

async function loadRecentCases() {
  try {
    const headers = {};
    const token = getCurrentOperatorToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch("/api/cases", { headers });
    if (!res.ok) return;
    const cases = await res.json();
    const tbody = document.getElementById("cases-tbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (cases.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="px-4 py-8 text-center text-slate-400">No cases recorded yet. Click "Start New Citizen Case" or load a demo scenario above.</td></tr>`;
      return;
    }

    cases.forEach(c => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 transition";
      const statusBadge = c.verification_status === "Operator Verified"
        ? `<span class="px-2 py-0.5 rounded font-semibold bg-emerald-100 text-emerald-800">Operator Verified</span>`
        : `<span class="px-2 py-0.5 rounded font-semibold bg-amber-100 text-amber-800">Needs Review</span>`;

      const citizenName = c.citizen_name || c.extracted_fields?.citizen_name || "Unknown";
      const village = c.extracted_fields?.village ? `${c.extracted_fields.village}, ${c.extracted_fields.district || ''}` : "Pending";
      const issue = c.extracted_fields?.issue_type || c.template_type || "Grievance";
      const dateStr = c.created_at ? c.created_at.split("T")[0] : "Recent";

      tr.innerHTML = `
        <td class="px-4 py-3 font-mono font-bold text-gov-800">${c.id}</td>
        <td class="px-4 py-3 font-semibold text-slate-900">${citizenName}</td>
        <td class="px-4 py-3">${village}</td>
        <td class="px-4 py-3">${issue}</td>
        <td class="px-4 py-3">${statusBadge}</td>
        <td class="px-4 py-3 text-slate-500">${dateStr}</td>
        <td class="px-4 py-3 text-right space-x-2">
          <button onclick="openExistingCase('${c.id}')" class="px-2.5 py-1 bg-gov-700 text-white rounded font-medium hover:bg-gov-800 text-[11px]">Open Workspace</button>
          <button onclick="deleteExistingCase('${c.id}')" class="px-2 py-1 bg-slate-100 text-rose-600 rounded font-medium hover:bg-rose-50 text-[11px]" title="Delete Case">🗑️</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error loading cases:", err);
  }
}

async function openExistingCase(caseId, targetStep = null) {
  extractionRequestGeneration += 1;
  clearCurrentSearchResults();
  try {
    const headers = {};
    const token = getCurrentOperatorToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`/api/cases/${caseId}`, { headers });
    if (!res.ok) {
      console.warn("Case could not be retrieved:", caseId);
      return false;
    }
    const data = await res.json();
    currentCase = data;
    currentCase.template_type = data.template_type || "general";
    syncTemplateSelectionUI();
    updateVoiceGuideResponse();

    // Reconstruct valid completed steps from saved case data
    completedSteps = new Set();
    const hasStep1 = Boolean(
      (currentCase.original_transcript || currentCase.edited_transcript || "").trim().length > 0 &&
      currentCase.extracted_fields &&
      (currentCase.extracted_fields.citizen_name || currentCase.extracted_fields.issue_type || currentCase.extracted_fields.state)
    );
    if (hasStep1) completedSteps.add(1);

    const hasStep2 = hasStep1 && Boolean(
      currentCase.extracted_fields &&
      currentCase.extracted_fields.state &&
      currentCase.extracted_fields.district
    );
    if (hasStep2) completedSteps.add(2);

    const hasStep3 = hasStep2 && Boolean(
      currentCase.sources && currentCase.sources.length > 0
    );
    if (hasStep3) completedSteps.add(3);

    // Populate inputs
    document.getElementById("raw-input-text").value = currentCase.original_transcript || "";
    document.getElementById("original-transcript-display").innerText = currentCase.original_transcript || "";
    document.getElementById("edited-transcript-input").value = currentCase.edited_transcript || currentCase.original_transcript || "";

    validateStep1Form();
    populateFormFields(currentCase.extracted_fields || {});
    updateCaseHeader();
    updateStepTabLockState();
    switchView("workspace");

    if (currentCase.generated_documents && Object.keys(currentCase.generated_documents).length > 0) {
      renderBilingualPreview(currentCase.generated_documents);
    }
    if (currentCase.sources && currentCase.sources.length > 0) {
      renderSourceReviewCards(currentCase.sources);
    }

    if (targetStep) {
      goToStep(targetStep);
    } else if (hasStep3 && currentCase.generated_documents && Object.keys(currentCase.generated_documents).length > 0) {
      goToStep(4);
    } else if (hasStep2 && currentCase.sources && currentCase.sources.length > 0) {
      goToStep(3);
    } else if (hasStep1) {
      goToStep(2);
    } else {
      goToStep(1);
    }
  } catch (err) {
    console.error("Error opening case:", err);
  }
}

async function deleteExistingCase(caseId) {
  if (!confirm(`Are you sure you want to securely remove Case #${caseId}?`)) return;
  try {
    const headers = {};
    const token = getCurrentOperatorToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    await fetch(`/api/cases/${caseId}`, { method: "DELETE", headers });
    loadStats();
    loadRecentCases();
  } catch (err) {
    console.error("Error deleting case:", err);
  }
}

async function refreshDashboard() {
  const refreshBtns = document.querySelectorAll("button[onclick*='refreshDashboard'], #btn-refresh-dashboard, #btn-refresh-workspace");
  refreshBtns.forEach(b => {
    b.classList.add("opacity-60", "pointer-events-none");
    if (!b.dataset.origHtml) b.dataset.origHtml = b.innerHTML;
    b.innerHTML = "🔄 Refreshing...";
  });

  try {
    // 1. Refresh dashboard overview stats & recent cases table
    await loadStats();
    await loadRecentCases();

    // 2. Refresh active case data if a case is currently loaded
    if (currentCase && currentCase.id && currentCase.id !== "CASE-NEW") {
      const headers = {};
      const token = getCurrentOperatorToken();
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch(`/api/cases/${currentCase.id}`, { headers });
      if (res.ok) {
        if (currentView === "workspace") {
          const stepBefore = currentStep || 1;
          await openExistingCase(currentCase.id, stepBefore);
        } else {
          const freshData = await res.json();
          currentCase = freshData;
          updateCaseHeader();
        }
      } else if (currentView === "workspace") {
        updateCaseHeader();
      }
    } else if (currentView === "workspace") {
      updateCaseHeader();
    }
  } catch (err) {
    console.error("Refresh error:", err);
  } finally {
    setTimeout(() => {
      refreshBtns.forEach(b => {
        b.classList.remove("opacity-60", "pointer-events-none");
        if (b.dataset.origHtml) b.innerHTML = b.dataset.origHtml;
      });
    }, 250);
  }
}

// ========================================================
// 12. DEMO SCENARIOS
// ========================================================

async function loadDemoSamples() {
  try {
    const res = await fetch("/api/samples");
    if (!res.ok) return;
    const samples = await res.json();
    const container = document.getElementById("demo-chips-container");
    if (!container) return;
    container.innerHTML = "";

    samples.forEach(s => {
      const chip = document.createElement("div");
      chip.className = "bg-white p-3 rounded-lg border border-teal-200 hover:border-teal-500 cursor-pointer shadow-xs hover:shadow transition flex flex-col justify-between";
      chip.onclick = () => loadSampleScenario(s);
      chip.innerHTML = `
        <div>
          <div class="flex justify-between items-center text-xs">
            <strong class="text-slate-900">${s.title}</strong>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-teal-100 text-teal-800 font-mono uppercase">${s.language}</span>
          </div>
          <p class="text-[11px] text-slate-600 mt-1 line-clamp-2 italic">"${s.transcript}"</p>
        </div>
        <div class="mt-2 text-[10px] text-teal-700 font-semibold flex items-center justify-between">
          <span>Target: ${s.category.toUpperCase()}</span>
          <span>Load Scenario ⚡</span>
        </div>
      `;
      container.appendChild(chip);
    });
  } catch (err) {
    console.error("Error loading samples:", err);
  }
}

function loadSampleScenario(sample) {
  startNewCase();
  currentCase.language = sample.language;
  changeLanguage(sample.language);

  document.getElementById("raw-input-text").value = sample.transcript;
  currentCase.original_transcript = sample.transcript;
  currentCase.edited_transcript = sample.transcript;
  currentCase.template_type = sample.category || "general";

  validateStep1Form();
  updateCaseHeader();
  switchView("workspace");
  goToStep(1);

  // Show confirmation card directly
  showUnderstoodConfirm();
}

// ========================================================
// 13. SERPAPI CONFIGURATION MODAL
// ========================================================

function openSerpModal() {
  document.getElementById("serp-modal")?.classList.remove("hidden");
}

function closeSerpModal() {
  document.getElementById("serp-modal")?.classList.add("hidden");
}

async function saveSerpApiKey() {
  const key = document.getElementById("serp-key-input")?.value.trim();
  try {
    const headers = { "Content-Type": "application/json" };
    if (currentUser && currentUser.token) {
      headers["Authorization"] = `Bearer ${currentUser.token}`;
    }
    const res = await fetch("/api/update-config", {
      method: "POST",
      headers: headers,
      body: JSON.stringify({ serpapi_key: key })
    });
    if (res.ok) {
      const data = await res.json();
      const badge = document.getElementById("serp-badge-status");
      if (badge) {
        badge.innerText = data.active ? "LIVE KEY" : "DEMO MODE";
        badge.className = data.active
          ? "bg-emerald-600 text-white text-[10px] px-1.5 py-0.2 rounded font-mono"
          : "bg-blue-600 text-white text-[10px] px-1.5 py-0.2 rounded font-mono";
      }
      alert(data.message);
      closeSerpModal();
    }
  } catch (err) {
    alert("Error updating SerpApi key: " + err.message);
  }
}

// ============================================================
// CITIZEN TRACKING MODAL FUNCTIONS
// ============================================================

let _citizenTrackData = null;

function openCitizenTrackModal() {
  const modal = document.getElementById('citizen-track-modal');
  if (!modal) return;
  document.getElementById('track-step-1').classList.remove('hidden');
  document.getElementById('track-step-2').classList.add('hidden');
  document.getElementById('track-step-3').classList.add('hidden');
  document.getElementById('track-error-1').classList.add('hidden');
  document.getElementById('track-error-2').classList.add('hidden');
  document.getElementById('track-case-id').value = '';
  document.getElementById('track-mobile').value = '';
  document.getElementById('track-otp').value = '';
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function closeCitizenTrackModal() {
  const modal = document.getElementById('citizen-track-modal');
  if (modal) { modal.classList.add('hidden'); modal.classList.remove('flex'); }
  _citizenTrackData = null;
}

async function citizenRequestOtp() {
  const caseId = (document.getElementById('track-case-id').value || '').trim().toUpperCase();
  const mobile = (document.getElementById('track-mobile').value || '').trim().replace(/\D/g, '');
  const errEl = document.getElementById('track-error-1');
  errEl.classList.add('hidden');
  if (!caseId) { errEl.textContent = 'Please enter your Case ID.'; errEl.classList.remove('hidden'); return; }
  if (mobile.length < 10) { errEl.textContent = 'Please enter a valid 10-digit mobile number.'; errEl.classList.remove('hidden'); return; }
  const btn = document.getElementById('btn-request-otp');
  btn.disabled = true; btn.textContent = 'Sending...';
  try {
    const res = await fetch('/api/citizen/request-otp', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: caseId, mobile: mobile })
    });
    const data = await res.json();
    if (res.ok) {
      document.getElementById('track-step-1').classList.add('hidden');
      document.getElementById('track-step-2').classList.remove('hidden');
      const badge = document.getElementById('track-demo-badge');
      if (badge) badge.style.display = data.demo_mode ? '' : 'none';
    } else {
      errEl.textContent = data.detail || 'SMS service is not configured. Please contact the center directly.';
      errEl.classList.remove('hidden');
    }
  } catch (e) {
    errEl.textContent = 'Network error. Please try again.';
    errEl.classList.remove('hidden');
  } finally {
    btn.disabled = false; btn.textContent = 'Send One-Time Code \u2192';
  }
}

async function citizenVerifyOtp() {
  const caseId = (document.getElementById('track-case-id').value || '').trim().toUpperCase();
  const mobile = (document.getElementById('track-mobile').value || '').trim().replace(/\D/g, '');
  const otp = (document.getElementById('track-otp').value || '').trim();
  const errEl = document.getElementById('track-error-2');
  errEl.classList.add('hidden');
  if (!otp || otp.length < 4) { errEl.textContent = 'Please enter the one-time code.'; errEl.classList.remove('hidden'); return; }
  const btn = document.getElementById('btn-verify-otp');
  btn.disabled = true; btn.textContent = 'Verifying...';
  try {
    const res = await fetch('/api/citizen/track', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: caseId, mobile: mobile, otp: otp })
    });
    const data = await res.json();
    if (res.ok) {
      _citizenTrackData = data;
      showCitizenTrackResult(data);
    } else {
      errEl.textContent = data.detail || 'Invalid details provided.';
      errEl.classList.remove('hidden');
    }
  } catch (e) {
    errEl.textContent = 'Network error. Please try again.';
    errEl.classList.remove('hidden');
  } finally {
    btn.disabled = false; btn.textContent = '\uD83D\uDD0D Track My Complaint';
  }
}

function showCitizenTrackResult(data) {
  document.getElementById('track-step-2').classList.add('hidden');
  document.getElementById('track-step-3').classList.remove('hidden');
  document.getElementById('track-result-id').textContent = data.case_id || '';
  document.getElementById('track-result-name').textContent = data.citizen_name || '';
  document.getElementById('track-result-issue').textContent = data.issue_type || '';
  const loc = [data.village, data.district, data.state].filter(Boolean).join(', ');
  document.getElementById('track-result-location').textContent = loc || '';
  document.getElementById('track-result-date').textContent = data.created_at ? data.created_at.slice(0, 10) : '';
  document.getElementById('track-result-center').textContent = data.center_name || '';
  const statusMap = {
    'Operator Verified': { label: '✓ Verified — Ready to Submit', cls: 'bg-emerald-100 text-emerald-800' },
    'Operator Verified — Ready to Submit': { label: '✓ Verified — Ready to Submit', cls: 'bg-emerald-100 text-emerald-800' },
    'Needs Review': { label: '⏳ Under Review', cls: 'bg-amber-100 text-amber-800' },
    'Application Ready — Not Yet Submitted': { label: '📋 Ready to Submit', cls: 'bg-blue-100 text-blue-800' },
    'Submitted': { label: '📋 Ready to Submit', cls: 'bg-blue-100 text-blue-800' },
    'Under Review': { label: '⏳ Under Review', cls: 'bg-amber-100 text-amber-800' },
  };
  const statusInfo = statusMap[data.status] || { label: data.status, cls: 'bg-slate-100 text-slate-800' };
  const badge = document.getElementById('track-status-badge');
  badge.textContent = statusInfo.label;
  badge.className = 'text-xs font-bold px-2 py-1 rounded-full ' + statusInfo.cls;
  const pdfSection = document.getElementById('track-pdf-section');
  const pendingSection = document.getElementById('track-pending-section');
  if (data.pdf_available) {
    pdfSection.classList.remove('hidden'); pendingSection.classList.add('hidden');
  } else {
    pdfSection.classList.add('hidden'); pendingSection.classList.remove('hidden');
  }
}

async function citizenDownloadPdf() {
  if (!_citizenTrackData) return;
  const caseId = _citizenTrackData.case_id;
  const mobile = (document.getElementById('track-mobile').value || '').trim().replace(/\D/g, '');
  const otp = (document.getElementById('track-otp').value || '').trim();
  window.open('/api/citizen/pdf/' + caseId + '?mobile=' + encodeURIComponent(mobile) + '&otp=' + encodeURIComponent(otp), '_blank');
}

// ============================================================
// DOCUMENT REVIEW CARD MODAL FUNCTIONS
// ============================================================

let _pendingDocData = null;
let _pendingCaseData = null;

function openDocReviewModal(docData, caseData) {
  _pendingDocData = docData;
  _pendingCaseData = caseData;
  const modal = document.getElementById('doc-review-modal');
  if (!modal) { confirmDocReview(); return; }
  const original = (caseData.original_transcript || caseData.edited_transcript || '').substring(0, 600);
  document.getElementById('review-original').textContent = original || '(No original transcript available)';
  const enBody = ((docData.english_application || {}).body || '').substring(0, 800);
  document.getElementById('review-english').textContent = enBody;
  const regBody = ((docData.regional_language || {}).body || '').substring(0, 800);
  document.getElementById('review-regional').textContent = regBody;
  const lang = docData.language_primary || 'hi';
  const langNames = { hi: 'Hindi (\u0939\u093F\u0902\u0926\u0940)', mr: 'Marathi (\u092E\u0930\u093E\u0920\u0940)', bn: 'Bengali (\u09AC\u09BE\u0982\u09B2\u09BE)', en: 'English' };
  const lbl = document.getElementById('review-regional-label');
  if (lbl) lbl.textContent = (langNames[lang] || lang) + ' Application Wording';
  const validation = docData.validation || { valid: true, errors: [] };
  const validEl = document.getElementById('doc-review-valid-msg');
  const invalidEl = document.getElementById('doc-review-invalid-msg');
  const errEl = document.getElementById('doc-review-errors');
  const confirmBtn = document.getElementById('btn-review-confirm');
  if (validation.valid) {
    if (validEl) validEl.classList.remove('hidden');
    if (invalidEl) invalidEl.classList.add('hidden');
    if (errEl) errEl.classList.add('hidden');
    if (confirmBtn) confirmBtn.disabled = false;
  } else {
    if (validEl) validEl.classList.add('hidden');
    if (invalidEl) invalidEl.classList.remove('hidden');
    if (errEl) {
      errEl.innerHTML = '<strong>Validation Errors (fix before generating PDF):</strong><ul class="list-disc list-inside mt-1">' + validation.errors.map(function(e){return '<li>'+e+'</li>';}).join('') + '</ul>';
      errEl.classList.remove('hidden');
    }
    if (confirmBtn) confirmBtn.disabled = true;
  }
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function closeDocReviewModal() {
  const modal = document.getElementById('doc-review-modal');
  if (modal) { modal.classList.add('hidden'); modal.classList.remove('flex'); }
  _pendingDocData = null;
  _pendingCaseData = null;
}

function confirmDocReview() {
  const savedDoc = _pendingDocData;
  const savedCase = _pendingCaseData;
  closeDocReviewModal();
  if (savedCase && savedCase.id) {
    const token = getCurrentOperatorToken();
    if (!token) {
      redirectToOperatorLogin("Operator session expired. Please log in again to open the document.");
      return;
    }
    window.open('/document/' + savedCase.id + '?token=' + encodeURIComponent(token), '_blank');
  }
}

// ============================================================
// OPERATOR CASE CREATION SMS OTP FUNCTIONS
// ============================================================

let _caseOtpVerified = false;

async function sendCaseCreationOtp() {
  const mobileInput = document.getElementById('field-citizen-mobile');
  const mobile = (mobileInput?.value || '').replace(/\D/g, '');
  const caseId = currentCase.id;
  if (!caseId) { alert('Please save or start a case first.'); return; }
  if (mobile.length !== 10) { alert('Please enter a valid 10-digit mobile number.'); return; }

  const btn = document.getElementById('btn-send-case-otp');
  const badge = document.getElementById('mobile-verification-badge');
  const otpSection = document.getElementById('case-otp-verification-section');
  const msg = document.getElementById('case-otp-msg');

  if (btn) {
    btn.disabled = true;
    btn.innerText = 'Sending...';
  }

  const token = getCurrentOperatorToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const res = await fetch('/api/operator/send-case-otp', {
      method: 'POST',
      credentials: 'include',
      headers: headers,
      body: JSON.stringify({ case_id: caseId, mobile })
    });

    const data = await res.json();

    if (!res.ok) {
      if (res.status === 401) {
        if (msg) {
          msg.innerText = data.detail || 'Unauthorized: Valid operator authentication session required.';
          msg.className = 'text-xs font-medium text-rose-700';
        }
        if (badge) {
          badge.innerText = 'Auth Required';
          badge.className = 'text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-300';
        }
        alert('Operator session expired or required. Please log in to workspace.');
        redirectToOperatorLogin('Operator session expired. Please log in again.');
      } else {
        if (msg) {
          msg.innerText = data.detail || 'Failed to send OTP.';
          msg.className = 'text-xs font-medium text-rose-700';
        }
      }
      if (btn) btn.innerText = 'Send OTP';
      return;
    }

    // Success: OTP sent
    if (otpSection) otpSection.classList.remove('hidden');
    if (badge) {
      badge.innerText = 'OTP Sent';
      badge.className = 'text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 border border-blue-300';
    }
    if (msg) {
      msg.innerText = data.message || 'OTP sent successfully.';
      msg.className = 'text-xs font-medium text-green-700';
    }
    if (btn) btn.innerText = 'Resend OTP';
  } catch (e) {
    alert('Network error: ' + e.message);
    if (btn) btn.innerText = 'Send OTP';
  } finally {
    if (btn) {
      btn.disabled = false;
      if (btn.innerText === 'Sending...') {
        btn.innerText = 'Send OTP';
      }
    }
  }
}

async function verifyCaseCreationOtp() {
  const mobileInput = document.getElementById('field-citizen-mobile');
  const mobile = (mobileInput?.value || '').replace(/\D/g, '');
  const otpInput = document.getElementById('field-case-otp');
  const otp = (otpInput?.value || '').trim();
  const caseId = currentCase.id;
  if (!caseId) { alert('No active case to verify.'); return; }
  if (!otp || otp.length !== 6) { alert('Please enter the 6-digit OTP.'); return; }

  const btn = document.getElementById('btn-verify-case-otp');
  const msg = document.getElementById('case-otp-msg');
  const badge = document.getElementById('mobile-verification-badge');

  if (btn) {
    btn.disabled = true;
    btn.innerText = 'Verifying...';
  }

  const token = getCurrentOperatorToken();
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const res = await fetch('/api/operator/verify-case-otp', {
      method: 'POST',
      credentials: 'include',
      headers: headers,
      body: JSON.stringify({ case_id: caseId, mobile, otp })
    });

    const data = await res.json();

    if (res.ok && data.verified) {
      _caseOtpVerified = true;
      if (badge) {
        badge.innerText = '✓ Verified';
        badge.className = 'text-[10px] font-bold px-1.5 py-0.5 rounded bg-green-100 text-green-800 border border-green-300';
      }
      if (msg) {
        msg.innerText = '✓ Mobile verified successfully!';
        msg.className = 'text-xs font-medium text-green-700';
      }
      if (btn) {
        btn.innerText = 'Verified ✓';
        btn.disabled = true;
      }
      if (mobileInput) mobileInput.readOnly = true;
    } else {
      if (res.status === 401) {
        if (msg) {
          msg.innerText = data.detail || 'Unauthorized: Valid operator authentication session required.';
          msg.className = 'text-xs font-medium text-rose-700';
        }
        alert('Operator session expired. Please log in again.');
        redirectToOperatorLogin('Operator session expired. Please log in again.');
      } else {
        if (msg) {
          msg.innerText = data.detail || 'Invalid OTP. Please try again.';
          msg.className = 'text-xs font-medium text-rose-700';
        }
      }
      if (btn) {
        btn.disabled = false;
        btn.innerText = 'Verify OTP';
      }
    }
  } catch (e) {
    alert('Network error: ' + e.message);
    if (btn) {
      btn.disabled = false;
      btn.innerText = 'Verify OTP';
    }
  } finally {
    if (btn && !_caseOtpVerified) {
      btn.disabled = false;
      if (btn.innerText === 'Verifying...') {
        btn.innerText = 'Verify OTP';
      }
    }
  }
}

function submitApplicationAction() {
  const modal = document.getElementById('submit-guidance-modal');
  if (modal) {
    const topSource = (currentCase.sources || []).find(s => s.url && (s.is_official || s.operator_verified));
    const linkEl = document.getElementById('submit-portal-external-link');
    const noticeEl = document.getElementById('route2-no-source-notice');
    if (topSource && topSource.url) {
      if (linkEl) {
        linkEl.href = topSource.url;
        linkEl.innerText = `Open Discovered Portal: ${topSource.title || topSource.domain} ↗`;
        linkEl.classList.remove('hidden');
      }
      if (noticeEl) noticeEl.classList.add('hidden');
    } else {
      if (linkEl) {
        linkEl.href = "#";
        linkEl.innerText = "";
        linkEl.classList.add('hidden');
      }
      if (noticeEl) noticeEl.classList.remove('hidden');
    }
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }
}

function closeSubmitGuidanceModal() {
  const modal = document.getElementById('submit-guidance-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}
