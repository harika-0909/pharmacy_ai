"""
Doctor Prescription Module — Medicines from catalog
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
    add_medication_to_patient, get_all_medicines
)
from modules.utils.cloudinary_config import upload_qr_code, is_configured as cloudinary_configured


def show():
    st.title("👨‍⚕️ Prescriptions")

    # Load medicine catalog
    all_medicines = get_all_medicines()
    medicine_names = [m["name"] for m in all_medicines]

    if not medicine_names:
        st.warning("No medicines in catalog. Ask admin to add medicines first.")
        st.stop()

    # Build medicine lookup
    med_lookup = {}
    for m in all_medicines:
        med_lookup[m["name"]] = m

    # --- Patient ---
    st.markdown("##### Patient")

    patients = get_all_patients()
    patient_names = [p["name"] for p in patients]

    patient_mode = st.radio("", ["Existing Patient", "New Patient"], horizontal=True, label_visibility="collapsed")

    if patient_mode == "Existing Patient" and patient_names:
        patient_name = st.selectbox("Select Patient", patient_names)
        selected_patient = get_patient_by_name(patient_name)
        if selected_patient:
            col1, col2, col3 = st.columns(3)
            col1.metric("Age", selected_patient.get("age", "—"))
            col2.metric("Phone", selected_patient.get("phone", "—"))
            active = [m for m in selected_patient.get("medications", []) if m.get("status") == "active"]
            col3.metric("Active Meds", len(active))
            patient_age = selected_patient.get("age", "")
            patient_phone = selected_patient.get("phone", "")
        else:
            patient_age, patient_phone = "", ""
    else:
        patient_name = st.text_input("Patient Name")
        c1, c2 = st.columns(2)
        with c1:
            patient_age = st.number_input("Age", min_value=0, max_value=150, value=25)
        with c2:
            patient_phone = st.text_input("Phone")

    st.divider()

    # --- Details ---
    st.markdown("##### Details")
    col1, col2 = st.columns(2)
    with col1:
        caregiver = st.text_input("Caregiver", placeholder="Name or phone")
    with col2:
        doctor_name = st.text_input("Doctor", value=st.session_state.get("username", ""))

    treatment_type = st.selectbox("Treatment", ["General Treatment", "Chronic Disease", "Emergency", "Post Surgery"])

    st.divider()

    # --- Medicines (from catalog) ---
    st.markdown("##### Medicines")
    st.caption("Select medicines from the catalog. Admin manages the available medicines.")

    # Group medicines by category for easier selection
    categories = {}
    for m in all_medicines:
        cat = m.get("category", "Other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(m["name"])

    selected_medicines = st.multiselect(
        "Choose Medicines",
        medicine_names,
        placeholder="Search and select medicines..."
    )

    # Show selected medicine details
    if selected_medicines:
        st.markdown("**Selected:**")
        for med_name in selected_medicines:
            info = med_lookup.get(med_name, {})
            strength = info.get("strength", "")
            form = info.get("dosage_form", "")
            cat = info.get("category", "")
            st.markdown(f"• **{med_name}** — {strength} {form} _{cat}_")

    medicines_str = ", ".join(selected_medicines)

    # Interaction check
    if len(selected_medicines) > 1:
        warnings = check_interactions(medicines_str)
        if warnings:
            for w in warnings:
                st.warning(f"⚠️ {w}")

    dosage = st.text_input("Dosage Instructions", placeholder="e.g. Twice daily after meals for 7 days")

    st.divider()

    # --- Generate ---
    generate = st.button("Generate Prescription", use_container_width=True)

    if generate:
        if not patient_name or not doctor_name or not selected_medicines:
            st.error("Fill in patient, doctor, and select at least one medicine.")
            return

        # Create patient if new
        if patient_mode == "New Patient":
            existing = get_patient_by_name(patient_name)
            if not existing:
                patient_id = create_patient({
                    "name": patient_name, "age": patient_age,
                    "phone": patient_phone, "caregiver": caregiver
                })
            else:
                patient_id = str(existing["_id"])
        else:
            sel = get_patient_by_name(patient_name)
            patient_id = str(sel["_id"]) if sel else None

        prescription_id = "RX" + str(uuid.uuid4().hex)[:6]

        prescription_data = {
            "prescription_id": prescription_id,
            "patient_name": patient_name,
            "patient_id": patient_id,
            "caregiver": caregiver,
            "doctor_name": doctor_name,
            "medicines": medicines_str,
            "dosage": dosage,
            "treatment_type": treatment_type,
            "generated_date": datetime.now().isoformat(),
        }

        qr_json = json.dumps(prescription_data, default=str)
        qr_path = generate_qr(qr_json, prescription_id)

        qr_url = None
        if cloudinary_configured():
            cloud_result = upload_qr_code(qr_path, prescription_id)
            if cloud_result:
                qr_url = cloud_result["url"]
                prescription_data["qr_code_url"] = qr_url

        insert_prescription(prescription_data)

        create_order({
            "prescription_id": prescription_id,
            "patient_name": patient_name,
            "patient_id": patient_id,
            "doctor_name": doctor_name,
            "medicines": medicines_str,
            "dosage": dosage,
            "treatment_type": treatment_type,
            "status": "pending",
            "pharmacy_notes": "",
            "created_by": doctor_name,
        })

        if patient_id:
            for med_name in selected_medicines:
                info = med_lookup.get(med_name, {})
                add_medication_to_patient(patient_id, {
                    "name": med_name,
                    "dosage": dosage,
                    "strength": info.get("strength", ""),
                    "dosage_form": info.get("dosage_form", ""),
                    "prescribed_by": doctor_name,
                    "prescription_id": prescription_id,
                    "treatment_type": treatment_type,
                    "status": "active",
                })

        # Result
        st.success(f"Prescription {prescription_id} created. Order sent to pharmacy.")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"""
            | Field | Value |
            |-------|-------|
            | **ID** | {prescription_id} |
            | **Patient** | {patient_name} |
            | **Doctor** | {doctor_name} |
            | **Treatment** | {treatment_type} |
            | **Medicines** | {medicines_str} |
            | **Dosage** | {dosage or 'As directed'} |
            | **Caregiver** | {caregiver or '—'} |
            """)

        with col2:
            if qr_url:
                st.image(qr_url, width=180, caption="QR Code")
            else:
                st.image(qr_path, width=180, caption="QR Code")