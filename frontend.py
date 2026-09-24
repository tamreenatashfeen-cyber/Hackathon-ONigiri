import streamlit as st
import base64
import os
from pathlib import Path
from typing import Optional
import requests

st.set_page_config(page_title="BoLocal", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------
# Load Logo
# ---------------------------------------------------------
LOGO_PATH = Path(__file__).parent / "icon.png"

def get_logo_base64():
    if LOGO_PATH.exists():
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_b64 = get_logo_base64()

# ---------------------------------------------------------
# Backend Integration Helpers
# ---------------------------------------------------------
BASE_URL = "http://127.0.0.1:8000"

def send_otp(phone: str, cnic: Optional[str] = None):
    try:
        payload = {"phone": phone, "cnic": cnic}
        response = requests.post(f"{BASE_URL}/send-otp", json=payload, timeout=5)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Backend connection failed: {e}"}

def verify_otp(phone: str, otp: str):
    try:
        payload = {"phone": phone, "otp": otp}
        response = requests.post(f"{BASE_URL}/verify-otp", json=payload, timeout=5)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Backend connection failed: {e}"}

def upload_worker_voice(worker_id: int, audio_input_file):
    """Handles Streamlit UploadedFile buffer directly without needing manual disk saves."""
    url = f"{BASE_URL}/process-voice/{worker_id}"
    try:
        if hasattr(audio_input_file, "getvalue"):
            file_bytes = audio_input_file.getvalue()
            filename = getattr(audio_input_file, "name", "worker_audio.wav")
        elif isinstance(audio_input_file, (bytes, bytearray)):
            file_bytes = audio_input_file
            filename = "worker_audio.wav"
        else:
            with open(audio_input_file, "rb") as f:
                file_bytes = f.read()
            filename = Path(audio_input_file).name

        files = {"audio_file": (filename, file_bytes, "audio/wav")}
        response = requests.post(url, files=files, timeout=45)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Voice service unavailable: {e}"}

def search_workers(service_type: str, area: str, urgency: Optional[str] = None):
    try:
        payload = {
            "service_type": "" if service_type == "All" else service_type,
            "area": area,
            "urgency": urgency
        }
        response = requests.post(f"{BASE_URL}/employer/search", json=payload, timeout=8)
        if response.status_code == 200:
            return response.json().get("workers", [])
        return []
    except requests.exceptions.RequestException:
        return []

# ---------------------------------------------------------
# GLOBAL CSS
# ---------------------------------------------------------
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');

  :root{
    --plum:#3B2E68;
    --plum-light:#4c3c85;
    --coral:#E76F61;
    --coral-soft:#F0968A;
    --mint:#B8E0D2;
    --cream:#FFF9F1;
  }

  html, body, [class*="css"] { font-family: 'Nunito', sans-serif; }

  .stApp { background: var(--cream); }
  #MainMenu { visibility: hidden; }

  .block-container,
  [data-testid="stMainBlockContainer"],
  [data-testid="block-container"] {
    padding-top: 2rem;
    max-width: 100% !important;
    padding-left: 3rem;
    padding-right: 3rem;
  }

  /* SIDEBAR */
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--plum) 0%, var(--plum-light) 100%);
  }
  section[data-testid="stSidebar"] * { color: var(--cream) !important; }

  section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.5rem !important;
  }
  section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"]:first-of-type {
    padding-top: 0 !important;
  }
  section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
    gap: 0.9rem !important;
  }

  .sidebar-brand { display: flex; align-items: center; gap: 10px; margin-bottom: 30px; margin-top: -25px; }
  .sidebar-brand img { width: 34px; height: 34px; object-fit: contain; }
  .sidebar-brand .word { font-size: 20px; font-weight: 900; }
  .sidebar-brand .word .bo { color: var(--coral-soft) !important; }

  section[data-testid="stSidebar"] div[data-testid="stButton"] {
    margin-bottom: 0 !important;
  }
  section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    text-align: left;
    padding: 10px 16px !important;
    font-weight: 700;
    width: 100%;
    margin-bottom: 0;
  }
  section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
    background: var(--coral-soft) !important;
    border-color: var(--coral-soft) !important;
  }

  /* BUTTONS */
  div[data-testid="stButton"] > button {
    background: var(--coral-soft);
    color: #fff;
    border: none;
    border-radius: 100px;
    font-weight: 700;
    padding: 10px 20px;
    width: 100%;
  }
  div[data-testid="stButton"] > button:hover { background: var(--plum); color: #fff; }
  div[data-testid="stButton"] > button:disabled { background: #f0ece4; color: #a49bb8; }

  .back-btn div[data-testid="stButton"] > button {
    background: transparent;
    color: var(--plum);
    border: none;
    font-weight: 700;
    width: auto;
    padding: 4px 0;
  }
  .back-btn div[data-testid="stButton"] > button:hover { background: transparent; color: var(--coral); }

  .filter-active div[data-testid="stButton"] > button {
    background: var(--plum) !important;
  }

  /* SPLASH */
  .st-key-splash_panel {
    background: linear-gradient(160deg, var(--plum) 0%, var(--plum-light) 100%);
    border-radius: 32px;
    padding: 60px 40px 40px;
    position: relative;
    overflow: hidden;
  }
  .splash-logo-row { text-align: center; position: relative; z-index: 2; }
  .splash-logo-row img { width: 84px; }
  .splash-word { font-size: 46px; font-weight: 900; letter-spacing: -0.02em; margin-top: 14px; }
  .splash-word .bo { color: var(--coral-soft); }
  .splash-word .lo { color: var(--cream); }
  .splash-tagline { color: rgba(255,249,241,0.75); font-size: 16px; margin-top: 8px; margin-bottom: 30px; }

  /* WORKER CARD */
  .st-key-worker_card {
    background: #fff; border-radius: 28px; padding: 50px;
    box-shadow: 0 20px 50px -30px rgba(59,46,104,0.25);
  }
  .status-badge {
    padding: 10px 24px; border-radius: 100px; font-weight: 800; font-size: 14px;
    display: inline-flex; align-items: center; gap: 8px; margin-bottom: 26px;
  }
  .status-badge.active { background: var(--mint); color: #245c48; }
  .status-badge.inactive { background: #f4d9d3; color: var(--coral); }
  .status-dot { width: 9px; height: 9px; border-radius: 50%; background: currentColor; }

  .mic-wrap { position: relative; width: 200px; height: 200px; margin: 0 auto 10px; }
  .mic-pulse {
    position: absolute; inset: 0; border-radius: 50%;
    background: linear-gradient(135deg, var(--coral-soft), var(--mint));
    opacity: 0.35; animation: pulse 2.4s ease-out infinite;
  }
  @keyframes pulse { 0%{transform:scale(.85);opacity:.4;} 70%{transform:scale(1.35);opacity:0;} 100%{opacity:0;} }
  .mic-btn {
    position: absolute; inset: 16px; border-radius: 50%;
    background: linear-gradient(135deg, var(--coral-soft), var(--mint));
    box-shadow: 0 22px 40px -16px rgba(231,111,97,0.45);
    display: flex; align-items: center; justify-content: center;
  }
  .mic-btn svg { width: 50px; height: 50px; }
  .worker-caption { text-align: center; margin-top: 14px; color: #8b81a3; font-size: 14px; }

  .info-label { font-size: 12px; font-weight: 800; color: #a49bb8; letter-spacing: .04em; }
  .info-card-big { background: var(--cream); border-radius: 18px; padding: 18px 20px; margin-bottom: 14px; }
  .info-card-big .value { font-size: 20px; font-weight: 900; color: var(--plum); margin-top: 4px; }
  .confirm-bubble { margin-top: 6px; background: var(--plum); color: var(--cream); padding: 14px 18px; border-radius: 16px 16px 16px 4px; font-size: 13.5px; }

  /* EMPLOYER */
  .emp-title { font-size: 26px; color: var(--plum); font-weight: 900; }
  .emp-sub { color: #8b81a3; margin-top: 2px; margin-bottom: 20px; }

  div[data-testid="stTextInput"] input {
    border-radius: 100px !important; padding: 14px 20px !important; border: none !important;
    box-shadow: 0 10px 30px -20px rgba(59,46,104,0.3);
  }

  .worker-card {
    background: #fff; border-radius: 20px; padding: 20px; margin-bottom: 8px;
    box-shadow: 0 14px 30px -22px rgba(59,46,104,0.3);
  }
  .avatar {
    width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center;
    justify-content: center; font-weight: 800; color: #fff; font-size: 15px; margin-bottom: 12px;
  }
  .wc-name { font-size: 15.5px; font-weight: 800; color: var(--plum); }
  .wc-meta { font-size: 12px; color: #9d94b3; margin-top: 3px; margin-bottom: 12px; }
  .wc-badge { display: inline-block; padding: 5px 13px; border-radius: 100px; font-size: 11px; font-weight: 800; background: var(--mint); color: #245c48; margin-bottom: 4px; }
  .wc-badge.off { background: #f0ece4; color: #a49bb8; }

  /* CONFIRMATION */
  .st-key-confirm_card {
    max-width: 520px; margin: 20px auto; text-align: center; background: #fff;
    border-radius: 28px; padding: 60px 40px; box-shadow: 0 20px 50px -30px rgba(59,46,104,0.25);
  }
  .check-circle { width: 90px; height: 90px; border-radius: 50%; background: var(--mint); display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; }
  .check-circle svg { width: 42px; height: 42px; }
  .confirm-card-inner { display: flex; align-items: center; gap: 14px; background: var(--cream); border-radius: 16px; padding: 16px 18px; text-align: left; margin-bottom: 24px; }

  /* CONTENT PAGES */
  .content-card { background: #fff; border-radius: 28px; padding: 50px; box-shadow: 0 20px 50px -30px rgba(59,46,104,0.25); }
  .content-card h2 { color: var(--plum); margin-bottom: 14px; }
  .content-card p { color: #5b5470; line-height: 1.7; }
  .content-card h3 { color: var(--plum); margin-top: 22px; margin-bottom: 6px; font-size: 16px; }
  .content-card .faq-q { color: var(--plum); font-weight: 800; margin-top: 16px; margin-bottom: 4px; }
  .team-member { margin-bottom: 22px; }
  .team-member .name { color: var(--plum); font-weight: 800; font-size: 16px; }
  .team-member .role { color: var(--coral); font-weight: 700; font-size: 13px; margin-bottom: 6px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if 'screen' not in st.session_state:
    st.session_state.screen = 'splash'
if 'is_active' not in st.session_state:
    st.session_state.is_active = False
if 'worker_area' not in st.session_state:
    st.session_state.worker_area = "G-11, Islamabad"
if 'worker_duration' not in st.session_state:
    st.session_state.worker_duration = "9 AM – 6 PM"
if 'worker_id' not in st.session_state:
    st.session_state.worker_id = 1
if 'last_reply_text' not in st.session_state:
    st.session_state.last_reply_text = '🔊 "Aap ka status active kar diya gaya hai"'
if 'last_reply_audio' not in st.session_state:
    st.session_state.last_reply_audio = None
if 'last_audio_hash' not in st.session_state:
    st.session_state.last_audio_hash = None
if 'selected_worker' not in st.session_state:
    st.session_state.selected_worker = None
if 'selected_filter' not in st.session_state:
    st.session_state.selected_filter = "All"
if 'employer_search_input' not in st.session_state:
    st.session_state.employer_search_input = "Gulberg"

def navigate_to(screen_name):
    st.session_state.screen = screen_name
    st.rerun()

def back_button(target="splash", label="← Back to Home"):
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    col = st.columns([1, 5])[0]
    with col:
        if st.button(label, key=f"back_{target}_{st.session_state.screen}"):
            navigate_to(target)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    logo_tag = f'<img src="data:image/png;base64,{logo_b64}">' if logo_b64 else ""
    st.markdown(f"""
    <div class="sidebar-brand">
        {logo_tag}
        <div class="word"><span class="bo">Bo</span>Local</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🏠 Splash"):
        navigate_to('splash')
    if st.button("🎙️ Worker"):
        navigate_to('worker')
    if st.button("🔍 Employer"):
        navigate_to('employer')
    if st.button("ℹ️ About"):
        navigate_to('about')
    if st.button("❓ Help"):
        navigate_to('help')
    if st.button("👥 Team"):
        navigate_to('team')

# ===========================================================
# SPLASH SCREEN
# ===========================================================
if st.session_state.screen == 'splash':
    with st.container(key="splash_panel"):
        logo_tag = f'<img src="data:image/png;base64,{logo_b64}">' if logo_b64 else ""
        st.markdown(f"""
        <div class="splash-logo-row">
            {logo_tag}
            <div class="splash-word"><span class="bo">Bo</span><span class="lo">Local</span></div>
            <div class="splash-tagline">Kaam bolo, kaam paao</div>
        </div>
        """, unsafe_allow_html=True)

        spacer_l, col1, col2, spacer_r = st.columns([2, 1.3, 1.3, 2])
        with col1:
            if st.button("I need work"):
                navigate_to('worker')
        with col2:
            if st.button("I need worker"):
                navigate_to('employer')

# ===========================================================
# WORKER SCREEN
# ===========================================================
elif st.session_state.screen == 'worker':
    back_button("splash")

    # Worker Registration / Switcher Expander
    with st.expander(f"🔐 Worker Phone / CNIC Verification (Worker ID: {st.session_state.worker_id})"):
        col_p, col_c, col_sb = st.columns([2, 2, 1])
        with col_p:
            p_val = st.text_input("Phone Number", placeholder="03001234567", key="login_phone")
        with col_c:
            c_val = st.text_input("CNIC (New Worker)", placeholder="37405-1234567-1", key="login_cnic")
        with col_sb:
            st.write("")
            if st.button("Send OTP"):
                otp_res = send_otp(p_val, c_val)
                if "error" in otp_res:
                    st.error(otp_res["error"])
                else:
                    st.success(otp_res.get("message", "OTP Sent!"))

        col_o, col_vb = st.columns([2, 1])
        with col_o:
            otp_val = st.text_input("Enter 4-digit OTP", placeholder="1234", key="login_otp")
        with col_vb:
            st.write("")
            if st.button("Verify OTP"):
                v_res = verify_otp(p_val, otp_val)
                if "error" in v_res:
                    st.error(v_res["error"])
                elif "worker_id" in v_res:
                    st.session_state.worker_id = v_res["worker_id"]
                    st.success(f"Verified! Using Worker ID: {st.session_state.worker_id}")
                    st.rerun()

    with st.container(key="worker_card"):
        left, right = st.columns([1, 1])

        with left:
            badge_class = "active" if st.session_state.is_active else "inactive"
            badge_text = "Active — Taking Requests" if st.session_state.is_active else "Inactive — Not Available"
            st.markdown(f"""
            <div style="text-align:center;">
                <div class="status-badge {badge_class}">
                    <span class="status-dot"></span>{badge_text}
                </div>
            </div>
            <div class="mic-wrap">
                <div class="mic-pulse"></div>
                <div class="mic-btn">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#2b1f4d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                        <line x1="12" y1="19" x2="12" y2="23"/>
                        <line x1="8" y1="23" x2="16" y2="23"/>
                    </svg>
                </div>
            </div>
            <div class="worker-caption">Tap the mic and say<br><b>"I'm free today from 9 to 6 in G-11"</b></div>
            """, unsafe_allow_html=True)

            audio = st.audio_input("Record your status")
            if audio is not None:
                audio_data = audio.getvalue()
                audio_hash = hash(audio_data)

                # Process only when a new recording is submitted (prevents infinite reload)
                if st.session_state.last_audio_hash != audio_hash:
                    st.session_state.last_audio_hash = audio_hash

                    with st.spinner("Processing voice command with AI pipeline..."):
                        res = upload_worker_voice(st.session_state.worker_id, audio)

                        if "error" in res:
                            st.error(res["error"])
                        else:
                            st.session_state.is_active = (res.get("updated_status") == "active")
                            p_info = res.get("pipeline_data", {})

                            if p_info.get("area"):
                                st.session_state.worker_area = p_info["area"]
                            if p_info.get("duration"):
                                st.session_state.worker_duration = p_info["duration"]
                            if p_info.get("reply_text"):
                                st.session_state.last_reply_text = f"🔊 \"{p_info['reply_text']}\""
                            if p_info.get("reply_audio_path") and os.path.exists(p_info["reply_audio_path"]):
                                st.session_state.last_reply_audio = p_info["reply_audio_path"]

                            st.success("Status updated!")
                            st.rerun()

        with right:
            st.markdown(f"""
            <div class="info-label">AREA</div>
            <div class="info-card-big"><div class="value">{st.session_state.worker_area}</div></div>
            <div class="info-label">AVAILABLE</div>
            <div class="info-card-big"><div class="value">{st.session_state.worker_duration}</div></div>
            <div class="confirm-bubble">{st.session_state.last_reply_text}</div>
            """, unsafe_allow_html=True)

            if st.session_state.last_reply_audio:
                st.audio(st.session_state.last_reply_audio)

# ===========================================================
# EMPLOYER SCREEN
# ===========================================================
elif st.session_state.screen == 'employer':
    back_button("splash")

    st.markdown("""
    <div class="emp-title">Find help nearby</div>
    <div class="emp-sub">Showing active workers in your area</div>
    """, unsafe_allow_html=True)

    query_val = st.text_input("Search area or service", value=st.session_state.employer_search_input)
    if query_val != st.session_state.employer_search_input:
        st.session_state.employer_search_input = query_val

    # Filters
    filters = ["All", "Cleaning", "Cooking", "Laundry"]
    filter_cols = st.columns(4)
    for i, f in enumerate(filters):
        with filter_cols[i]:
            is_on = (st.session_state.selected_filter == f)
            if is_on:
                st.markdown('<div class="filter-active">', unsafe_allow_html=True)
            if st.button(f, key=f"filter_{f}"):
                st.session_state.selected_filter = f
                st.rerun()
            if is_on:
                st.markdown('</div>', unsafe_allow_html=True)

    # 1. Query Backend Database
    raw_workers = search_workers(
        service_type=st.session_state.selected_filter,
        area=st.session_state.employer_search_input
    )

    # 2. Present matched workers or fallback demo
    if raw_workers:
        visible_workers = []
        palette = ["#E76F61", "#3B2E68", "#245c48", "#9d94b3"]
        for idx, w in enumerate(raw_workers):
            visible_workers.append({
                "id": str(w.get("id")),
                "name": w.get("phone", f"Worker #{w.get('id')}"),
                "meta": f"{w.get('area', 'Islamabad')} · {w.get('service_type', 'General')}",
                "color": palette[idx % len(palette)],
                "active": (w.get("status") == "active")
            })
    else:
        demo_workers = [
            {"id": "w1", "name": "Rukhsana Bibi", "meta": "G-11 · Cleaning, Cooking", "color": "#E76F61", "active": True, "tags": ["Cleaning", "Cooking"]},
            {"id": "w2", "name": "Shaista Kausar", "meta": "F-10 · Laundry", "color": "#3B2E68", "active": True, "tags": ["Laundry"]},
            {"id": "w3", "name": "Aasia Manzoor", "meta": "G-9 · Cleaning", "color": "#9d94b3", "active": False, "tags": ["Cleaning"]},
        ]
        if st.session_state.selected_filter == "All":
            visible_workers = demo_workers
        else:
            visible_workers = [w for w in demo_workers if st.session_state.selected_filter in w["tags"]]

    st.write("")

    if not visible_workers:
        st.info(f"No workers found for '{st.session_state.selected_filter}' right now.")
    else:
        cols = st.columns(3)
        for i, w in enumerate(visible_workers):
            initials = "".join([n[0] for n in w["name"].split()[:2]]).upper()
            badge_class = "" if w["active"] else "off"
            badge_text = "Active" if w["active"] else "Offline"
            with cols[i % 3]:
                st.markdown(f"""
                <div class="worker-card">
                    <div class="avatar" style="background:{w['color']}">{initials}</div>
                    <div class="wc-name">{w['name']}</div>
                    <div class="wc-meta">{w['meta']}</div>
                    <div class="wc-badge {badge_class}">{badge_text}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Contact", key=f"contact_{w['id']}", disabled=not w["active"]):
                    st.session_state.selected_worker = w
                    navigate_to('confirm')

# ===========================================================
# CONFIRMATION SCREEN
# ===========================================================
elif st.session_state.screen == 'confirm':
    back_button("employer", "← Back to search")

    worker = st.session_state.selected_worker or {"name": "The worker", "meta": "", "color": "#E76F61"}
    initials = "".join([n[0] for n in worker["name"].split()[:2]]).upper()

    with st.container(key="confirm_card"):
        st.markdown(f"""
        <div class="check-circle">
            <svg viewBox="0 0 24 24" fill="none" stroke="#245c48" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
            </svg>
        </div>
        <h2 style="color:var(--plum); margin-bottom:8px;">{worker['name']} has been notified</h2>
        <p style="color:#8b81a3; margin-bottom:20px;">She'll call you back within a few minutes to confirm timing.</p>
        <div class="confirm-card-inner">
            <div class="avatar" style="background:{worker['color']}; margin-bottom:0;">{initials}</div>
            <div><div class="wc-name">{worker['name']}</div><div class="wc-meta" style="margin-bottom:0;">{worker.get('meta','')}</div></div>
        </div>
        """, unsafe_allow_html=True)

# ===========================================================
# ABOUT / HELP / TEAM
# ===========================================================
elif st.session_state.screen == 'about':
    back_button("splash")
    st.markdown("""
<div class="content-card">
<h2>About BoLocal</h2>
<p>
BoLocal is a voice-first hiring platform that connects households directly with
local domestic workers — maids, sweepers, and cleaners — without the barriers
that make this process slow and unreliable today.
</p>

<h3>The Problem</h3>
<p>
In most communities, finding trustworthy domestic help still relies on word-of-mouth:
asking neighbors, waiting weeks for a referral, or hoping someone reliable happens to
be free. On the worker's side, the challenge is just as real — many domestic workers
are illiterate and simply cannot use typing-based apps to list their services or manage
their availability. Add to this the complete absence of identity or age verification in
informal hiring, and you get a system where trust is low, safety is uncertain, and
underage labor can go unchecked.
</p>

<h3>The Solution</h3>
<p>
BoLocal removes the biggest barrier first: literacy. Instead of typing, a worker simply
speaks — "I'm free today from 9 to 6 in G-11" — and the app listens, understands, and
updates their availability automatically. No forms, no menus, no reading required. On the
other side, an employer searching for help can type or speak naturally too, such as
"I need a maid in Gulberg right now," and the app instantly finds and lists verified,
currently active workers nearby.
</p>
<p>
Every account is created through CNIC and phone number verification with an OTP, which
does double duty: it builds real trust between strangers, and it quietly blocks anyone
under 18 from signing up, since CNICs in Pakistan are only issued at that age — turning
identity verification into a built-in child-labor safeguard, without needing a separate
system for it.
</p>

<h3>How It Works (Technology)</h3>
<p>
<b>Speech-to-Text:</b> Groq-hosted Whisper (whisper-large-v3-turbo) converts the worker's
or employer's spoken words into text in real time.<br><br>
<b>Intent Understanding:</b> Groq-hosted Llama 3.3 70B parses that text to extract
structured meaning — availability status, area, duration, or search intent — as clean JSON.<br><br>
<b>Voice Response:</b> edge-tts converts confirmations back into spoken Urdu audio, so the
worker hears "Aap ka status active kar diya gaya hai" instead of having to read it.<br><br>
<b>Reliability:</b> tenacity wraps every API call with automatic retries, so a slow network
doesn't crash the experience mid-conversation.<br><br>
<b>Backend:</b> A FastAPI + Uvicorn server handles verification, matching, and data storage.
</p>

<h3>Why It Matters</h3>
<p>
BoLocal isn't just a convenience app — it's designed around the reality of who actually
needs it. By making voice the primary interface rather than an add-on feature, it opens up
digital hiring to a workforce that most apps quietly exclude, while giving households a
faster, safer way to find help they can trust.
</p>
</div>
    """, unsafe_allow_html=True)

elif st.session_state.screen == 'help':
    back_button("splash")
    st.markdown("""
<div class="content-card">
<h2>Help & FAQs</h2>

<h3>For Workers</h3>
<div class="faq-q">Q: How do I set my availability?</div>
<p>Tap the microphone button and speak naturally — for example, "Main abhi free hoon,
Gulberg mein 2 ghante ke liye." You don't need to type anything. The app listens,
understands what you said, and updates your status automatically.</p>

<div class="faq-q">Q: What if the app doesn't understand me correctly?</div>
<p>Just tap the mic again and repeat yourself a little more clearly. There's no limit on
how many times you can try — the app will keep listening until it gets it right.</p>

<div class="faq-q">Q: Do I need to know how to read or write to use this app?</div>
<p>No. BoLocal is built specifically so that reading and writing are never required. Every
interaction — setting your status, hearing confirmations — happens through voice.</p>

<div class="faq-q">Q: Why do I need to verify with my CNIC and phone number?</div>
<p>This keeps you and the households you work with safe. Verified accounts build trust with
employers, and it also confirms you're old enough to work, since CNICs are only issued at 18.</p>

<div class="faq-q">Q: Will my personal information be shared publicly?</div>
<p>No. Only your verification status (verified), name, general area, and availability are
visible to employers — your CNIC number itself is never shown to anyone.</p>

<h3>For Employers</h3>
<div class="faq-q">Q: How do I find a worker?</div>
<p>Type or speak what you need — for example, "Mujhe Gulberg mein maid chahiye abhi." The
app will show you a list of currently active, verified workers nearby.</p>

<div class="faq-q">Q: How do I know a worker is trustworthy?</div>
<p>Every worker on BoLocal has completed CNIC and phone OTP verification before they can
create an account. Look for the "Active" badge, which means they're verified and currently
available.</p>

<div class="faq-q">Q: What if no workers are shown for my search?</div>
<p>Try broadening your filter (for example, select "All" instead of a specific task) or
check back shortly, since worker availability updates in real time as they toggle their
own status.</p>

<div class="faq-q">Q: How do I contact a worker I find?</div>
<p>Tap "Contact" on their card. You'll see a confirmation, and the worker will be notified
directly so they can reach out to confirm timing.</p>

<h3>General</h3>
<div class="faq-q">Q: What languages does BoLocal support?</div>
<p>The app is designed around Urdu and Roman Urdu voice input, since that's the everyday
language of the workers it serves, alongside English for typed employer searches.</p>

<div class="faq-q">Q: Is my data secure?</div>
<p>Yes. Verification data is used only to confirm identity and is not shared publicly. All
API communication is handled securely through encrypted requests.</p>
</div>
    """, unsafe_allow_html=True)

elif st.session_state.screen == 'team':
    back_button("splash")
    st.markdown("""
<div class="content-card">
<h2>Our Team</h2>

<div class="team-member">
<div class="name">Tamreena Tashfeen</div>
<div class="role">Idea & Voice/AI Development</div>
<p>Conceived the original concept behind BoLocal — solving domestic worker hiring
through a voice-first, literacy-free experience. Built the entire voice pipeline
(speech-to-text via Groq Whisper, intent parsing via Llama 3.3 70B, and voice
responses via edge-tts), and developed the app's frontend interface.</p>
</div>

<div class="team-member">
<div class="name">Ayan Touqeer</div>
<div class="role">Backend Development</div>
<p>Built the backend systems powering BoLocal, including the database architecture,
CNIC and OTP-based identity verification, and the worker-employer matching logic
that connects real-time voice input to search results.</p>
</div>

<div class="team-member">
<div class="name">Mehmona Tehran</div>
<div class="role">Design & Documentation</div>
<p>Led the brand identity for BoLocal, including the logo and color palette, and
managed the project's documentation, research, and pitch materials — including the
problem statement, tech stack write-up, and presentation content submitted for
judging.</p>
</div>

<p style="margin-top:10px; color:#9d94b3; font-size:13px;">
Built for the WeAreDevelopers Hackathon, September 2026.
</p>
</div>
    """, unsafe_allow_html=True)