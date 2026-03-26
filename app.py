import streamlit as st
import pandas as pd

from modules import dashboard
from modules import doctor
from modules.caregiver import show as show_caregiver
from modules import pharmacy
from modules import admin
from modules import ai_prediction
from modules import alerts
from modules import login
from modules import pdf_generator
from modules import patients
from modules import orders

st.set_page_config(
    page_title="Smart Pharmacy AI",
    page_icon="💊",
    layout="wide"
)

# ==================== SKY BLUE THEME (#90e0ef base) ====================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* Palette: sky #90e0ef · deep teal text #0a3d47 · borders #48b8ce · surfaces #f5fcfe */
:root {
    --sp-sky: #90e0ef;
    --sp-sky-mid: #6ecae0;
    --sp-sky-deep: #48b8ce;
    --sp-sky-pale: #c5eef6;
    --sp-surface: rgba(255, 255, 255, 0.92);
    --sp-surface-muted: #e8f8fc;
    --sp-text: #0a3d47;
    --sp-text-muted: #2d5c6a;
    --sp-text-soft: #4a7a8a;
    --sp-border: #48b8ce;
    --sp-border-light: rgba(72, 184, 206, 0.45);
    --sp-accent: #0d4c5c;
    --sp-accent-hover: #155f73;
}

/* ===== GLOBAL ===== */
html, body, p, span, input, textarea, select, button, a,
h1, h2, h3, h4, h5, h6, li, td, th, caption {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
/* Apply Inter only to Streamlit's own text elements, not internal layout divs */
[data-testid="stMarkdownContainer"] *,
[data-testid="stText"] *,
.stAlert p, .stSuccess p, .stError p, .stWarning p, .stInfo p {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Preserve Streamlit's icon font for arrows, toggles etc */
[data-testid="stExpanderToggleIcon"],
.material-symbols-rounded,
[class*="material"] {
    font-family: 'Material Symbols Rounded' !important;
}

.stApp {
    background: linear-gradient(165deg, var(--sp-sky-pale) 0%, var(--sp-sky) 48%, #7dd4e8 100%) !important;
    color: var(--sp-text) !important;
}

/* ===== TYPOGRAPHY ===== */
h1 {
    color: var(--sp-text) !important;
    font-weight: 900 !important;
    letter-spacing: -1px;
    font-size: 2rem !important;
}
h2 {
    color: var(--sp-text) !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px;
    font-size: 1.5rem !important;
}
h3 {
    color: var(--sp-text) !important;
    font-weight: 600 !important;
    font-size: 1.15rem !important;
}
h4 { color: var(--sp-text) !important; margin-top: 1rem !important; }
h5 { color: var(--sp-text-muted) !important; font-size: 0.85rem !important; font-weight: 600 !important;
     letter-spacing: 0.5px !important; margin-top: 1.2rem !important; margin-bottom: 0.5rem !important; }
h6 { color: var(--sp-text-soft) !important; margin-top: 0.8rem !important; }
p, span {
    color: var(--sp-text) !important;
}
/* Expander header — flex layout, prevent arrow/label overlap */
.streamlit-expanderHeader, [data-testid="stExpanderHeader"] {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    padding: 10px 14px !important;
    margin-top: 6px !important;
    background: var(--sp-surface) !important;
    border: 1px solid var(--sp-border-light) !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: var(--sp-text) !important;
    line-height: 1.5 !important;
    white-space: normal !important;
    overflow: visible !important;
    word-break: break-word !important;
}
/* Arrow icon — fixed width, right-aligned; replace Material ligature with clean chevron */
[data-testid="stExpanderToggleIcon"],
[data-testid="stExpanderHeader"] [data-testid="stExpanderToggleIcon"],
.streamlit-expanderHeader [data-testid="stExpanderToggleIcon"] {
    flex-shrink: 0 !important;
    flex-grow: 0 !important;
    min-width: 24px !important;
    width: 24px !important;
    margin-left: auto !important;
    order: 2 !important;
    font-family: 'Inter', sans-serif !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
/* Hide ALL content inside toggle — Material ligature (_arrow_right etc) bleeds as text */
[data-testid="stExpanderToggleIcon"] * {
    display: none !important;
    font-size: 0 !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
}
[data-testid="stExpanderToggleIcon"] {
    font-size: 0 !important; /* Hide any direct text/ligature */
    color: transparent !important;
    overflow: hidden !important;
}
/* Chevron: ▶ collapsed, ▼ expanded — shown via ::before */
[data-testid="stExpanderToggleIcon"]::before {
    content: "▶" !important;
    font-size: 12px !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--sp-text-muted) !important;
    line-height: 1 !important;
    display: block !important;
}
[data-testid="stExpanderHeader"][aria-expanded="true"] [data-testid="stExpanderToggleIcon"]::before {
    content: "▼" !important;
}
/* Expander label — takes remaining space, never overlaps icon */
[data-testid="stExpanderHeader"] p,
.streamlit-expanderHeader p {
    flex: 1 1 auto !important;
    min-width: 0 !important;
    margin: 0 !important;
    overflow: visible !important;
    white-space: normal !important;
    order: 1 !important;
}
a { color: var(--sp-accent) !important; }

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--sp-surface) 0%, var(--sp-sky-pale) 100%) !important;
    border-right: 1px solid var(--sp-border-light) !important;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: var(--sp-text-muted) !important;
}
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
    background: rgba(255,255,255,0.35) !important;
    border: 1px solid var(--sp-border-light) !important;
    border-radius: 8px !important;
    padding: 8px 14px !important;
    margin-bottom: 2px !important;
    transition: all 0.2s ease !important;
    color: var(--sp-text) !important;
    font-size: 13px !important;
}
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:hover {
    background: rgba(144, 224, 239, 0.55) !important;
    border-color: var(--sp-border) !important;
    color: var(--sp-accent) !important;
}
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label[data-checked="true"] {
    background: var(--sp-accent) !important;
    border-color: var(--sp-accent) !important;
    color: #fff !important;
}
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label[data-checked="true"] p,
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label[data-checked="true"] span {
    color: #fff !important;
}

/* ===== BUTTONS ===== */
.stButton > button,
.stButton > button p,
.stButton > button span,
.stButton > button label {
    background: var(--sp-accent) !important;
    color: #fff !important;
    border: 1px solid var(--sp-accent) !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 0.3px;
    transition: all 0.2s ease !important;
}
.stButton > button p,
.stButton > button span,
.stButton > button label {
    padding: 0 !important;
    margin: 0 !important;
}
.stButton > button:hover {
    background: var(--sp-accent-hover) !important;
    border-color: var(--sp-accent-hover) !important;
    transform: translateY(-1px);
}
.stButton > button:hover p,
.stButton > button:hover span,
.stButton > button:hover label {
    color: #fff !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
    background: #0a3a48 !important;
}
.stDownloadButton > button {
    background: var(--sp-accent) !important;
    color: #fff !important;
    border: 1px solid var(--sp-accent) !important;
    border-radius: 8px !important;
}

/* ===== INPUT FIELDS ===== */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background: var(--sp-surface) !important;
    border: 1px solid var(--sp-border-light) !important;
    border-radius: 8px !important;
    color: var(--sp-text) !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    transition: border-color 0.2s ease !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stNumberInput > div > div > input:focus {
    border-color: var(--sp-border) !important;
    box-shadow: 0 0 0 1px rgba(72, 184, 206, 0.35) !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: var(--sp-text-soft) !important;
}

/* Labels */
.stTextInput > label, .stTextArea > label,
.stNumberInput > label, .stSelectbox > label,
.stMultiSelect > label, .stRadio > label, .stSlider > label {
    color: var(--sp-text-muted) !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* ===== SELECT / MULTISELECT ===== */
/* BaseWeb used to use transparent here — sky page showed through; match text inputs (#fff). */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: #ffffff !important;
    border: 1px solid var(--sp-border-light) !important;
    border-radius: 8px !important;
    color: var(--sp-text) !important;
}
.stSelectbox [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"] {
    background: #ffffff !important;
    border-radius: 8px !important;
}
[data-baseweb="select"] > div:first-child {
    background-color: #ffffff !important;
}
.stMultiSelect [data-baseweb="input"] input {
    background: transparent !important;
    color: var(--sp-text) !important;
}
[data-baseweb="tag"] {
    background: var(--sp-accent) !important;
    color: #fff !important;
    border-radius: 4px !important;
}
/* Dropdown menus from select / multiselect */
[data-baseweb="menu"],
[data-baseweb="popover"] [data-baseweb="menu"] {
    background: #ffffff !important;
    border: 1px solid var(--sp-border-light) !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 18px rgba(13, 76, 92, 0.12) !important;
}
[data-baseweb="menu"] li,
[data-baseweb="menu"] [role="option"] {
    color: var(--sp-text) !important;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: transparent;
    border-bottom: 1px solid var(--sp-border-light);
    padding: 0;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 0 !important;
    padding: 10px 20px !important;
    color: var(--sp-text-soft) !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
    transition: all 0.2s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--sp-accent) !important;
}
.stTabs [aria-selected="true"] {
    color: var(--sp-accent) !important;
    border-bottom: 2px solid var(--sp-border) !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ===== METRICS ===== */
[data-testid="stMetric"] {
    background: var(--sp-surface) !important;
    border: 1px solid var(--sp-border-light) !important;
    border-radius: 12px !important;
    padding: 18px !important;
    box-shadow: 0 2px 12px rgba(13, 76, 92, 0.08) !important;
}
[data-testid="stMetricValue"] {
    color: var(--sp-accent) !important;
    font-weight: 800 !important;
    font-size: 26px !important;
}
[data-testid="stMetricLabel"] {
    color: var(--sp-text-muted) !important;
    font-weight: 500 !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* ===== EXPANDER wrapper ===== */
[data-testid="stExpander"] {
    background: var(--sp-surface-muted) !important;
    border: 1px solid var(--sp-border-light) !important;
    border-radius: 10px !important;
    overflow: visible !important;
}

/* ===== DATAFRAME ===== */
[data-testid="stDataFrame"] {
    border: 1px solid var(--sp-border-light) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ===== ALERTS ===== */
.stSuccess, [data-baseweb="notification"][kind="positive"] {
    background: var(--sp-surface) !important;
    border-radius: 8px !important;
    border: 1px solid var(--sp-border-light) !important;
    border-left: 3px solid #0d8a5b !important;
}
.stWarning, [data-baseweb="notification"][kind="warning"] {
    background: var(--sp-surface) !important;
    border-radius: 8px !important;
    border: 1px solid var(--sp-border-light) !important;
    border-left: 3px solid #c47a00 !important;
}
.stError, [data-baseweb="notification"][kind="negative"] {
    background: var(--sp-surface) !important;
    border-radius: 8px !important;
    border: 1px solid var(--sp-border-light) !important;
    border-left: 3px solid #c43d3d !important;
}
.stInfo, [data-baseweb="notification"][kind="info"] {
    background: var(--sp-surface) !important;
    border-radius: 8px !important;
    border: 1px solid var(--sp-border-light) !important;
    border-left: 3px solid var(--sp-border) !important;
}

/* ===== DIVIDER ===== */
hr { border-color: var(--sp-border-light) !important; }

/* ===== FORM ===== */
[data-testid="stForm"] {
    background: var(--sp-surface) !important;
    border: 1px solid var(--sp-border-light) !important;
    border-radius: 12px !important;
    padding: 24px !important;
}

/* ===== FILE UPLOADER ===== */
[data-testid="stFileUploader"] {
    background: var(--sp-surface-muted) !important;
    border: 1px dashed var(--sp-border) !important;
    border-radius: 10px !important;
    padding: 16px !important;
}

/* ===== PROGRESS ===== */
.stProgress > div > div > div {
    background: var(--sp-border) !important;
    border-radius: 4px !important;
}
.stProgress > div > div {
    background: var(--sp-border-light) !important;
    border-radius: 4px !important;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--sp-sky-pale); }
::-webkit-scrollbar-thumb { background: var(--sp-sky-deep); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--sp-accent); }

/* ===== RESPONSIVE MOBILE ===== */
@media (max-width: 768px) {
    .stApp { padding: 0 !important; }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; }
    [data-testid="stMetric"] { padding: 12px !important; }
    [data-testid="stMetricValue"] { font-size: 20px !important; }
    .stButton > button { padding: 8px 16px !important; font-size: 12px !important; }
    .stTabs [data-baseweb="tab"] { padding: 8px 12px !important; font-size: 12px !important; }
    section[data-testid="stSidebar"] { width: 240px !important; }
    [data-testid="stForm"] { padding: 16px !important; }
    [data-testid="column"] { padding: 0 4px !important; }
    .mobile-hide { display: none !important; }
}

@media (max-width: 480px) {
    h1 { font-size: 1.3rem !important; }
    h2 { font-size: 1.1rem !important; }
    .stTabs [data-baseweb="tab"] { padding: 6px 8px !important; font-size: 11px !important; }
}

/* ===== CAPTION ===== */
.stCaption, [data-testid="stCaption"] { color: var(--sp-text-soft) !important; font-size: 11px !important; }

/* ===== SLIDER ===== */
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: var(--sp-accent) !important;
    border-color: var(--sp-accent) !important;
}

/* ===== TOOLTIP ===== */
[data-testid="stTooltipIcon"] { color: var(--sp-text-soft) !important; }

/* ===== CHECKBOX ===== */
.stCheckbox label span { color: var(--sp-text-muted) !important; }

/* ===== HIDE SIDEBAR COLLAPSE BUTTON + Material Icons ligature bleed ===== */
/* The collapse button renders its icon as a text ligature which bleeds in some browsers */
[data-testid="collapsedControl"],
button[kind="header"],
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
    visibility: hidden !important;
}
/* Suppress any stray Material Icons text rendering in the sidebar header area */
section[data-testid="stSidebar"] > div:first-child > div:first-child > button {
    display: none !important;
}
/* Hide the top bar that shows icon text */
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
    min-height: 0 !important;
}
/* Prevent Material Icons from rendering literal ligature strings — SIDEBAR ONLY
   (expander toggle in main content uses same font; must NOT be hidden) */
section[data-testid="stSidebar"] .material-icons,
section[data-testid="stSidebar"] .material-symbols-outlined,
section[data-testid="stSidebar"] .material-symbols-rounded {
    font-size: 0 !important;
    color: transparent !important;
}
</style>
""", unsafe_allow_html=True)


# ==================== LOGIN CHECK ====================
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    login.login()
    st.stop()

if not login.verify_session():
    st.warning("Session expired. Please login again.")
    login.login()
    st.stop()


# ==================== SIDEBAR ====================
st.sidebar.markdown("""
<div style="padding:10px 0 16px 0; border-bottom:1px solid rgba(72,184,206,0.45); margin-bottom:12px;">
    <p style="margin:0; color:#0a3d47; font-size:18px; font-weight:800; letter-spacing:-0.5px;">
        💊 Smart Pharmacy
    </p>
    <p style="margin:2px 0 0 0; color:#2d5c6a; font-size:11px; letter-spacing:1px; text-transform:uppercase;">
        AI Platform
    </p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"""
<div style="background:rgba(255,255,255,0.65); border:1px solid rgba(72,184,206,0.5); border-radius:8px;
            padding:10px 14px; margin-bottom:12px;">
    <p style="margin:0; color:#2d5c6a; font-size:10px; text-transform:uppercase; letter-spacing:1px;">
        Signed in as
    </p>
    <p style="margin:3px 0 0 0; color:#0a3d47; font-weight:600; font-size:14px;">
        {st.session_state.username}
    </p>
    <p style="margin:2px 0 0 0; color:#4a7a8a; font-size:11px; text-transform:uppercase; letter-spacing:0.5px;">
        {st.session_state.role}
    </p>
</div>
""", unsafe_allow_html=True)

role = st.session_state.role
menu_options = login.get_menu_options(role)

menu = st.sidebar.radio(
    "Navigation", menu_options, label_visibility="collapsed", key="main_nav"
)

# ── Live alert count badge ──
try:
    from modules.alerts import get_low_stock_alerts, get_missed_dose_alerts, seed_inventory
    from modules.alerts import INVENTORY as _INV
    seed_inventory(_INV)
    _n_crit = len([a for a in get_low_stock_alerts() if a["severity"] == "critical"])
    _n_miss = len(get_missed_dose_alerts())
    _total_alerts = _n_crit + _n_miss
    if _total_alerts > 0:
        st.sidebar.markdown(f"""
<div style="background:rgba(255,230,232,0.95);border:1px solid rgba(220,80,80,0.45);border-radius:8px;
            padding:10px 14px;margin-top:4px;margin-bottom:4px;display:flex;
            align-items:center;gap:10px;box-shadow:0 1px 8px rgba(13,76,92,0.06);">
    <span style="font-size:18px;">🚨</span>
    <div>
        <p style="margin:0;color:#b71c1c;font-weight:700;font-size:13px;">{_total_alerts} Active Alerts</p>
        <p style="margin:0;color:#2d5c6a;font-size:11px;">{_n_crit} critical · {_n_miss} missed doses</p>
    </div>
</div>
""", unsafe_allow_html=True)
except Exception:
    pass

st.sidebar.markdown("---")
if st.sidebar.button("Logout", use_container_width=True):
    login.logout()
    st.rerun()

st.sidebar.markdown("""
<p style="color:#4a7a8a; font-size:10px; text-align:center; margin-top:20px;">
    v2.0 · MongoDB · JWT
</p>
""", unsafe_allow_html=True)


# ==================== PAGE ROUTING ====================
def show_pdf_generator():
    st.title("📄 PDF Generator")
    from modules.utils.db import get_all_prescriptions
    prescriptions = get_all_prescriptions()
    if not prescriptions:
        st.info("No prescriptions yet.")
        return

    options = [f"{p.get('prescription_id','')}: {p.get('patient_name','')}" for p in prescriptions]
    idx = st.selectbox("Select Prescription", range(len(options)), format_func=lambda x: options[x])

    if idx is not None:
        selected = prescriptions[idx]
        if st.button("Generate PDF"):
            with st.spinner("Generating..."):
                data = {
                    "Patient": selected.get("patient_name", ""),
                    "Doctor": selected.get("doctor_name", ""),
                    "Medicines": selected.get("medicines", ""),
                    "Caregiver": selected.get("caregiver", ""),
                    "Age": selected.get("age", ""),
                    "Instructions": selected.get("dosage", ""),
                }
                pdf = pdf_generator.generate_prescription_pdf(data)
                if pdf:
                    import os
                    from datetime import datetime
                    fn = f"rx_{selected.get('prescription_id','')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                    fp = os.path.join("data", fn)
                    os.makedirs("data", exist_ok=True)
                    pdf.output(fp)
                    st.success("PDF generated")
                    with open(fp, "rb") as f:
                        st.download_button("Download PDF", f.read(), fn, "application/pdf")


if menu == "🏥 Dashboard": dashboard.show()
elif menu == "👨‍⚕️ Doctor Module": doctor.show()
elif menu == "👨‍👩‍👦 Caregiver Dashboard": show_caregiver()
elif menu == "💊 Pharmacy Verification": pharmacy.show()
elif menu == "👤 Patient Management": patients.show()
elif menu == "📦 Orders": orders.show()
elif menu == "🧑‍💻 Admin Panel": admin.show()
elif menu == "🤖 AI Prediction": ai_prediction.show()
elif menu == "🚨 Alerts": alerts.show_alerts()
elif menu == "📄 PDF Generator": show_pdf_generator()