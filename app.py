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

# ==================== MINIMALIST B&W THEME ====================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

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
    background: #000 !important;
    color: #fff !important;
}

/* ===== TYPOGRAPHY ===== */
h1 {
    color: #fff !important;
    font-weight: 900 !important;
    letter-spacing: -1px;
    font-size: 2rem !important;
}
h2 {
    color: #fff !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px;
    font-size: 1.5rem !important;
}
h3 {
    color: #e0e0e0 !important;
    font-weight: 600 !important;
    font-size: 1.15rem !important;
}
h4 { color: #e0e0e0 !important; margin-top: 1rem !important; }
h5 { color: #aaa !important; font-size: 0.85rem !important; font-weight: 600 !important;
     letter-spacing: 0.5px !important; margin-top: 1.2rem !important; margin-bottom: 0.5rem !important; }
h6 { color: #888 !important; margin-top: 0.8rem !important; }
p, span {
    color: #e0e0e0 !important;
}
/* Expander header — flex layout, prevent arrow/label overlap */
.streamlit-expanderHeader, [data-testid="stExpanderHeader"] {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    padding: 10px 14px !important;
    margin-top: 6px !important;
    background: #0d0d0d !important;
    border: 1px solid #1e1e1e !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #ddd !important;
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
    color: #999 !important;
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
a { color: #999 !important; }

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background: #0a0a0a !important;
    border-right: 1px solid #1a1a1a !important;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #999 !important;
}
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
    background: transparent !important;
    border: 1px solid #1a1a1a !important;
    border-radius: 8px !important;
    padding: 8px 14px !important;
    margin-bottom: 2px !important;
    transition: all 0.2s ease !important;
    color: #aaa !important;
    font-size: 13px !important;
}
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:hover {
    background: #111 !important;
    border-color: #333 !important;
    color: #fff !important;
}
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label[data-checked="true"] {
    background: #fff !important;
    border-color: #fff !important;
    color: #000 !important;
}
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label[data-checked="true"] p,
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label[data-checked="true"] span {
    color: #000 !important;
}

/* ===== BUTTONS ===== */
.stButton > button,
.stButton > button p,
.stButton > button span,
.stButton > button label {
    background: #fff !important;
    color: #111 !important;
    border: none !important;
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
    background: #e0e0e0 !important;
    transform: translateY(-1px);
}
.stButton > button:hover p,
.stButton > button:hover span,
.stButton > button:hover label {
    color: #111 !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
    background: #ccc !important;
}
.stDownloadButton > button {
    background: #fff !important;
    color: #000 !important;
    border: none !important;
    border-radius: 8px !important;
}

/* ===== INPUT FIELDS ===== */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background: #111 !important;
    border: 1px solid #222 !important;
    border-radius: 8px !important;
    color: #fff !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    transition: border-color 0.2s ease !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stNumberInput > div > div > input:focus {
    border-color: #555 !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: #444 !important;
}

/* Labels */
.stTextInput > label, .stTextArea > label,
.stNumberInput > label, .stSelectbox > label,
.stMultiSelect > label, .stRadio > label, .stSlider > label {
    color: #888 !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* ===== SELECT / MULTISELECT ===== */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: #111 !important;
    border: 1px solid #222 !important;
    border-radius: 8px !important;
    color: #fff !important;
}
[data-baseweb="select"] { background: transparent !important; }
[data-baseweb="tag"] {
    background: #fff !important;
    color: #000 !important;
    border-radius: 4px !important;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: transparent;
    border-bottom: 1px solid #1a1a1a;
    padding: 0;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 0 !important;
    padding: 10px 20px !important;
    color: #666 !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
    transition: all 0.2s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #fff !important;
}
.stTabs [aria-selected="true"] {
    color: #fff !important;
    border-bottom: 2px solid #fff !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ===== METRICS ===== */
[data-testid="stMetric"] {
    background: #0a0a0a !important;
    border: 1px solid #1a1a1a !important;
    border-radius: 12px !important;
    padding: 18px !important;
}
[data-testid="stMetricValue"] {
    color: #fff !important;
    font-weight: 800 !important;
    font-size: 26px !important;
}
[data-testid="stMetricLabel"] {
    color: #666 !important;
    font-weight: 500 !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* ===== EXPANDER wrapper ===== */
[data-testid="stExpander"] {
    background: #0a0a0a !important;
    border: 1px solid #1a1a1a !important;
    border-radius: 10px !important;
    overflow: visible !important;
}

/* ===== DATAFRAME ===== */
[data-testid="stDataFrame"] {
    border: 1px solid #1a1a1a !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ===== ALERTS ===== */
.stSuccess, [data-baseweb="notification"][kind="positive"] {
    background: #0a0a0a !important;
    border-left: 3px solid #fff !important;
    border-radius: 8px !important;
}
.stWarning, [data-baseweb="notification"][kind="warning"] {
    background: #0a0a0a !important;
    border-left: 3px solid #888 !important;
    border-radius: 8px !important;
}
.stError, [data-baseweb="notification"][kind="negative"] {
    background: #0a0a0a !important;
    border-left: 3px solid #666 !important;
    border-radius: 8px !important;
}
.stInfo, [data-baseweb="notification"][kind="info"] {
    background: #0a0a0a !important;
    border-left: 3px solid #444 !important;
    border-radius: 8px !important;
}

/* ===== DIVIDER ===== */
hr { border-color: #1a1a1a !important; }

/* ===== FORM ===== */
[data-testid="stForm"] {
    background: #0a0a0a !important;
    border: 1px solid #1a1a1a !important;
    border-radius: 12px !important;
    padding: 24px !important;
}

/* ===== FILE UPLOADER ===== */
[data-testid="stFileUploader"] {
    background: #0a0a0a !important;
    border: 1px dashed #222 !important;
    border-radius: 10px !important;
    padding: 16px !important;
}

/* ===== PROGRESS ===== */
.stProgress > div > div > div {
    background: #fff !important;
    border-radius: 4px !important;
}
.stProgress > div > div {
    background: #1a1a1a !important;
    border-radius: 4px !important;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #000; }
::-webkit-scrollbar-thumb { background: #222; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #333; }

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
.stCaption, [data-testid="stCaption"] { color: #444 !important; font-size: 11px !important; }

/* ===== SLIDER ===== */
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: #fff !important;
    border-color: #fff !important;
}

/* ===== TOOLTIP ===== */
[data-testid="stTooltipIcon"] { color: #444 !important; }

/* ===== CHECKBOX ===== */
.stCheckbox label span { color: #ccc !important; }

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
<div style="padding:10px 0 16px 0; border-bottom:1px solid #1a1a1a; margin-bottom:12px;">
    <p style="margin:0; color:#fff; font-size:18px; font-weight:800; letter-spacing:-0.5px;">
        💊 Smart Pharmacy
    </p>
    <p style="margin:2px 0 0 0; color:#444; font-size:11px; letter-spacing:1px; text-transform:uppercase;">
        AI Platform
    </p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"""
<div style="background:#111; border:1px solid #1a1a1a; border-radius:8px;
            padding:10px 14px; margin-bottom:12px;">
    <p style="margin:0; color:#555; font-size:10px; text-transform:uppercase; letter-spacing:1px;">
        Signed in as
    </p>
    <p style="margin:3px 0 0 0; color:#fff; font-weight:600; font-size:14px;">
        {st.session_state.username}
    </p>
    <p style="margin:2px 0 0 0; color:#666; font-size:11px; text-transform:uppercase; letter-spacing:0.5px;">
        {st.session_state.role}
    </p>
</div>
""", unsafe_allow_html=True)

role = st.session_state.role
menu_options = login.get_menu_options(role)

menu = st.sidebar.radio("Navigation", menu_options, label_visibility="collapsed")

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
<div style="background:#1a0000;border:1px solid #ff2d2d40;border-radius:8px;
            padding:10px 14px;margin-top:4px;margin-bottom:4px;display:flex;
            align-items:center;gap:10px;">
    <span style="font-size:18px;">🚨</span>
    <div>
        <p style="margin:0;color:#ff2d2d;font-weight:700;font-size:13px;">{_total_alerts} Active Alerts</p>
        <p style="margin:0;color:#555;font-size:11px;">{_n_crit} critical · {_n_miss} missed doses</p>
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
<p style="color:#333; font-size:10px; text-align:center; margin-top:20px;">
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