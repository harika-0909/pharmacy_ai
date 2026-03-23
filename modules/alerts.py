"""
Alerts Module
=============
Features:
  • Missed dose detection (time-window based + custom schedules)
  • Upcoming dose reminders (30-min look-ahead + custom schedules)
  • Low stock alerts  (critical ≤5 / warning ≤15) + one-click restock
  • Expiry date alerts (≤90 days / ≤30 days)
  • Pending order delay alerts
  • Alert acknowledgement (MongoDB-backed log)
  • Custom dose-time scheduler (caregiver)
  • WhatsApp mock reminder button
  • CSV export of active alerts
  • Auto-refresh countdown toggle
  • Animated pulse CSS for critical alerts
  • Sidebar live-badge integration
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time as _time

from modules.utils.db import (
    get_inventory, get_low_stock_items, get_all_prescriptions,
    seed_inventory, get_all_orders, get_orders_by_status,
    # New helpers
    log_alert, get_alert_log, acknowledge_alert, clear_acked_alerts,
    get_expiring_items, restock_item, set_inventory_expiry,
    save_dose_schedule, get_dose_schedules, get_all_dose_schedules,
)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
INVENTORY = {
    "Paracetamol": 50, "Ibuprofen": 10, "Aspirin": 5, "Naproxen": 25,
    "Diclofenac": 18, "Acetaminophen": 45, "Celecoxib": 12, "Meloxicam": 20,
    "Indomethacin": 15, "Ketorolac": 8,
    "Amoxicillin": 20, "Azithromycin": 30, "Ciprofloxacin": 22, "Doxycycline": 28,
    "Metronidazole": 35, "Clindamycin": 16, "Erythromycin": 24, "Penicillin": 12,
    "Tetracycline": 18, "Vancomycin": 6, "Gentamicin": 14, "Levofloxacin": 19,
    "Vitamin C": 30, "Vitamin D3": 40, "Vitamin B12": 35, "Multivitamin": 55,
    "Insulin": 15, "Metformin": 45, "Glipizide": 28,
    "Amlodipine": 38, "Lisinopril": 42, "Losartan": 35, "Metoprolol": 29,
    "Atorvastatin": 48, "Simvastatin": 33, "Warfarin": 11,
    "Albuterol": 44, "Salbutamol": 39, "Fluticasone": 25,
    "Omeprazole": 52, "Pantoprazole": 46, "Ranitidine": 29,
    "Loratadine": 47, "Cetirizine": 43, "Diphenhydramine": 39,
    "Sertraline": 23, "Escitalopram": 19, "Fluoxetine": 26, "Gabapentin": 34,
}

LOW_STOCK_THRESHOLD  = 15
CRITICAL_THRESHOLD   = 5
EXPIRY_WARN_DAYS     = 90
EXPIRY_CRIT_DAYS     = 30

DOSE_WINDOWS = [
    ("morning",   6,  10,  "🌅 Morning",   "6–10 AM"),
    ("afternoon", 12, 15,  "☀️ Afternoon", "12–3 PM"),
    ("evening",   18, 21,  "🌙 Evening",   "6–9 PM"),
    ("night",     21, 24,  "🌑 Night",     "9 PM–midnight"),
]

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
ALERT_CSS = """
<style>
@keyframes pulse-red {
  0%,100% { box-shadow: 0 0 0 0 rgba(255,45,45,.4); }
  50%      { box-shadow: 0 0 0 8px rgba(255,45,45,0); }
}
.alert-card {
    display:flex; align-items:flex-start; gap:14px;
    padding:14px 18px; border-radius:10px; margin-bottom:10px;
    border:1px solid transparent; transition:transform .15s ease;
}
.alert-card:hover { transform:translateX(3px); }
.alert-critical {
    background:linear-gradient(135deg,#1a0000,#0d0000);
    border-color:#ff2d2d !important;
    animation: pulse-red 2.4s infinite;
}
.alert-warning {
    background:linear-gradient(135deg,#1a1000,#0d0900);
    border-color:#ffaa00 !important;
    box-shadow:0 0 16px rgba(255,170,0,.12);
}
.alert-info {
    background:linear-gradient(135deg,#00101a,#00090d);
    border-color:#00aaff !important;
    box-shadow:0 0 16px rgba(0,170,255,.12);
}
.alert-high {
    background:linear-gradient(135deg,#150010,#0d0008);
    border-color:#cc44ff !important;
    box-shadow:0 0 16px rgba(200,68,255,.15);
}
.alert-success {
    background:linear-gradient(135deg,#001a05,#000d02);
    border-color:#00cc44 !important;
    box-shadow:0 0 12px rgba(0,204,68,.1);
}
.alert-icon {
    width:40px;height:40px;border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    font-size:18px;flex-shrink:0;
}
.icon-critical { background:rgba(255,45,45,.18); }
.icon-warning  { background:rgba(255,170,0,.18); }
.icon-info     { background:rgba(0,170,255,.18); }
.icon-high     { background:rgba(200,68,255,.18); }
.icon-success  { background:rgba(0,204,68,.18); }
.alert-body  { flex:1; }
.alert-msg   { color:#fff;font-weight:600;font-size:14px;margin:0 0 3px; }
.alert-act   { color:#888;font-size:12px;margin:0; }
.alert-badge {
    display:inline-block; padding:2px 10px; border-radius:20px;
    font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.7px;
    flex-shrink:0;align-self:flex-start;margin-top:2px;
}
.badge-critical { background:#ff2d2d20;color:#ff2d2d;border:1px solid #ff2d2d40; }
.badge-warning  { background:#ffaa0020;color:#ffaa00;border:1px solid #ffaa0040; }
.badge-info     { background:#00aaff20;color:#00aaff;border:1px solid #00aaff40; }
.badge-high     { background:#cc44ff20;color:#cc44ff;border:1px solid #cc44ff40; }
.badge-success  { background:#00cc4420;color:#00cc44;border:1px solid #00cc4440; }

.summary-strip {
    display:grid;grid-template-columns:repeat(5,1fr);
    gap:12px;margin-bottom:24px;
}
.summary-card {
    background:#0a0a0a;border:1px solid #1a1a1a;border-radius:12px;
    padding:16px;text-align:center;
}
.summary-count { font-size:26px;font-weight:800;margin:0; }
.summary-label { color:#555;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin:4px 0 0; }
.count-critical{ color:#ff2d2d !important; }
.count-warning { color:#ffaa00 !important; }
.count-info    { color:#00aaff !important; }
.count-high    { color:#cc44ff !important; }
.count-success { color:#00cc44 !important; }

.section-hdr {
    display:flex;align-items:center;gap:10px;
    margin:24px 0 12px;padding-bottom:8px;border-bottom:1px solid #1a1a1a;
}
.section-hdr-title { font-size:15px;font-weight:700;color:#fff;margin:0; }
.section-hdr-count {
    background:#1a1a1a;color:#aaa;border-radius:20px;
    padding:1px 10px;font-size:11px;font-weight:600;
}

.empty-state   { text-align:center;padding:40px 20px;color:#444; }
.empty-icon    { font-size:36px;margin-bottom:8px; }
.empty-text    { font-size:14px; }

.ack-log-row {
    display:flex;gap:10px;align-items:center;
    padding:8px 12px;border-radius:8px;margin-bottom:6px;background:#0a0a0a;
    border:1px solid #1a1a1a;
}
.ack-log-msg  { flex:1;color:#ccc;font-size:13px; }
.ack-log-meta { color:#444;font-size:11px;flex-shrink:0; }

.refresh-bar {
    display:flex;align-items:center;gap:8px;
    padding:6px 14px;background:#0a0a0a;border:1px solid #1a1a1a;
    border-radius:8px;margin-bottom:16px;
}
.refresh-dot { width:8px;height:8px;border-radius:50%;background:#00cc44;
               animation:pulse-red 1.5s infinite; margin-right:4px; }

@media(max-width:600px){
    .summary-strip{grid-template-columns:repeat(2,1fr);}
}
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Data-layer helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_low_stock_alerts():
    seed_inventory(INVENTORY)
    alerts = []
    for item in get_low_stock_items(LOW_STOCK_THRESHOLD):
        name  = item.get("medicine_name", "Unknown")
        stock = item.get("stock", 0)
        sev   = "critical" if stock <= CRITICAL_THRESHOLD else "warning"
        alerts.append({
            "type": "low_stock", "severity": sev,
            "medicine": name, "stock": stock,
            "message": f"{name} — {stock} units remaining",
            "action":  "Restock immediately" if sev == "critical" else "Plan reorder",
        })
    return alerts


def get_expiry_alerts():
    """Items expiring within 90 days (from DB expiry_date field)."""
    alerts = []
    try:
        for item in get_expiring_items(EXPIRY_WARN_DAYS):
            name   = item.get("medicine_name", "Unknown")
            exp    = item.get("expiry_date")
            if exp is None:
                continue
            days_left = (exp - datetime.utcnow()).days
            sev = "critical" if days_left <= EXPIRY_CRIT_DAYS else "warning"
            alerts.append({
                "type": "expiry", "severity": sev,
                "medicine": name, "days_left": days_left,
                "expiry_date": exp.strftime("%Y-%m-%d") if hasattr(exp, "strftime") else str(exp),
                "message": f"{name} — expires in {days_left} days ({exp.strftime('%d %b %Y') if hasattr(exp,'strftime') else str(exp)})",
                "action":  "Remove / quarantine immediately" if sev == "critical" else "Plan replacement",
            })
    except Exception:
        pass
    return alerts


def _get_custom_schedule_missed(caregiver_name=None):
    """Alerts from custom dose schedules stored in MongoDB."""
    alerts = []
    try:
        now  = datetime.now()
        if caregiver_name:
            schedules = get_dose_schedules(caregiver_name)
        else:
            schedules = get_all_dose_schedules()

        for sched in schedules:
            patient  = sched.get("patient", "Unknown")
            medicine = sched.get("medicine", "Unknown")
            caregiver = sched.get("caregiver", "")
            for t_str in sched.get("times", []):
                try:
                    h, m = map(int, t_str.split(":"))
                    due_today = now.replace(hour=h, minute=m, second=0, microsecond=0)
                    overdue_minutes = (now - due_today).total_seconds() / 60
                    if 5 < overdue_minutes <= 120:        # 5 min grace, max 2 h
                        alerts.append({
                            "type": "missed_dose", "severity": "high",
                            "patient":   patient,
                            "caregiver": caregiver,
                            "medicine":  medicine,
                            "window":    f"⏰ {t_str}",
                            "message":   f"{patient} — {medicine} (due {t_str}, {int(overdue_minutes)}m overdue)",
                            "action":    "Administer dose now and log in system",
                        })
                    elif -30 <= overdue_minutes <= 5:     # upcoming
                        alerts.append({
                            "type": "reminder", "severity": "info",
                            "patient":   patient,
                            "caregiver": caregiver,
                            "medicine":  medicine,
                            "window":    f"⏰ {t_str}",
                            "time_range": t_str,
                            "message":   f"{patient} — {medicine} due at {t_str}",
                            "action":    "Prepare dose",
                        })
                except Exception:
                    pass
    except Exception:
        pass
    return alerts


def get_missed_dose_alerts():
    now  = datetime.now()
    hour = now.hour
    alerts = []
    try:
        for presc in get_all_prescriptions()[:40]:
            medicines = presc.get("medicines", "")
            patient   = presc.get("patient_name", "Unknown")
            caregiver = presc.get("caregiver", "")
            presc_id  = presc.get("prescription_id", "")
            if not medicines:
                continue
            for med_raw in medicines.split(","):
                med = med_raw.strip()
                if not med:
                    continue
                for label_key, start_h, end_h, emoji_label, time_range in DOSE_WINDOWS:
                    if label_key in med.lower() and hour >= end_h:
                        alerts.append({
                            "type": "missed_dose", "severity": "high",
                            "patient": patient, "caregiver": caregiver,
                            "medicine": med, "window": emoji_label,
                            "presc_id": presc_id,
                            "message":  f"{patient} — {med} ({emoji_label} dose)",
                            "action":   "Notify caregiver / administer now",
                        })
    except Exception:
        pass
    alerts += _get_custom_schedule_missed()
    return alerts


def get_reminder_alerts():
    now  = datetime.now()
    hour = now.hour
    alerts = []
    try:
        for presc in get_all_prescriptions()[:40]:
            medicines = presc.get("medicines", "")
            patient   = presc.get("patient_name", "Unknown")
            caregiver = presc.get("caregiver", "")
            if not medicines:
                continue
            for med_raw in medicines.split(","):
                med = med_raw.strip()
                if not med:
                    continue
                for label_key, start_h, end_h, emoji_label, time_range in DOSE_WINDOWS:
                    if label_key in med.lower() and start_h - 1 <= hour < start_h:
                        alerts.append({
                            "type": "reminder", "severity": "info",
                            "patient": patient, "caregiver": caregiver,
                            "medicine": med, "window": emoji_label,
                            "time_range": time_range,
                            "message":   f"{patient} — {med} due {emoji_label} ({time_range})",
                            "action":    "Prepare dose",
                        })
    except Exception:
        pass
    return alerts


def get_pending_order_alerts():
    alerts = []
    try:
        now = datetime.utcnow()
        for order in get_orders_by_status("pending"):
            created = order.get("created_at")
            if not created:
                continue
            age_h = (now - created).total_seconds() / 3600
            if age_h >= 2:
                alerts.append({
                    "type": "pending_order",
                    "severity": "critical" if age_h >= 6 else "warning",
                    "patient":  order.get("patient_name", "Unknown"),
                    "presc_id": order.get("prescription_id", ""),
                    "age_h":    round(age_h, 1),
                    "message":  f"{order.get('patient_name','?')} — Rx {order.get('prescription_id','')} pending {round(age_h,1)}h",
                    "action":   "Process immediately" if age_h >= 6 else "Follow up soon",
                })
    except Exception:
        pass
    return alerts


def get_all_alerts():
    seed_inventory(INVENTORY)
    return {
        "low_stock":      get_low_stock_alerts(),
        "missed_dose":    get_missed_dose_alerts(),
        "reminders":      get_reminder_alerts(),
        "pending_orders": get_pending_order_alerts(),
        "expiry":         get_expiry_alerts(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# UI helpers
# ─────────────────────────────────────────────────────────────────────────────

def _render_card(msg: str, action: str, severity: str, icon: str, alert_id: str = None, show_ack: bool = False):
    sev = severity.lower()
    ack_html = ""
    st.markdown(f"""
<div class="alert-card alert-{sev}">
    <div class="alert-icon icon-{sev}">{icon}</div>
    <div class="alert-body">
        <p class="alert-msg">{msg}</p>
        <p class="alert-act">↪ {action}</p>
    </div>
    <span class="alert-badge badge-{sev}">{sev}</span>
</div>""", unsafe_allow_html=True)

    if show_ack and alert_id:
        if st.button("✓ Acknowledge", key=f"ack_{alert_id}", help="Mark as handled"):
            username = st.session_state.get("username", "system")
            acknowledge_alert(alert_id, username)
            st.success("Acknowledged ✓")
            st.rerun()


def _section_hdr(title: str, count: int, icon: str):
    c_html = f'<span class="section-hdr-count">{count}</span>' if count else ""
    st.markdown(f"""
<div class="section-hdr">
    <span style="font-size:18px">{icon}</span>
    <p class="section-hdr-title">{title}</p>
    {c_html}
</div>""", unsafe_allow_html=True)


def _empty(msg="Nothing to show right now."):
    st.markdown(f"""
<div class="empty-state">
    <div class="empty-icon">✅</div>
    <div class="empty-text">{msg}</div>
</div>""", unsafe_allow_html=True)


def _whatsapp_button(patient: str, medicine: str, window: str):
    """Mock WhatsApp reminder trigger."""
    if st.button(f"📲 WhatsApp Reminder", key=f"wa_{patient}_{medicine}_{window}"):
        msg = (
            f"🔔 *Medicine Reminder — Smart Pharmacy AI*\n\n"
            f"Dear Caregiver,\n\n"
            f"👤 Patient: *{patient}*\n"
            f"💊 Medicine: *{medicine}*\n"
            f"⏰ Dose window: *{window}*\n\n"
            f"Please administer the dose as prescribed.\n\n"
            f"_Smart Pharmacy AI_"
        )
        st.info(f"📲 WhatsApp would send:\n\n{msg}")


def _export_csv(alerts_flat: list):
    if not alerts_flat:
        return
    df = pd.DataFrame(alerts_flat)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Export Alerts CSV",
        data=csv,
        file_name=f"alerts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        key="export_csv_btn"
    )


def _auto_refresh_widget():
    """Toggle auto-refresh every 60 s."""
    col1, col2 = st.columns([1, 5])
    with col1:
        auto = st.checkbox("Auto-refresh", value=False, key="auto_refresh_chk")
    if auto:
        countdown = st.empty()
        for i in range(60, 0, -1):
            countdown.markdown(
                f'<div class="refresh-bar"><div class="refresh-dot"></div>'
                f'<span style="color:#555;font-size:12px;">Refreshing in {i}s…</span></div>',
                unsafe_allow_html=True
            )
            _time.sleep(1)
            if not st.session_state.get("auto_refresh_chk", False):
                break
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Main alerts page (full)
# ─────────────────────────────────────────────────────────────────────────────

def show_alerts():
    st.markdown(ALERT_CSS, unsafe_allow_html=True)

    role     = st.session_state.get("role", "admin")
    username = st.session_state.get("username", "user")

    # Header
    st.markdown("""
<div style="margin-bottom:8px;">
    <h1 style="margin:0;">🚨 Alerts &amp; Reminders</h1>
    <p style="color:#555;font-size:13px;margin:4px 0 0;">
        Real-time medication alerts · Low stock · Expiry · Dose reminders · Order delays
    </p>
</div>""", unsafe_allow_html=True)

    # Auto-refresh
    _auto_refresh_widget()

    data = get_all_alerts()
    ls   = data["low_stock"]
    md   = data["missed_dose"]
    rem  = data["reminders"]
    po   = data["pending_orders"]
    exp  = data["expiry"]

    crit_ls  = [a for a in ls  if a["severity"] == "critical"]
    warn_ls  = [a for a in ls  if a["severity"] == "warning"]
    crit_exp = [a for a in exp if a["severity"] == "critical"]
    warn_exp = [a for a in exp if a["severity"] == "warning"]

    total = len(ls) + len(md) + len(rem) + len(po) + len(exp)

    # Summary strip
    st.markdown(f"""
<div class="summary-strip">
    <div class="summary-card">
        <p class="summary-count count-critical">{len(crit_ls) + len(crit_exp)}</p>
        <p class="summary-label">Critical</p>
    </div>
    <div class="summary-card">
        <p class="summary-count count-warning">{len(warn_ls) + len(po) + len(warn_exp)}</p>
        <p class="summary-label">Warnings</p>
    </div>
    <div class="summary-card">
        <p class="summary-count count-high">{len(md)}</p>
        <p class="summary-label">Missed Doses</p>
    </div>
    <div class="summary-card">
        <p class="summary-count count-info">{len(rem)}</p>
        <p class="summary-label">Upcoming Doses</p>
    </div>
    <div class="summary-card">
        <p class="summary-count count-warning">{len(exp)}</p>
        <p class="summary-label">Near Expiry</p>
    </div>
</div>""", unsafe_allow_html=True)

    if total == 0:
        _empty("All clear — no active alerts right now.")
    else:
        # Export button (flat list)
        flat = [{
            "type": a["type"], "severity": a.get("severity",""),
            "message": a.get("message",""), "action": a.get("action",""),
        } for al_list in data.values() for a in al_list]
        _export_csv(flat)

    # --- Build tabs by role ---
    if role == "caregiver":
        tab_labels = ["💊 Missed Doses", "🔔 Reminders", "📅 Dose Scheduler"]
        tabs = st.tabs(tab_labels)
        _tab_missed_doses(tabs[0], md, show_wa=True)
        _tab_reminders(tabs[1], rem)
        _tab_dose_scheduler(tabs[2], username, role)

    elif role == "pharmacy":
        tab_labels = ["📦 Low Stock", "⏳ Pending Orders", "🗓️ Expiry", "📋 Alert Log"]
        tabs = st.tabs(tab_labels)
        _tab_low_stock(tabs[0], ls, username)
        _tab_pending_orders(tabs[1], po)
        _tab_expiry(tabs[2], exp, username)
        _tab_alert_log(tabs[3], username)

    else:  # admin / doctor / default — all tabs
        tab_labels = ["💊 Missed Doses", "📦 Low Stock", "⏳ Pending Orders",
                      "🗓️ Expiry", "🔔 Reminders", "📅 Dose Scheduler", "📋 Alert Log"]
        tabs = st.tabs(tab_labels)
        _tab_missed_doses(tabs[0], md, show_wa=True)
        _tab_low_stock(tabs[1], ls, username)
        _tab_pending_orders(tabs[2], po)
        _tab_expiry(tabs[3], exp, username)
        _tab_reminders(tabs[4], rem)
        _tab_dose_scheduler(tabs[5], username, role)
        _tab_alert_log(tabs[6], username)


# ─────────────────────────────────────────────────────────────────────────────
# Individual tab renderers
# ─────────────────────────────────────────────────────────────────────────────

def _tab_missed_doses(tab, md: list, show_wa: bool = False):
    with tab:
        if not md:
            _empty("No missed doses detected right now.")
            return
        _section_hdr("Missed Dose Alerts", len(md), "💊")
        # Log to DB
        for a in md:
            log_alert("missed_dose", a["message"], "high", {"patient": a["patient"], "medicine": a["medicine"]})
            _render_card(
                f"<b>{a['patient']}</b> — {a['medicine']} · {a.get('window','')}",
                a["action"], "high", "💊"
            )
            if show_wa:
                _whatsapp_button(a["patient"], a["medicine"], a.get("window", ""))
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)


def _tab_reminders(tab, rem: list):
    with tab:
        if not rem:
            _empty("No upcoming doses in the next hour.")
            return
        _section_hdr("Upcoming Dose Reminders", len(rem), "🔔")
        for a in rem:
            _render_card(
                f"<b>{a['patient']}</b> — {a['medicine']} · {a.get('time_range','')}",
                a["action"], "info", "🔔"
            )


def _tab_low_stock(tab, ls: list, username: str):
    with tab:
        if not ls:
            _empty("All medicines are well-stocked.")
            return

        crit = [a for a in ls if a["severity"] == "critical"]
        warn = [a for a in ls if a["severity"] == "warning"]

        if crit:
            log_alert("low_stock_critical", f"{len(crit)} critical stock items", "critical")
            _section_hdr("Critical — Needs Immediate Restock", len(crit), "🔴")
            for a in crit:
                _render_card(
                    f"<b>{a['medicine']}</b> — {a['stock']} units left",
                    a["action"], "critical", "🚨"
                )
                # One-click restock
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    qty = st.number_input(
                        "Units to add", min_value=1, max_value=1000, value=50,
                        key=f"restock_qty_{a['medicine']}"
                    )
                with col2:
                    st.write("")
                    if st.button("📦 Restock Now", key=f"restock_{a['medicine']}"):
                        ok = restock_item(a["medicine"], qty, username)
                        if ok:
                            st.success(f"✅ Restocked {a['medicine']} +{qty} units")
                            st.rerun()
                        else:
                            st.error("Restock failed — item not found in inventory.")
                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        if warn:
            _section_hdr("Warning — Low Stock", len(warn), "🟡")
            for a in warn:
                _render_card(
                    f"<b>{a['medicine']}</b> — {a['stock']} units left",
                    a["action"], "warning", "⚠️"
                )
                col1, col2 = st.columns([2, 1])
                with col1:
                    qty = st.number_input(
                        "Units to add", min_value=1, value=30,
                        key=f"restock_qty_{a['medicine']}"
                    )
                with col2:
                    st.write("")
                    if st.button("📦 Restock", key=f"restock_{a['medicine']}"):
                        restock_item(a["medicine"], qty, username)
                        st.success(f"✅ Restocked +{qty}")
                        st.rerun()

        # Summary table
        st.markdown("---")
        df = pd.DataFrame([{
            "Medicine": a["medicine"], "Stock": a["stock"],
            "Severity": a["severity"].upper(), "Action": a["action"],
        } for a in ls])
        st.dataframe(df, use_container_width=True, hide_index=True)


def _tab_pending_orders(tab, po: list):
    with tab:
        if not po:
            _empty("No delayed pending orders.")
            return
        _section_hdr("Orders Awaiting Processing", len(po), "⏳")
        for a in po:
            _render_card(
                f"<b>{a['patient']}</b> · Rx {a['presc_id']} — pending {a['age_h']}h",
                a["action"], a["severity"], "📦"
            )


def _tab_expiry(tab, exp: list, username: str):
    with tab:
        _section_hdr("Expiry Date Tracker", len(exp), "🗓️")

        # Set expiry dates form
        with st.expander("➕ Set / Update Expiry Date for an Item", expanded=not exp):
            cols = st.columns([2, 1, 1])
            inventory = get_inventory()
            med_names = [i["medicine_name"] for i in inventory]
            with cols[0]:
                med_sel = st.selectbox("Medicine", med_names, key="expiry_med_sel")
            with cols[1]:
                exp_date = st.date_input("Expiry Date", key="expiry_date_sel")
            with cols[2]:
                st.write("")
                if st.button("Save Expiry", key="save_expiry_btn"):
                    set_inventory_expiry(med_sel, datetime.combine(exp_date, datetime.min.time()))
                    st.success(f"Expiry set for {med_sel}: {exp_date}")
                    st.rerun()

        if not exp:
            _empty("No items nearing expiry.")
            return

        crit = [a for a in exp if a["severity"] == "critical"]
        warn = [a for a in exp if a["severity"] == "warning"]

        if crit:
            _section_hdr(f"Expiring ≤ {EXPIRY_CRIT_DAYS} Days", len(crit), "🔴")
            for a in crit:
                _render_card(a["message"], a["action"], "critical", "⛔")

        if warn:
            _section_hdr(f"Expiring ≤ {EXPIRY_WARN_DAYS} Days", len(warn), "🟡")
            for a in warn:
                _render_card(a["message"], a["action"], "warning", "📅")

        df = pd.DataFrame([{
            "Medicine": a["medicine"], "Expires": a["expiry_date"],
            "Days Left": a["days_left"], "Severity": a["severity"].upper(),
        } for a in exp])
        st.dataframe(df, use_container_width=True, hide_index=True)


def _tab_dose_scheduler(tab, username: str, role: str):
    """Custom per-patient dose time scheduling."""
    with tab:
        st.markdown("""
<div style="margin-bottom:12px;">
    <p style="color:#888;font-size:13px;margin:0;">
        Schedule exact dose times per patient · Alerts fire 30 min before and flag missed doses up to 2h after
    </p>
</div>""", unsafe_allow_html=True)

        # Get prescription list for caregiver
        try:
            from modules.utils.db import get_prescriptions_by_caregiver, get_all_prescriptions
            if role == "caregiver":
                prescriptions = get_prescriptions_by_caregiver(username)
            else:
                prescriptions = get_all_prescriptions()[:50]
        except Exception:
            prescriptions = []

        patients  = sorted({p.get("patient_name","") for p in prescriptions if p.get("patient_name")})
        med_map   = {}
        for p in prescriptions:
            nm = p.get("patient_name","")
            meds = [m.strip() for m in p.get("medicines","").split(",") if m.strip()]
            if nm:
                med_map.setdefault(nm, set()).update(meds)

        with st.expander("➕ Add / Update Dose Schedule", expanded=True):
            with st.form("dose_sched_form"):
                col1, col2 = st.columns(2)
                with col1:
                    pat_sel  = st.selectbox("Patient", patients if patients else ["— no patients —"], key="ds_patient")
                    meds_for = sorted(med_map.get(pat_sel, []))
                    med_sel  = st.selectbox("Medicine", meds_for if meds_for else ["— no medicines —"], key="ds_medicine")
                with col2:
                    t1 = st.text_input("Dose Time 1 (HH:MM)", placeholder="08:00", key="ds_t1")
                    t2 = st.text_input("Dose Time 2 (HH:MM)", placeholder="14:00", key="ds_t2")
                    t3 = st.text_input("Dose Time 3 (HH:MM)", placeholder="20:00", key="ds_t3")

                if st.form_submit_button("💾 Save Schedule", use_container_width=True):
                    times = [t for t in [t1.strip(), t2.strip(), t3.strip()] if t]
                    if pat_sel and med_sel and times:
                        save_dose_schedule(username, pat_sel, med_sel, times)
                        st.success(f"Schedule saved for {pat_sel} · {med_sel}: {', '.join(times)}")
                        st.rerun()
                    else:
                        st.error("Fill in patient, medicine, and at least one time.")

        # Show existing schedules
        try:
            if role == "caregiver":
                schedules = get_dose_schedules(username)
            else:
                schedules = get_all_dose_schedules()
        except Exception:
            schedules = []

        if schedules:
            _section_hdr("Active Dose Schedules", len(schedules), "📅")
            rows = [{"Patient": s["patient"], "Medicine": s["medicine"],
                     "Times": " · ".join(s.get("times", [])),
                     "Caregiver": s.get("caregiver","")} for s in schedules]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            _empty("No dose schedules set up yet.")


def _tab_alert_log(tab, username: str):
    """MongoDB-backed alert history with acknowledge/clear controls."""
    with tab:
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            show_all = st.checkbox("Show acknowledged", value=False, key="log_show_all")
        with col2:
            if st.button("🗑️ Clear Acknowledged", key="clear_acked_btn"):
                clear_acked_alerts()
                st.success("Cleared.")
                st.rerun()

        logs = get_alert_log(limit=100, only_unacked=not show_all)

        if not logs:
            _empty("No alert log entries yet." if show_all else "No unacknowledged alerts in log.")
            return

        _section_hdr("Alert History", len(logs), "📋")

        sev_icons = {"critical": "🔴", "warning": "🟡", "info": "🔵", "high": "🟣", "success": "🟢"}

        for entry in logs:
            eid     = str(entry.get("_id",""))
            sev     = entry.get("severity","info")
            msg     = entry.get("message","")
            acked   = entry.get("acknowledged", False)
            ack_by  = entry.get("ack_by","")
            created = str(entry.get("created_at",""))[:16]
            icon    = sev_icons.get(sev, "⚪")

            with st.container():
                c1, c2 = st.columns([6, 1])
                with c1:
                    acked_badge = f'<span style="color:#00cc44;font-size:11px;"> ✓ {ack_by}</span>' if acked else ""
                    st.markdown(f"""
<div class="ack-log-row">
    <span style="font-size:16px">{icon}</span>
    <div class="ack-log-msg">{msg}{acked_badge}</div>
    <span class="ack-log-meta">{created}</span>
</div>""", unsafe_allow_html=True)
                with c2:
                    if not acked:
                        if st.button("✓", key=f"ack_{eid}", help="Acknowledge"):
                            acknowledge_alert(eid, username)
                            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Embedded panels (called from other modules)
# ─────────────────────────────────────────────────────────────────────────────

def show_caregiver_alerts(caregiver_name: str):
    """Inline caregiver alert panel — used inside caregiver.py."""
    st.markdown(ALERT_CSS, unsafe_allow_html=True)

    try:
        from modules.utils.db import get_prescriptions_by_caregiver
        prescriptions = get_prescriptions_by_caregiver(caregiver_name)
    except Exception:
        prescriptions = []

    patient_names = {p.get("patient_name","").lower() for p in prescriptions}
    all_md  = [a for a in get_missed_dose_alerts()
               if a.get("patient","").lower() in patient_names
               or a.get("caregiver","").lower() == caregiver_name.lower()]
    all_rem = [a for a in get_reminder_alerts()
               if a.get("patient","").lower() in patient_names
               or a.get("caregiver","").lower() == caregiver_name.lower()]
    custom  = _get_custom_schedule_missed(caregiver_name)
    all_md  = all_md + [a for a in custom if a["type"] == "missed_dose"]
    all_rem = all_rem + [a for a in custom if a["type"] == "reminder"]

    total = len(all_md) + len(all_rem)
    if total == 0:
        _empty("No alerts for your patients right now.")
        return

    col1, col2 = st.columns(2)
    col1.metric("💊 Missed Doses", len(all_md))
    col2.metric("🔔 Upcoming Reminders", len(all_rem))

    tabs = st.tabs(["💊 Missed Doses", "🔔 Upcoming", "📅 Schedule"])
    with tabs[0]:
        if not all_md:
            _empty()
        for a in all_md:
            _render_card(
                f"<b>{a['patient']}</b> — {a['medicine']} · {a.get('window','')}",
                a["action"], "high", "💊"
            )
            _whatsapp_button(a["patient"], a["medicine"], a.get("window",""))
    with tabs[1]:
        if not all_rem:
            _empty("No upcoming doses.")
        for a in all_rem:
            _render_card(
                f"<b>{a['patient']}</b> — {a['medicine']} · {a.get('time_range','')}",
                a["action"], "info", "🔔"
            )
    with tabs[2]:
        _tab_dose_scheduler(st, caregiver_name, "caregiver")


def show_pharmacy_alerts():
    """Inline pharmacy alert panel — used inside pharmacy.py."""
    st.markdown(ALERT_CSS, unsafe_allow_html=True)
    seed_inventory(INVENTORY)

    username = st.session_state.get("username", "pharmacy")
    ls  = get_low_stock_alerts()
    po  = get_pending_order_alerts()
    exp = get_expiry_alerts()

    crit = [a for a in ls if a["severity"] == "critical"]
    warn = [a for a in ls if a["severity"] == "warning"]
    total = len(ls) + len(po) + len(exp)

    if total == 0:
        _empty("All inventory healthy · No delayed orders · No near-expiry items.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔴 Critical Stock", len(crit))
    col2.metric("🟡 Low Stock",      len(warn))
    col3.metric("⏳ Delayed Orders", len(po))
    col4.metric("🗓️ Near Expiry",    len(exp))

    tabs = st.tabs(["📦 Stock", "🗓️ Expiry", "⏳ Orders"])
    _tab_low_stock(tabs[0], ls, username)
    _tab_expiry(tabs[1], exp, username)
    _tab_pending_orders(tabs[2], po)


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard mini-widget (called from dashboard.py)
# ─────────────────────────────────────────────────────────────────────────────

def show_dashboard_widget():
    """Compact alert summary for the main dashboard."""
    st.markdown(ALERT_CSS, unsafe_allow_html=True)
    try:
        seed_inventory(INVENTORY)
        ls  = get_low_stock_alerts()
        md  = get_missed_dose_alerts()
        po  = get_pending_order_alerts()
        exp = get_expiry_alerts()
        total = len(ls) + len(md) + len(po) + len(exp)
        if total == 0:
            return

        crit = len([a for a in ls if a["severity"]=="critical"]) + \
               len([a for a in exp if a["severity"]=="critical"])

        st.markdown(f"""
<div style="background:{'#1a0000' if crit else '#0a0a0a'};
            border:1px solid {'#ff2d2d' if crit else '#1a1a1a'};
            border-radius:10px;padding:14px 18px;margin-bottom:16px;
            display:flex;gap:16px;flex-wrap:wrap;align-items:center;">
    <span style="font-size:22px">{'🚨' if crit else '⚠️'}</span>
    <div style="flex:1">
        <p style="color:{'#ff2d2d' if crit else '#ffaa00'};font-weight:700;font-size:14px;margin:0">
            {total} Active Alert{'s' if total!=1 else ''}
        </p>
        <p style="color:#555;font-size:12px;margin:2px 0 0">
            {'Critical: ' + str(crit) + ' · ' if crit else ''}
            Low stock: {len(ls)} · Missed doses: {len(md)} · Orders: {len(po)} · Expiry: {len(exp)}
        </p>
    </div>
    <span style="color:#444;font-size:12px">→ Go to 🚨 Alerts</span>
</div>""", unsafe_allow_html=True)
    except Exception:
        pass