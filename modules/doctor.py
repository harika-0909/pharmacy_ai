"""
Doctor Module — Premium Rebuild
Tabs: New Prescription · My Prescriptions · Patient Lookup
"""
import streamlit as st
import uuid
import json
from datetime import datetime

from modules.utils.qr_generator import generate_qr
from modules.utils.interaction_checker import check_interactions
from modules.utils.db import (
    insert_prescription, create_order,
    get_all_patients, get_patient_by_name, create_patient,
    add_medication_to_patient, get_all_medicines,
    get_prescriptions_by_doctor, get_all_prescriptions,
    get_order_by_prescription
)
from modules.utils.cloudinary_config import upload_qr_code, is_configured as cloudinary_configured

# ─────────────────── CSS ───────────────────
DOCTOR_CSS = """
<style>
/* Medicine chip */
.med-chip {
    display:inline-flex; align-items:center; gap:6px;
    background:#111; border:1px solid #222; border-radius:8px;
    padding:6px 12px; margin:4px; font-size:13px; color:#e0e0e0;
}
.med-chip-cat  { color:#555; font-size:11px; }
.med-chip-warn { border-color:#ffaa00; background:#120e00; }

/* Interaction banner */
.interaction-banner {
    background:#1a1000; border:1px solid #ffaa0050;
    border-left:3px solid #ffaa00; border-radius:8px;
    padding:10px 14px; margin:8px 0;
    display:flex; gap:10px; align-items:flex-start;
}

/* Rx result card */
.rx-result {
    background:#050505; border:1px solid #1a1a1a; border-radius:12px;
    padding:20px; margin-top:16px;
}
.rx-result-id {
    font-size:22px; font-weight:900; color:#fff;
    letter-spacing:-1px; margin-bottom:16px; display:block;
}
.success-pulse {
    background:#001a05; border:1px solid #00cc4430;
    border-left:3px solid #00cc44; border-radius:8px;
    padding:12px 16px; font-size:14px; color:#00cc44;
    font-weight:600; margin-bottom:12px;
}

/* Prescription history item */
.rx-hist-item {
    display:flex; gap:12px; align-items:flex-start;
    padding:12px 0; border-bottom:1px solid #0f0f0f;
}
.rx-hist-id   { color:#fff; font-weight:700; font-size:13px; min-width:90px; }
.rx-hist-body { flex:1; color:#888; font-size:12px; }
.rx-hist-date { color:#333; font-size:11px; flex-shrink:0; }

/* Patient card */
.pat-mini {
    background:#0a0a0a; border:1px solid #1a1a1a; border-radius:10px;
    padding:14px; margin-bottom:8px;
}
</style>
"""


def _status_pill(status: str) -> str:
    colors = {"pending":"#ffaa00","processing":"#00aaff","dispensed":"#cc44ff",
              "completed":"#00cc44","cancelled":"#ff4444"}
    c = colors.get(status, "#555")
    return (f'<span style="background:{c}20;color:{c};border:1px solid {c}40;'
            f'padding:2px 10px;border-radius:20px;font-size:11px;font-weight:700;'
            f'text-transform:uppercase;">{status}</span>')


def show():
    st.markdown(DOCTOR_CSS, unsafe_allow_html=True)
    st.markdown("""
<div style="margin-bottom:8px;">
    <h1 style="margin:0;">👨‍⚕️ Doctor Portal</h1>
    <p style="color:#555;font-size:13px;margin:4px 0 0;">
        Create prescriptions · View history · Look up patients
    </p>
</div>""", unsafe_allow_html=True)

    # Load catalog once
    all_medicines = get_all_medicines()
    medicine_names = [m["name"] for m in all_medicines]
    med_lookup = {m["name"]: m for m in all_medicines}

    if not medicine_names:
        st.warning("⚠️ No medicines in catalog. Ask an admin to add medicines first.")
        return

    tab1, tab2, tab3 = st.tabs([
        "📝 New Prescription", "📋 My Prescriptions", "🔎 Patient Lookup"
    ])

    with tab1:
        _tab_new_prescription(medicine_names, med_lookup)
    with tab2:
        _tab_my_prescriptions()
    with tab3:
        _tab_patient_lookup()


# ──────────────────────────────────────────────
# TAB 1 — New Prescription
# ──────────────────────────────────────────────

def _tab_new_prescription(medicine_names, med_lookup):
    # ── Patient selection ──
    st.markdown("#### 👤 Patient")

    patients     = get_all_patients()
    patient_names = [p["name"] for p in patients]

    mode = st.radio("", ["Select Existing", "New Patient"], horizontal=True,
                    label_visibility="collapsed", key="doc_pat_mode")

    patient_age = patient_phone = ""
    patient_id  = None

    if mode == "Select Existing" and patient_names:
        patient_name = st.selectbox("Patient", patient_names, key="doc_pat_sel")
        sel_pat = get_patient_by_name(patient_name)
        if sel_pat:
            patient_id    = str(sel_pat["_id"])
            patient_age   = sel_pat.get("age","")
            patient_phone = sel_pat.get("phone","")
            active_meds   = [m for m in sel_pat.get("medications",[]) if m.get("status")=="active"]

            col1,col2,col3,col4 = st.columns(4)
            col1.metric("Age",          patient_age)
            col2.metric("Phone",        patient_phone if patient_phone else "—")
            col3.metric("Active Meds",  len(active_meds))
            col4.metric("Blood Group",  sel_pat.get("blood_group","—"))

            if active_meds:
                with st.expander("💊 Current Medications"):
                    for m in active_meds:
                        st.write(f"• **{m.get('name','')}** — {m.get('dosage','')} "
                                 f"_{m.get('prescribed_by','')}_")

            if sel_pat.get("medical_notes"):
                st.info(f"📋 Medical notes: {sel_pat['medical_notes']}")

    elif mode == "Select Existing" and not patient_names:
        st.info("No patients registered yet. Switch to New Patient.")
        patient_name = ""
    else:
        col1,col2,col3 = st.columns(3)
        with col1:
            patient_name = st.text_input("Patient Name *", key="doc_new_name")
        with col2:
            patient_age = st.number_input("Age", 0, 150, 25, key="doc_new_age")
        with col3:
            patient_phone = st.text_input("Phone", key="doc_new_phone")

    # ── Prescription details ──
    st.markdown("---")
    st.markdown("#### 📋 Prescription Details")

    col1,col2 = st.columns(2)
    with col1:
        doctor_name = st.text_input("Doctor Name", value=st.session_state.get("username",""),
                                    key="doc_doctor_name")
        caregiver   = st.text_input("Caregiver (optional)", placeholder="Name or phone", key="doc_caregiver")
    with col2:
        treatment   = st.selectbox("Treatment Type",
                                   ["General Treatment","Chronic Disease","Emergency","Post Surgery","Follow-up"],
                                   key="doc_treatment")
        priority    = st.selectbox("Priority", ["Normal","Urgent","Emergency"], key="doc_priority")

    # ── Medicines ──
    st.markdown("---")
    st.markdown("#### 💊 Medicines")
    st.caption("Search and select from the approved medicine catalog")

    # Category filter
    categories = {}
    for m in [{"name":n} for n in medicine_names]:
        pass
    all_cats = sorted({med_lookup[n].get("category","Other") for n in medicine_names})
    cat_filter = st.multiselect("Filter by category", all_cats, key="doc_cat_filter",
                                placeholder="All categories")
    filtered_meds = medicine_names if not cat_filter else [
        n for n in medicine_names if med_lookup[n].get("category","Other") in cat_filter
    ]

    selected = st.multiselect("Choose Medicines *", filtered_meds,
                              placeholder="Search medicines…", key="doc_med_sel")

    # Show medicine chips with details
    if selected:
        chips_html = ""
        for n in selected:
            info = med_lookup.get(n,{})
            warn = "med-chip-warn" if len(selected) > 1 else ""
            chips_html += (f'<span class="med-chip {warn}">'
                           f'💊 <b>{n}</b> '
                           f'<span class="med-chip-cat">{info.get("strength","")} '
                           f'{info.get("dosage_form","")} · {info.get("category","")}</span>'
                           f'</span>')
        st.markdown(chips_html, unsafe_allow_html=True)

    # Interaction check
    if len(selected) > 1:
        warnings = check_interactions(", ".join(selected))
        if warnings:
            for w in warnings:
                st.markdown(f"""
<div class="interaction-banner">
    <span style="font-size:18px">⚠️</span>
    <div>
        <p style="color:#ffaa00;font-weight:700;margin:0;font-size:13px">Drug Interaction Warning</p>
        <p style="color:#888;margin:2px 0 0;font-size:12px">{w}</p>
    </div>
</div>""", unsafe_allow_html=True)

    medicines_str = ", ".join(selected)

    col1,col2 = st.columns(2)
    with col1:
        dosage = st.text_input("Dosage Instructions *",
                               placeholder="e.g. Twice daily after meals for 7 days", key="doc_dosage")
    with col2:
        duration = st.text_input("Duration", placeholder="e.g. 5 days, 2 weeks", key="doc_duration")

    notes_doc = st.text_area("Clinical Notes (optional)",
                             placeholder="Additional notes for pharmacy / caregiver…",
                             height=80, key="doc_notes")

    # ── Generate ──
    st.markdown("---")
    col1,col2 = st.columns([1,3])
    with col1:
        generate = st.button("🖨️ Generate Prescription", use_container_width=True, type="primary")

    if generate:
        if not patient_name:
            st.error("Patient name is required.")
            return
        if not doctor_name:
            st.error("Doctor name is required.")
            return
        if not selected:
            st.error("Select at least one medicine.")
            return
        if not dosage:
            st.error("Dosage instructions are required.")
            return

        with st.spinner("Generating prescription…"):
            # Create patient if new
            if mode == "New Patient":
                existing = get_patient_by_name(patient_name)
                if not existing:
                    patient_id = create_patient({
                        "name": patient_name, "age": patient_age,
                        "phone": patient_phone, "caregiver": caregiver,
                        "medications": [], "medical_history": []
                    })
                else:
                    patient_id = str(existing["_id"])
            elif not patient_id:
                sel = get_patient_by_name(patient_name)
                patient_id = str(sel["_id"]) if sel else None

            prescription_id = "RX" + str(uuid.uuid4().hex)[:6].upper()

            prescription_data = {
                "prescription_id":  prescription_id,
                "patient_name":     patient_name,
                "patient_id":       patient_id,
                "caregiver":        caregiver,
                "doctor_name":      doctor_name,
                "medicines":        medicines_str,
                "dosage":           dosage,
                "duration":         duration,
                "treatment_type":   treatment,
                "priority":         priority,
                "clinical_notes":   notes_doc,
                "generated_date":   datetime.now().isoformat(),
            }

            qr_json = json.dumps(prescription_data, default=str)
            qr_path = generate_qr(qr_json, prescription_id)

            qr_url = None
            if cloudinary_configured():
                cloud = upload_qr_code(qr_path, prescription_id)
                if cloud:
                    qr_url = cloud["url"]
                    prescription_data["qr_code_url"] = qr_url

            insert_prescription(prescription_data)
            create_order({
                "prescription_id": prescription_id,
                "patient_name":    patient_name,
                "patient_id":      patient_id,
                "doctor_name":     doctor_name,
                "medicines":       medicines_str,
                "dosage":          dosage,
                "duration":        duration,
                "treatment_type":  treatment,
                "priority":        priority,
                "status":          "pending",
                "pharmacy_notes":  "",
                "created_by":      doctor_name,
            })

            if patient_id:
                for med_name in selected:
                    info = med_lookup.get(med_name, {})
                    add_medication_to_patient(patient_id, {
                        "name":            med_name,
                        "dosage":          dosage,
                        "strength":        info.get("strength",""),
                        "dosage_form":     info.get("dosage_form",""),
                        "prescribed_by":   doctor_name,
                        "prescription_id": prescription_id,
                        "treatment_type":  treatment,
                        "status":          "active",
                    })

        # ── Success display ──
        st.markdown(f"""
<div class="success-pulse">
    ✅ Prescription <code>{prescription_id}</code> created successfully · Order sent to pharmacy
</div>""", unsafe_allow_html=True)

        col_det, col_qr = st.columns([2, 1])
        with col_det:
            st.markdown(f"""
<div class="rx-result">
    <span class="rx-result-id">Rx {prescription_id}</span>
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <tr><td style="color:#555;padding:4px 0;width:130px;">Patient</td>
            <td style="color:#fff;font-weight:600;">{patient_name}</td></tr>
        <tr><td style="color:#555;padding:4px 0;">Doctor</td>
            <td style="color:#fff;">Dr. {doctor_name}</td></tr>
        <tr><td style="color:#555;padding:4px 0;">Treatment</td>
            <td style="color:#fff;">{treatment}</td></tr>
        <tr><td style="color:#555;padding:4px 0;">Priority</td>
            <td>{_status_pill(priority.lower()) if priority!='Normal' else '<span style="color:#555">Normal</span>'}</td></tr>
        <tr><td style="color:#555;padding:4px 0;">Medicines</td>
            <td style="color:#e0e0e0;">{medicines_str}</td></tr>
        <tr><td style="color:#555;padding:4px 0;">Dosage</td>
            <td style="color:#e0e0e0;">{dosage}</td></tr>
        <tr><td style="color:#555;padding:4px 0;">Duration</td>
            <td style="color:#e0e0e0;">{duration or "—"}</td></tr>
        <tr><td style="color:#555;padding:4px 0;">Caregiver</td>
            <td style="color:#e0e0e0;">{caregiver or "—"}</td></tr>
        <tr><td style="color:#555;padding:4px 0;">Date</td>
            <td style="color:#555;">{datetime.now().strftime("%d %b %Y · %H:%M")}</td></tr>
    </table>
</div>""", unsafe_allow_html=True)

        with col_qr:
            qr_src = qr_url or qr_path
            st.image(qr_src, caption=f"QR — {prescription_id}", use_container_width=True)
            with open(qr_path, "rb") as f:
                st.download_button("⬇️ Download QR", f, f"{prescription_id}_qr.png",
                                   "image/png", key="dl_qr_btn")


# ──────────────────────────────────────────────
# TAB 2 — My Prescriptions
# ──────────────────────────────────────────────

def _tab_my_prescriptions():
    doctor_name = st.session_state.get("username","")
    role        = st.session_state.get("role","doctor")

    if role == "admin":
        prescriptions = get_all_prescriptions()
        st.caption("(Admin view — all prescriptions)")
    else:
        prescriptions = get_prescriptions_by_doctor(doctor_name)

    if not prescriptions:
        st.info("No prescriptions found.")
        return

    # Metrics
    total = len(prescriptions)
    dates = [p.get("created_at") for p in prescriptions if p.get("created_at")]
    today_count = len([d for d in dates if hasattr(d,"date") and d.date()==datetime.utcnow().date()])

    col1,col2,col3 = st.columns(3)
    col1.metric("📋 Total Prescriptions", total)
    col2.metric("📅 Today",               today_count)
    unique_patients = len({p.get("patient_name","") for p in prescriptions})
    col3.metric("👤 Unique Patients",      unique_patients)

    st.markdown("---")

    # Search & filter
    col1,col2 = st.columns([3,1])
    with col1:
        search_q = st.text_input("Search patient / Rx ID", placeholder="Search…",
                                 label_visibility="collapsed", key="doc_rx_search")
    with col2:
        sort_new = st.checkbox("Newest first", value=True, key="doc_rx_sort")

    display = prescriptions
    if search_q:
        q = search_q.lower()
        display = [p for p in display if q in p.get("patient_name","").lower()
                   or q in p.get("prescription_id","").lower()]
    if sort_new:
        display = sorted(display, key=lambda p: p.get("created_at", datetime.min), reverse=True)

    for presc in display:
        rx_id   = presc.get("prescription_id","—")
        patient = presc.get("patient_name","—")
        meds    = presc.get("medicines","—")
        if len(meds) > 60: meds = meds[:60]+"…"
        date    = str(presc.get("created_at",""))[:10]

        order = get_order_by_prescription(rx_id)
        status = order.get("status","pending") if order else "—"

        label = f"Rx {rx_id}  ·  {patient}  ·  {date}"
        with st.expander(label):
            st.markdown(_status_pill(status), unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            col1,col2 = st.columns(2)
            with col1:
                st.markdown(f"**Patient:** {patient}")
                st.markdown(f"**Doctor:** {presc.get('doctor_name','—')}")
                st.markdown(f"**Caregiver:** {presc.get('caregiver','—')}")
                st.markdown(f"**Treatment:** {presc.get('treatment_type','—')}")
            with col2:
                st.markdown(f"**Medicines:** {presc.get('medicines','—')}")
                st.markdown(f"**Dosage:** {presc.get('dosage','—')}")
                if presc.get("duration"):
                    st.markdown(f"**Duration:** {presc['duration']}")
                if presc.get("priority") and presc["priority"] != "Normal":
                    st.markdown(f"**Priority:** {presc['priority']}")

            if presc.get("clinical_notes"):
                st.info(f"📋 {presc['clinical_notes']}")

            qr = presc.get("qr_code_url")
            if qr:
                with st.expander("📱 QR Code"):
                    st.image(qr, width=150)

            if order and order.get("pharmacy_notes"):
                st.warning(f"💬 Pharmacy: {order['pharmacy_notes']}")


# ──────────────────────────────────────────────
# TAB 3 — Patient Lookup
# ──────────────────────────────────────────────

def _tab_patient_lookup():
    st.markdown("#### 🔎 Patient Lookup")
    query = st.text_input("Search by name or phone", placeholder="Type patient name or number…",
                          key="doc_pat_search")
    if not query:
        # Show all patients as a table
        patients = get_all_patients()
        if patients:
            df = [{
                "Name":      p.get("name",""),
                "Age":       p.get("age","—"),
                "Phone":     p.get("phone","—"),
                "Blood Grp": p.get("blood_group","—"),
                "Caregiver": p.get("caregiver","—"),
                "Active Meds": len([m for m in p.get("medications",[]) if m.get("status")=="active"]),
            } for p in patients]
            st.dataframe(df, use_container_width=True, hide_index=True)
        return

    from modules.utils.db import search_patients
    results = search_patients(query)

    if not results:
        st.info("No patients found.")
        return

    st.success(f"Found {len(results)} patient(s)")
    for p in results:
        pid    = str(p["_id"])
        name   = p.get("name","Unknown")
        age    = p.get("age","—")
        phone  = p.get("phone","—")
        active = [m for m in p.get("medications",[]) if m.get("status")=="active"]
        presc  = get_prescriptions_by_patient(name) if True else []

        with st.expander(f"{name}  ·  Age {age}  ·  {len(active)} active meds"):
            col1,col2 = st.columns(2)

            with col1:
                st.markdown(f"""
<div class="pat-mini">
    <p style="color:#555;font-size:11px;text-transform:uppercase;letter-spacing:.5px;margin:0">Patient Info</p>
    <p style="color:#fff;font-weight:700;font-size:16px;margin:4px 0">{name}</p>
    <p style="color:#888;font-size:13px;margin:0">Age: {age} · Phone: {phone}</p>
    <p style="color:#888;font-size:13px;margin:4px 0 0">Blood Group: {p.get('blood_group','—')}</p>
    <p style="color:#888;font-size:13px;margin:4px 0 0">Caregiver: {p.get('caregiver','—')}</p>
</div>""", unsafe_allow_html=True)

                if p.get("medical_notes"):
                    st.warning(f"📋 {p['medical_notes']}")

            with col2:
                st.markdown("**💊 Active Medications**")
                if active:
                    for m in active:
                        st.markdown(f"• **{m.get('name','')}** — {m.get('dosage','')}  "
                                    f"_{m.get('prescribed_by','')}_")
                else:
                    st.caption("No active medications")

            # Prescription history
            try:
                from modules.utils.db import get_prescriptions_by_patient
                prescriptions = get_prescriptions_by_patient(name)
            except Exception:
                prescriptions = []

            if prescriptions:
                st.markdown("---")
                st.markdown("**📋 Prescription History**")
                for pr in sorted(prescriptions, key=lambda x: x.get("created_at",datetime.min), reverse=True)[:5]:
                    rx_id  = pr.get("prescription_id","—")
                    doc    = pr.get("doctor_name","—")
                    meds   = pr.get("medicines","—")
                    if len(meds) > 50: meds = meds[:50]+"…"
                    date   = str(pr.get("created_at",""))[:10]
                    order  = get_order_by_prescription(rx_id)
                    status = order.get("status","—") if order else "—"
                    st.markdown(f"""
<div class="rx-hist-item">
    <span class="rx-hist-id">{rx_id}</span>
    <div class="rx-hist-body">Dr. {doc} · {meds}</div>
    {_status_pill(status)}
    <span class="rx-hist-date">{date}</span>
</div>""", unsafe_allow_html=True)