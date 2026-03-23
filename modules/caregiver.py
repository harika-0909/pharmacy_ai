"""
Caregiver Dashboard - View prescriptions and QR codes for assigned patients
"""
import streamlit as st
import json

from modules.utils.qr_scanner import scan_qr
from modules.utils.db import get_prescriptions_by_caregiver, get_prescription_by_id
from modules.alerts import show_caregiver_alerts


def show():
    st.markdown("## 👨‍👩‍👦 Caregiver Dashboard")

    current_caregiver = st.session_state.get('username', '')

    st.info(f"🔐 **Welcome {current_caregiver}** — You can view prescriptions assigned to you.")

    tab1, tab2, tab3 = st.tabs(["🚨 Alerts & Reminders", "📋 My Prescriptions", "📱 Scan QR Code"])

    with tab1:
        show_caregiver_alerts(current_caregiver)

    with tab2:
        show_my_prescriptions(current_caregiver)

    with tab3:
        show_qr_scanner(current_caregiver)


def show_my_prescriptions(caregiver_name):
    """Show prescriptions assigned to this caregiver."""
    prescriptions = get_prescriptions_by_caregiver(caregiver_name)

    if not prescriptions:
        st.warning("📋 No prescriptions found for you yet.")
        st.info("Doctors will assign prescriptions to you when they create them.")
        return

    st.success(f"Found {len(prescriptions)} prescriptions assigned to you")

    # Summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Prescriptions", len(prescriptions))
    with col2:
        patients = set(p.get("patient_name", "") for p in prescriptions)
        st.metric("Patients", len(patients))
    with col3:
        doctors = set(p.get("doctor_name", "") for p in prescriptions)
        st.metric("Doctors", len(doctors))

    st.divider()

    # Display prescriptions
    for presc in prescriptions:
        presc_id = presc.get("prescription_id", "N/A")
        patient = presc.get("patient_name", "Unknown")
        doctor = presc.get("doctor_name", "Unknown")
        medicines = presc.get("medicines", "N/A")

        with st.expander(f"{presc_id}  —  Patient: {patient}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Patient Name:**", patient)
                st.write("**Doctor:**", doctor)
                st.write("**Medicines:**", medicines)

            with col2:
                st.write("**Prescription ID:**", presc_id)
                st.write("**Treatment:**", presc.get("treatment_type", "N/A"))
                st.write("**Dosage:**", presc.get("dosage", "N/A"))

            if presc.get("qr_code_url"):
                st.image(presc["qr_code_url"], width=150, caption="Prescription QR")

            created = presc.get("created_at", "")
            if created:
                st.write("**Date:**", str(created)[:16])

            # Adherence tracking
            st.markdown("---")
            st.markdown("##### 📊 Adherence Tracking")
            adherence = st.slider(
                "Adherence Score",
                0, 100, 85,
                key=f"adh_{presc_id}"
            )
            st.progress(adherence / 100)

            if adherence < 70:
                st.warning("⚠️ Low adherence! Consider setting reminders.")
            elif adherence < 85:
                st.info("📊 Moderate adherence. Keep tracking.")
            else:
                st.success("✅ Great adherence!")


def show_qr_scanner(caregiver_name):
    """Scan QR codes to view prescription details."""
    st.markdown("### 📱 Scan Prescription QR Code")

    uploaded_file = st.file_uploader(
        "Upload QR Code Image",
        type=['png', 'jpg', 'jpeg'],
        key="cg_qr_upload"
    )

    if uploaded_file:
        with open("temp_qr.png", "wb") as f:
            f.write(uploaded_file.read())

        qr_data = scan_qr("temp_qr.png")

        if qr_data:
            try:
                prescription_data = json.loads(qr_data)
                st.success("✅ QR Scanned Successfully")

                # Check if this belongs to the caregiver
                qr_caregiver = prescription_data.get("caregiver", "").lower()
                if qr_caregiver != caregiver_name.lower():
                    st.error("❌ Access Denied: This prescription is not assigned to you.")
                    return

                # Display details
                st.markdown("### 🧾 Prescription Details")

                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Patient:**", prescription_data.get("patient_name", "N/A"))
                    st.write("**Doctor:**", prescription_data.get("doctor_name", "N/A"))
                    st.write("**Medicines:**", prescription_data.get("medicines", "N/A"))

                with col2:
                    st.write("**Prescription ID:**", prescription_data.get("prescription_id", "N/A"))
                    st.write("**Treatment:**", prescription_data.get("treatment_type", "N/A"))
                    st.write("**Dosage:**", prescription_data.get("dosage", "N/A"))

                if prescription_data.get("generated_date"):
                    st.write("**Date:**", prescription_data["generated_date"])

                st.success("✅ Prescription verified!")

            except json.JSONDecodeError:
                # Try as prescription ID
                st.info(f"QR Data: {qr_data}")
                result = get_prescription_by_id(qr_data)
                if result:
                    st.write("**Patient:**", result.get("patient_name", "N/A"))
                    st.write("**Doctor:**", result.get("doctor_name", "N/A"))
                    st.write("**Medicines:**", result.get("medicines", "N/A"))
                else:
                    st.error("❌ Prescription not found")
        else:
            st.error("❌ Could not read QR code")