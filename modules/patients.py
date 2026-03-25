"""
Patient Management — Premium Rebuild
Tabs: All Patients (cards+table) · Register · Search · Adherence Tracker
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from modules.utils.db import (
    create_patient, get_all_patients, get_patient,
    update_patient, add_medication_to_patient,
    remove_medication_from_patient, search_patients,
    get_prescriptions_by_patient, get_all_medicines,
    get_order_by_prescription
)

# ─────────────────── CSS ───────────────────
PATIENT_CSS = """
<style>
/* Patient profile card — sky theme */
.pat-card {
    background:rgba(255,255,255,0.92); border:1px solid rgba(72,184,206,0.5); border-radius:12px;
    padding:18px; margin-bottom:4px; box-shadow:0 2px 10px rgba(13,76,92,0.06);
}
.pat-name  { font-size:18px;font-weight:800;color:#0a3d47;margin:0; }
.pat-sub   { color:#2d5c6a;font-size:12px;margin:2px 0 0; }

/* Med badge */
.med-badge {
    display:inline-block; background:rgba(197,238,246,0.5); border:1px solid rgba(72,184,206,0.45);
    border-radius:6px; padding:4px 10px; font-size:12px;
    color:#0a3d47; margin:3px 3px 3px 0;
}
.med-badge-active   { border-color:rgba(13,138,91,0.5); color:#0d6b47; background:rgba(13,138,91,0.1); }
.med-badge-inactive { border-color:rgba(72,184,206,0.35); color:#4a7a8a; }

/* Adherence ring */
.adh-ring-wrap   { text-align:center; padding:8px; }
.adh-ring-value  { font-size:24px;font-weight:800;color:#0a3d47; }
.adh-ring-label  { font-size:11px;color:#2d5c6a;text-transform:uppercase;letter-spacing:.5px; }

/* History row */
.hist-row {
    display:flex; gap:10px; align-items:center;
    padding:8px 0; border-bottom:1px solid rgba(72,184,206,0.25); font-size:13px;
}
.hist-rx  { color:#0a3d47;font-weight:700;min-width:90px; }
.hist-med { color:#4a7a8a;flex:1;font-size:12px; }
.hist-date{ color:#2d5c6a;font-size:11px; }

/* Blood group badge */
.blood-badge {
    display:inline-block; padding:2px 10px;border-radius:20px;
    font-size:12px;font-weight:700;
    background:#1a0010;color:#ff44aa;border:1px solid #ff44aa30;
}

/* Search result card */
.search-card {
    background:rgba(255,255,255,0.92); border:1px solid rgba(72,184,206,0.5); border-radius:10px;
    padding:14px 16px; margin-bottom:8px;
    display:flex; gap:14px; align-items:flex-start;
    box-shadow:0 1px 8px rgba(13,76,92,0.05);
}
.search-avatar {
    width:44px;height:44px;border-radius:50%;background:rgba(197,238,246,0.8);
    border:1px solid rgba(72,184,206,0.45);display:flex;align-items:center;
    justify-content:center;font-size:18px;flex-shrink:0;
}
</style>
"""


def _status_pill(status: str) -> str:
    colors = {"pending":"#ffaa00","processing":"#00aaff","dispensed":"#cc44ff",
              "completed":"#00cc44","cancelled":"#ff4444"}
    c = colors.get(status, "#555")
    return (f'<span style="background:{c}20;color:{c};border:1px solid {c}40;'
            f'padding:2px 8px;border-radius:20px;font-size:10px;font-weight:700;'
            f'text-transform:uppercase;">{status}</span>')


def show():
    st.markdown(PATIENT_CSS, unsafe_allow_html=True)
    st.markdown("""
<div style="margin-bottom:8px;">
    <h1 style="margin:0;">👤 Patients</h1>
    <p style="color:#2d5c6a;font-size:13px;margin:4px 0 0;">
        Patient management · Medication tracking · Adherence monitoring
    </p>
</div>""", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 All Patients", "➕ Register", "🔎 Search", "📊 Adherence"
    ])
    with tab1: show_all()
    with tab2: show_add()
    with tab3: show_search()
    with tab4: show_adherence()


# ──────────────────────────────────────────────
# ALL PATIENTS
# ──────────────────────────────────────────────

def show_all():
    patients = get_all_patients()
    if not patients:
        st.info("No patients registered. Use the Register tab to add one.")
        return

    medicine_catalog = get_all_medicines()
    med_names = [m["name"] for m in medicine_catalog]

    # Metrics
    total      = len(patients)
    with_meds  = len([p for p in patients if any(m.get("status")=="active" for m in p.get("medications",[]))])
    no_cg      = len([p for p in patients if not p.get("caregiver")])

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("👥 Total Patients",    total)
    col2.metric("💊 On Medications",    with_meds)
    col3.metric("✅ Have Caregiver",    total-no_cg)
    col4.metric("⚠️ No Caregiver",     no_cg)

    st.markdown("---")

    # View toggle + search
    col1,col2,col3 = st.columns([2,2,1])
    with col1:
        search_q = st.text_input("Filter patients", placeholder="Search name or phone…",
                                 label_visibility="collapsed", key="pat_all_search")
    with col2:
        med_filter = st.selectbox("Filter by medication", ["All"] + med_names,
                                  key="pat_med_filter")
    with col3:
        view = st.radio("View", ["🃏","📊"], horizontal=True, label_visibility="collapsed", key="pat_view")

    display = patients
    if search_q:
        q = search_q.lower()
        display = [p for p in display if q in p.get("name","").lower() or q in p.get("phone","").lower()]
    if med_filter != "All":
        display = [p for p in display if any(
            m.get("name","").lower() == med_filter.lower() and m.get("status")=="active"
            for m in p.get("medications",[])
        )]

    if view == "📊":
        # Table mode
        rows = [{
            "Name":       p.get("name",""),
            "Age":        p.get("age","—"),
            "Phone":      p.get("phone","—"),
            "Blood Grp":  p.get("blood_group","—"),
            "Caregiver":  p.get("caregiver","—"),
            "Active Meds": len([m for m in p.get("medications",[]) if m.get("status")=="active"]),
        } for p in display]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        return

    # Card mode — dropdown + detail panel (avoids expander / _arrow_right overlap)
    def _patient_row_label(p):
        n = p.get("name", "Unknown")
        a = p.get("age", "—")
        meds_local = p.get("medications", [])
        ac = len([m for m in meds_local if m.get("status") == "active"])
        return f"{n} · Age {a} · {ac} active med{'s' if ac != 1 else ''}"

    row_labels = [_patient_row_label(p) for p in display]

    st.markdown("**Select a patient to view and edit:**")
    ix = st.selectbox(
        "",
        list(range(len(display))),
        format_func=lambda i: row_labels[i],
        key="pat_card_pick",
        label_visibility="collapsed",
    )
    patient = display[ix]

    pid = str(patient["_id"])
    name = patient.get("name", "Unknown")
    age = patient.get("age", "—")
    phone = patient.get("phone", "—")
    blood = patient.get("blood_group", "")
    cg = patient.get("caregiver", "—")
    notes = patient.get("medical_notes", "")
    meds = patient.get("medications", [])
    active = [m for m in meds if m.get("status") == "active"]
    inactive = [m for m in meds if m.get("status") != "active"]

    blood_html = f'<span class="blood-badge">{blood}</span>' if blood else ""
    st.markdown(f"""
<div class="pat-card">
    <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
            <p class="pat-name">{name}</p>
            <p class="pat-sub">Age {age} · 📞 {phone} · 👨‍👩‍👦 {cg} {blood_html}</p>
        </div>
        <div style="text-align:right">
            <p style="color:#2d5c6a;font-size:11px;margin:0">Active Medications</p>
            <p style="color:#0a3d47;font-size:22px;font-weight:800;margin:0">{len(active)}</p>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

    if notes:
        st.warning(f"📋 {notes}")

    if active or inactive:
        st.markdown("**💊 Medications**")
        all_med_html = ""
        for m in active:
            all_med_html += f'<span class="med-badge med-badge-active">✓ {m.get("name","")}</span>'
        for m in inactive:
            all_med_html += f'<span class="med-badge med-badge-inactive">{m.get("name","")}</span>'
        st.markdown(all_med_html, unsafe_allow_html=True)

        if active:
            st.markdown("**📋 Medication details**")
            for m in active:
                st.markdown(
                    f"• **{m.get('name','')}** — {m.get('dosage','—')} "
                    f"_{m.get('strength','')} {m.get('dosage_form','')}_  "
                    f"Rx: {m.get('prescription_id','')}  "
                    f"by Dr.{m.get('prescribed_by','')}"
                )

    st.markdown("---")

    col_edit, col_add = st.columns(2)

    with col_edit:
        st.markdown("**✏️ Edit Info**")
        new_phone = st.text_input("Phone", value=phone if phone != "—" else "", key=f"ph_{pid}")
        new_cg = st.text_input("Caregiver", value=cg if cg != "—" else "", key=f"cg_{pid}")
        new_bg = st.selectbox(
            "Blood Group",
            ["", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"],
            index=(
                ["", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"].index(blood)
                if blood in ["", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
                else 0
            ),
            key=f"bg_{pid}",
        )
        new_notes = st.text_input("Medical Notes", value=notes, key=f"mn_{pid}")
        if st.button("💾 Save", key=f"sv_{pid}"):
            update_patient(
                pid,
                {
                    "phone": new_phone,
                    "caregiver": new_cg,
                    "blood_group": new_bg,
                    "medical_notes": new_notes,
                },
            )
            st.success("Updated ✓")
            st.rerun()

    with col_add:
        st.markdown("**➕ Add Medication**")
        if med_names:
            new_med = st.selectbox("Medicine", med_names, key=f"am_{pid}")
        else:
            new_med = st.text_input("Medicine", key=f"am_{pid}")
        new_dose = st.text_input("Dosage", key=f"ad_{pid}", placeholder="e.g. 500mg twice daily")
        if st.button("➕ Add", key=f"ab_{pid}"):
            if new_med:
                add_medication_to_patient(
                    pid,
                    {
                        "name": new_med,
                        "dosage": new_dose,
                        "prescribed_by": st.session_state.get("username", ""),
                        "status": "active",
                        "added_at": datetime.utcnow().isoformat(),
                    },
                )
                st.success(f"Added {new_med} ✓")
                st.rerun()

        if active:
            st.markdown("**🗑️ Remove Medication**")
            rem_med = st.selectbox("Remove", [m.get("name") for m in active], key=f"rm_{pid}")
            if st.button("Remove", key=f"rb_{pid}"):
                remove_medication_from_patient(pid, rem_med)
                st.success(f"Removed {rem_med}")
                st.rerun()

    st.markdown("---")
    st.markdown("**📋 Prescription History**")
    prescriptions = get_prescriptions_by_patient(name)
    if prescriptions:
        for pr in sorted(prescriptions, key=lambda x: x.get("created_at", datetime.min), reverse=True)[:5]:
            rx_id = pr.get("prescription_id", "—")
            doc = pr.get("doctor_name", "—")
            meds_s = pr.get("medicines", "—")
            if len(meds_s) > 50:
                meds_s = meds_s[:50] + "…"
            date = str(pr.get("created_at", ""))[:10]
            order = get_order_by_prescription(rx_id)
            status = order.get("status", "—") if order else "—"

            st.markdown(f"""
<div class="hist-row">
    <span class="hist-rx">{rx_id}</span>
    <span class="hist-med">Dr. {doc} · {meds_s}</span>
    {_status_pill(status)}
    <span class="hist-date">{date}</span>
</div>""", unsafe_allow_html=True)
    else:
        st.caption("No prescription history")


# ──────────────────────────────────────────────
# REGISTER PATIENT
# ──────────────────────────────────────────────

def show_add():
    st.markdown("#### ➕ Register New Patient")

    with st.form("add_patient_form", clear_on_submit=True):
        col1,col2 = st.columns(2)
        with col1:
            name     = st.text_input("Full Name *", placeholder="e.g. Ravi Kumar")
            age      = st.number_input("Age", 0, 150, 25)
            phone    = st.text_input("Phone Number", placeholder="+91 98765 43210")
            email    = st.text_input("Email (optional)")
        with col2:
            caregiver = st.text_input("Caregiver Name / Phone")
            blood     = st.selectbox("Blood Group", ["","A+","A-","B+","B-","O+","O-","AB+","AB-"])
            gender    = st.selectbox("Gender", ["", "Male","Female","Other","Prefer not to say"])
            address   = st.text_input("Address (optional)")

        notes = st.text_area("Medical Notes", placeholder="Allergies, chronic conditions, known reactions…")
        emergency_contact = st.text_input("Emergency Contact (optional)")

        submitted = st.form_submit_button("✅ Register Patient", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Patient name is required.")
            return
        pid = create_patient({
            "name":              name.strip(),
            "age":               age,
            "phone":             phone,
            "email":             email,
            "caregiver":         caregiver,
            "blood_group":       blood,
            "gender":            gender,
            "address":           address,
            "medical_notes":     notes,
            "emergency_contact": emergency_contact,
            "medications":       [],
            "medical_history":   [],
        })
        st.success(f"✅ Patient **{name}** registered successfully!")
        st.balloons()
        st.markdown(f"""
<div style="background:#001a05;border:1px solid #00cc4430;border-left:3px solid #00cc44;
border-radius:8px;padding:12px 16px;margin-top:8px;">
    <p style="color:#00cc44;font-weight:700;margin:0;font-size:14px">Patient Created</p>
    <p style="color:#555;font-size:12px;margin:4px 0 0">{name} · Age {age} · {phone or "no phone"}</p>
</div>""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SEARCH
# ──────────────────────────────────────────────

def show_search():
    st.markdown("#### 🔎 Search Patients")
    query = st.text_input("Search by name or phone", placeholder="Type to search…",
                          key="pat_search_q")
    if not query:
        return

    results = search_patients(query)
    if not results:
        st.info(f"No patients found for **{query}**")
        return

    st.success(f"**{len(results)}** patient(s) found")

    for p in results:
        name   = p.get("name","Unknown")
        age    = p.get("age","—")
        phone  = p.get("phone","—")
        blood  = p.get("blood_group","")
        cg     = p.get("caregiver","—")
        active = [m for m in p.get("medications",[]) if m.get("status")=="active"]

        st.markdown(f"""
<div class="search-card">
    <div class="search-avatar">👤</div>
    <div style="flex:1">
        <p style="color:#0a3d47;font-weight:700;font-size:15px;margin:0">{name}</p>
        <p style="color:#2d5c6a;font-size:12px;margin:3px 0">
            Age {age} · 📞 {phone}
            {' · <span class="blood-badge">' + blood + '</span>' if blood else ''}
        </p>
        <p style="color:#4a7a8a;font-size:12px;margin:3px 0">Caregiver: {cg}</p>
        <p style="color:#4a7a8a;font-size:12px;margin:3px 0">{len(active)} active medication(s)</p>
    </div>
</div>""", unsafe_allow_html=True)

        st.markdown(f"**Full details — {name}**")
        if active:
            st.markdown("**Active medications**")
            for m in active:
                st.markdown(
                    f"• **{m.get('name','')}** — {m.get('dosage','')} _{m.get('prescribed_by','')}_"
                )

        prescriptions = get_prescriptions_by_patient(name)
        if prescriptions:
            st.markdown(f"**{len(prescriptions)} prescription(s)**")
            for pr in sorted(
                prescriptions, key=lambda x: x.get("created_at", datetime.min), reverse=True
            )[:3]:
                rx_id = pr.get("prescription_id", "—")
                date = str(pr.get("created_at", ""))[:10]
                st.caption(f"• {rx_id} · Dr. {pr.get('doctor_name','—')} · {date}")

        st.markdown("---")


# ──────────────────────────────────────────────
# ADHERENCE TRACKER
# ──────────────────────────────────────────────

def show_adherence():
    st.markdown("#### 📊 Medication Adherence Tracker")
    st.caption("Track and log patient adherence to prescribed medication schedules")

    patients = get_all_patients()
    if not patients:
        st.info("No patients registered.")
        return

    # Summary
    adherence_data = st.session_state.setdefault("adherence_scores", {})

    col1,col2,col3 = st.columns(3)
    scores = list(adherence_data.values())
    col1.metric("📋 Patients", len(patients))
    col2.metric("📊 Avg Adherence", f"{int(sum(scores)/len(scores))}%" if scores else "—")
    low_adh = len([s for s in scores if s < 70])
    col3.metric("⚠️ Low Adherence", low_adh)

    st.markdown("---")

    with_active = [
        p for p in patients
        if any(m.get("status") == "active" for m in p.get("medications", []))
    ]
    if not with_active:
        st.info("No patients with active medications to track.")
    else:
        adh_labels = []
        for patient in with_active:
            pid = str(patient["_id"])
            name = patient.get("name", "Unknown")
            age = patient.get("age", "—")
            sc = adherence_data.get(pid, 85)
            stxt = "🔴 Critical" if sc < 60 else ("🟡 Moderate" if sc < 80 else "🟢 Good")
            adh_labels.append(f"{name} · Age {age} · {stxt} · {sc}%")

        st.markdown("**Select a patient:**")
        adh_ix = st.selectbox(
            "",
            list(range(len(with_active))),
            format_func=lambda i: adh_labels[i],
            key="adh_patient_pick",
            label_visibility="collapsed",
        )
        patient = with_active[adh_ix]
        pid = str(patient["_id"])
        name = patient.get("name", "Unknown")
        age = patient.get("age", "—")
        active = [m for m in patient.get("medications", []) if m.get("status") == "active"]
        score = adherence_data.get(pid, 85)
        bar_color = "#ff2d2d" if score < 60 else ("#ffaa00" if score < 80 else "#00cc44")
        status_txt = "🔴 Critical" if score < 60 else ("🟡 Moderate" if score < 80 else "🟢 Good")

        st.caption(f"{name} · Age {age} · {status_txt}")

        col1, col2 = st.columns([3, 1])
        with col1:
            new_score = st.slider(
                "Adherence Score (%)",
                0,
                100,
                score,
                key=f"adh_sl_{pid}",
                help="Drag to update patient's observed adherence",
            )
            if new_score != score:
                adherence_data[pid] = new_score
                st.session_state["adherence_scores"] = adherence_data

            st.markdown(f"""
<div style="background:rgba(197,238,246,0.85);border-radius:6px;height:8px;margin:4px 0 8px">
    <div style="background:{bar_color};width:{new_score}%;height:8px;border-radius:6px;transition:width .3s"></div>
</div>""", unsafe_allow_html=True)

            if new_score < 60:
                st.error("⚠️ Critical adherence — immediate intervention needed. Contact caregiver.")
            elif new_score < 80:
                st.warning("⚠️ Moderate adherence — consider setting custom dose reminders.")
            else:
                st.success("✅ Good adherence — patient is taking medications as prescribed.")

        with col2:
            st.markdown(f"""
<div class="adh-ring-wrap">
    <p class="adh-ring-value" style="color:{bar_color}">{new_score}%</p>
    <p class="adh-ring-label">Adherence</p>
</div>""", unsafe_allow_html=True)

        st.markdown("**Active meds being tracked:**")
        for m in active:
            st.markdown(f"• **{m.get('name','')}** — {m.get('dosage','')}")

    # Export
    if adherence_data:
        st.markdown("---")
        rows = []
        for p in patients:
            pid = str(p["_id"])
            if pid in adherence_data:
                rows.append({
                    "Patient":   p.get("name",""),
                    "Age":       p.get("age",""),
                    "Adherence": f"{adherence_data[pid]}%",
                    "Status":    "Critical" if adherence_data[pid]<60
                                  else ("Moderate" if adherence_data[pid]<80 else "Good"),
                })
        if rows:
            df = pd.DataFrame(rows)
            st.download_button("⬇️ Export Adherence Report CSV",
                               df.to_csv(index=False).encode(),
                               "adherence_report.csv","text/csv",
                               key="adh_csv_dl")
