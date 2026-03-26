"""
Doctor Module — Premium Rebuild
Tabs: New Prescription · My Prescriptions · Patient Lookup
"""
from html import escape
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
    get_order_by_prescription, get_prescriptions_by_patient,
    search_patients,
)
from modules.utils.cloudinary_config import upload_qr_code, is_configured as cloudinary_configured

# ─────────────────── CSS (sky theme — matches app) ───────────────────
DOCTOR_CSS = """
<style>
.med-chip {
    display:inline-flex; align-items:center; gap:6px;
    background:rgba(255,255,255,.92); border:1px solid rgba(72,184,206,.5); border-radius:8px;
    padding:6px 12px; margin:4px 4px 4px 0; font-size:13px; color:#0a3d47;
}
.med-chip-cat { color:#4a7a8a; font-size:11px; }
.med-chip-warn { border-color:rgba(184,134,11,.55); background:rgba(255,248,220,.9); }

.interaction-banner {
    background:rgba(255,243,224,.96); border:1px solid rgba(255,170,0,.4);
    border-left:3px solid #e65100; border-radius:8px;
    padding:10px 14px; margin:8px 0;
    display:flex; gap:10px; align-items:flex-start;
}

.rx-result {
    background:linear-gradient(135deg,rgba(255,255,255,.96),rgba(232,248,252,.92));
    border:1px solid rgba(72,184,206,.45); border-radius:12px;
    padding:18px; margin-top:12px;
    box-shadow:0 2px 12px rgba(13,76,92,.06);
}
.rx-result-id {
    font-size:20px; font-weight:800; color:#0a3d47;
    letter-spacing:-0.5px; margin-bottom:14px; display:block;
}
.success-pulse {
    background:rgba(230,250,245,.95); border:1px solid rgba(13,138,91,.35);
    border-left:3px solid #0d8a5b; border-radius:8px;
    padding:12px 16px; font-size:14px; color:#0d6b47;
    font-weight:600; margin-bottom:12px;
}

.rx-hist-item {
    display:flex; gap:12px; align-items:flex-start; flex-wrap:wrap;
    padding:10px 0; border-bottom:1px solid rgba(72,184,206,.28);
}
.rx-hist-id   { color:#0a3d47; font-weight:700; font-size:13px; min-width:90px; }
.rx-hist-body { flex:1; color:#4a7a8a; font-size:12px; min-width:100px; }
.rx-hist-date { color:#2d5c6a; font-size:11px; flex-shrink:0; }

.pat-mini {
    background:rgba(255,255,255,.9);
    border:1px solid rgba(72,184,206,.45); border-radius:10px;
    padding:14px; margin-bottom:8px;
}

.doc-current-meds {
    background:rgba(255,255,255,.78);
    border:1px solid rgba(72,184,206,.4);
    border-radius:10px;
    padding:12px 14px;
    margin-top:8px;
}
.doc-rx-detail {
    background:rgba(255,255,255,.9);
    border:1px solid rgba(72,184,206,.42);
    border-radius:12px;
    padding:16px 18px;
    margin-top:10px;
    box-shadow:0 2px 10px rgba(13,76,92,.05);
}
.doc-rx-detail-h {
    font-size:15px; font-weight:700; color:#0a3d47;
    margin:0 0 12px; padding-bottom:10px;
    border-bottom:1px solid rgba(72,184,206,.35);
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
    <p style="color:#2d5c6a;font-size:13px;margin:4px 0 0;">
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

    mode = st.radio("Patient Mode", ["Select Existing", "New Patient"], horizontal=True,
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
                st.markdown(
                    '<p style="margin:10px 0 6px;font-weight:700;color:#0a3d47;font-size:13px;">'
                    "💊 Current medications</p>",
                    unsafe_allow_html=True,
                )
                lines = "".join(
                    f'<p style="margin:4px 0;font-size:13px;color:#2d5c6a;">• '
                    f"<strong>{escape(str(m.get('name','')))}</strong> — "
                    f"{escape(str(m.get('dosage','')))} "
                    f'<span style="color:#4a7a8a;">Dr. {escape(str(m.get("prescribed_by","")))}</span></p>'
                    for m in active_meds
                )
                st.markdown(
                    f'<div class="doc-current-meds">{lines}</div>',
                    unsafe_allow_html=True,
                )

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
                we = escape(str(w))
                st.markdown(
                    f'<div class="interaction-banner"><span style="font-size:18px">⚠️</span>'
                    f'<div><p style="color:#bf360c;font-weight:700;margin:0;font-size:13px">'
                    f"Drug interaction warning</p>"
                    f'<p style="color:#4a7a8a;margin:2px 0 0;font-size:12px">{we}</p></div></div>',
                    unsafe_allow_html=True,
                )

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
        pid_e = escape(str(prescription_id))
        st.markdown(
            f'<div class="success-pulse">✅ Prescription <code>{pid_e}</code> created · '
            f"order sent to pharmacy</div>",
            unsafe_allow_html=True,
        )

        pn_e, dn_e = escape(str(patient_name)), escape(str(doctor_name))
        tr_e = escape(str(treatment))
        ms_e, ds_e = escape(str(medicines_str)), escape(str(dosage))
        du_e, cg_e = escape(str(duration or "—")), escape(str(caregiver or "—"))
        pri_cell = (
            _status_pill(priority.lower())
            if priority != "Normal"
            else '<span style="color:#4a7a8a">Normal</span>'
        )
        dt = escape(datetime.now().strftime("%d %b %Y · %H:%M"))
        tbl = (
            f'<div class="rx-result"><span class="rx-result-id">Rx {pid_e}</span>'
            f'<table style="width:100%;border-collapse:collapse;font-size:13px;">'
            f'<tr><td style="color:#4a7a8a;padding:4px 0;width:130px;">Patient</td>'
            f'<td style="color:#0a3d47;font-weight:600;">{pn_e}</td></tr>'
            f'<tr><td style="color:#4a7a8a;padding:4px 0;">Doctor</td>'
            f'<td style="color:#0a3d47;">Dr. {dn_e}</td></tr>'
            f'<tr><td style="color:#4a7a8a;padding:4px 0;">Treatment</td>'
            f'<td style="color:#0a3d47;">{tr_e}</td></tr>'
            f'<tr><td style="color:#4a7a8a;padding:4px 0;">Priority</td><td>{pri_cell}</td></tr>'
            f'<tr><td style="color:#4a7a8a;padding:4px 0;">Medicines</td>'
            f'<td style="color:#2d5c6a;">{ms_e}</td></tr>'
            f'<tr><td style="color:#4a7a8a;padding:4px 0;">Dosage</td>'
            f'<td style="color:#2d5c6a;">{ds_e}</td></tr>'
            f'<tr><td style="color:#4a7a8a;padding:4px 0;">Duration</td>'
            f'<td style="color:#2d5c6a;">{du_e}</td></tr>'
            f'<tr><td style="color:#4a7a8a;padding:4px 0;">Caregiver</td>'
            f'<td style="color:#2d5c6a;">{cg_e}</td></tr>'
            f'<tr><td style="color:#4a7a8a;padding:4px 0;">Date</td>'
            f'<td style="color:#2d5c6a;">{dt}</td></tr>'
            f"</table></div>"
        )

        col_det, col_qr = st.columns([2, 1])
        with col_det:
            st.markdown(tbl, unsafe_allow_html=True)

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

    row_labels = []
    for presc in display:
        rx_id = presc.get("prescription_id", "—")
        patient = presc.get("patient_name", "—")
        date = str(presc.get("created_at", ""))[:10]
        row_labels.append(f"Rx {rx_id} · {patient} · {date}")

    st.markdown("**Select a prescription:**")
    pick_ix = st.selectbox(
        "",
        list(range(len(display))),
        format_func=lambda i: row_labels[i],
        key="doc_my_rx_pick",
        label_visibility="collapsed",
    )
    presc = display[pick_ix]

    rx_id = presc.get("prescription_id", "—")
    patient = presc.get("patient_name", "—")
    order = get_order_by_prescription(rx_id)
    status = order.get("status", "pending") if order else "—"

    st.markdown(
        f'<div class="doc-rx-detail-h">Rx {escape(str(rx_id))} · '
        f"{escape(str(patient))} · {escape(str(presc.get('created_at',''))[:10])}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(_status_pill(status), unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Patient:** {patient}")
        st.markdown(f"**Doctor:** {presc.get('doctor_name','—')}")
        st.markdown(f"**Caregiver:** {presc.get('caregiver','—') or '—'}")
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
        st.markdown("**QR code**")
        st.image(qr, width=200)

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
        patients = get_all_patients()
        if patients:
            df = [{
                "Name":      p.get("name", ""),
                "Age":       p.get("age", "—"),
                "Phone":     p.get("phone", "—"),
                "Blood Grp": p.get("blood_group", "—"),
                "Caregiver": p.get("caregiver", "—"),
                "Active Meds": len([m for m in p.get("medications", []) if m.get("status") == "active"]),
            } for p in patients]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No patients registered yet.")
        return

    results = search_patients(query)
    if not results:
        st.info("No patients found.")
        return

    st.success(f"Found **{len(results)}** patient(s)")

    if len(results) > 1:
        labels = []
        for p in results:
            act = [m for m in p.get("medications", []) if m.get("status") == "active"]
            labels.append(
                f"{p.get('name', 'Unknown')} · Age {p.get('age', '—')} · {len(act)} active med(s)"
            )
        ix = st.selectbox(
            "Select patient",
            list(range(len(results))),
            format_func=lambda i: labels[i],
            key="doc_lookup_pick",
        )
        p = results[ix]
    else:
        p = results[0]

    name = p.get("name", "Unknown")
    age = p.get("age", "—")
    phone = p.get("phone", "—")
    active = [m for m in p.get("medications", []) if m.get("status") == "active"]
    ne = escape(str(name))
    ae, pe = escape(str(age)), escape(str(phone))
    bg = escape(str(p.get("blood_group", "—")))
    cg = escape(str(p.get("caregiver", "—")))

    mini = (
        f'<div class="pat-mini">'
        f'<p style="color:#4a7a8a;font-size:11px;text-transform:uppercase;letter-spacing:.5px;margin:0">'
        f"Patient info</p>"
        f'<p style="color:#0a3d47;font-weight:700;font-size:16px;margin:4px 0">{ne}</p>'
        f'<p style="color:#2d5c6a;font-size:13px;margin:0">Age {ae} · 📞 {pe}</p>'
        f'<p style="color:#2d5c6a;font-size:13px;margin:4px 0 0">Blood: {bg}</p>'
        f'<p style="color:#2d5c6a;font-size:13px;margin:4px 0 0">Caregiver: {cg}</p>'
        f"</div>"
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(mini, unsafe_allow_html=True)
        if p.get("medical_notes"):
            st.warning(f"📋 {p['medical_notes']}")
    with col2:
        st.markdown("**💊 Active medications**")
        if active:
            med_lines = "".join(
                f'<p style="margin:4px 0;font-size:13px;color:#2d5c6a;">• '
                f"<strong>{escape(str(m.get('name','')))}</strong> — "
                f"{escape(str(m.get('dosage','')))} "
                f'<span style="color:#4a7a8a;">{escape(str(m.get("prescribed_by","")))}</span></p>'
                for m in active
            )
            st.markdown(
                f'<div class="doc-current-meds">{med_lines}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("No active medications")

    prescriptions = get_prescriptions_by_patient(name)
    if prescriptions:
        st.markdown("---")
        st.markdown("**📋 Prescription history**")
        for pr in sorted(
            prescriptions, key=lambda x: x.get("created_at", datetime.min), reverse=True
        )[:5]:
            rx_id = pr.get("prescription_id", "—")
            doc = pr.get("doctor_name", "—")
            meds = pr.get("medicines", "—")
            if len(meds) > 50:
                meds = meds[:50] + "…"
            date = str(pr.get("created_at", ""))[:10]
            order = get_order_by_prescription(rx_id)
            status = order.get("status", "—") if order else "—"
            rx_e = escape(str(rx_id))
            doc_e, meds_e, date_e = escape(str(doc)), escape(str(meds)), escape(str(date))
            hist = (
                f'<div class="rx-hist-item">'
                f'<span class="rx-hist-id">{rx_e}</span>'
                f'<div class="rx-hist-body">Dr. {doc_e} · {meds_e}</div>'
                f"{_status_pill(status)}"
                f'<span class="rx-hist-date">{date_e}</span>'
                f"</div>"
            )
            st.markdown(hist, unsafe_allow_html=True)