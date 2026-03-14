"""
Patient Management — Minimalist
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from modules.utils.db import (
    create_patient, get_all_patients, get_patient,
    update_patient, add_medication_to_patient,
    remove_medication_from_patient, search_patients,
    get_prescriptions_by_patient, get_all_medicines
)


def show():
    st.title("👤 Patients")

    tab1, tab2, tab3 = st.tabs(["All Patients", "Add Patient", "Search"])

    with tab1:
        show_all()
    with tab2:
        show_add()
    with tab3:
        show_search()


def show_all():
    patients = get_all_patients()
    if not patients:
        st.info("No patients yet. Add one to get started.")
        return

    col1, col2 = st.columns(2)
    col1.metric("Total", len(patients))
    with_meds = len([p for p in patients if p.get("medications")])
    col2.metric("With Medications", with_meds)

    st.divider()

    # Get medicine catalog for adding meds
    medicine_catalog = get_all_medicines()
    med_names = [m["name"] for m in medicine_catalog]

    for patient in patients:
        pid = str(patient["_id"])
        name = patient.get("name", "Unknown")
        age = patient.get("age", "—")
        phone = patient.get("phone", "—")
        meds = patient.get("medications", [])
        active = [m for m in meds if m.get("status") == "active"]

        with st.expander(f"{name} · Age {age} · {len(active)} active meds"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Info**")
                st.write(f"Name: {name}")
                st.write(f"Age: {age}")
                st.write(f"Phone: {phone}")
                st.write(f"Caregiver: {patient.get('caregiver', '—')}")

            with col2:
                st.markdown("**Active Medications**")
                if active:
                    for m in active:
                        st.write(f"• {m.get('name', '')} — {m.get('dosage', '')}")
                else:
                    st.caption("None")

            st.markdown("---")

            # Edit
            ecol1, ecol2 = st.columns(2)
            with ecol1:
                new_phone = st.text_input("Phone", value=phone, key=f"ph_{pid}")
                new_cg = st.text_input("Caregiver", value=patient.get("caregiver", ""), key=f"cg_{pid}")
                if st.button("Save", key=f"sv_{pid}"):
                    update_patient(pid, {"phone": new_phone, "caregiver": new_cg})
                    st.success("Updated")
                    st.rerun()

            with ecol2:
                st.markdown("**Add Medicine**")
                if med_names:
                    new_med = st.selectbox("Medicine", med_names, key=f"am_{pid}")
                    new_dose = st.text_input("Dosage", key=f"ad_{pid}", placeholder="e.g. 500mg twice daily")
                else:
                    new_med = st.text_input("Medicine Name", key=f"am_{pid}")
                    new_dose = st.text_input("Dosage", key=f"ad_{pid}")

                if st.button("Add", key=f"ab_{pid}"):
                    if new_med:
                        add_medication_to_patient(pid, {
                            "name": new_med, "dosage": new_dose,
                            "prescribed_by": st.session_state.get("username", ""),
                            "status": "active"
                        })
                        st.success(f"Added {new_med}")
                        st.rerun()

            if active:
                st.markdown("---")
                rem = st.selectbox("Remove medication", [m.get("name") for m in active], key=f"rm_{pid}")
                if st.button("Remove", key=f"rb_{pid}"):
                    remove_medication_from_patient(pid, rem)
                    st.rerun()

            # History
            st.markdown("---")
            st.markdown("**Prescription History**")
            presc = get_prescriptions_by_patient(name)
            if presc:
                for p in presc:
                    st.caption(f"{p.get('prescription_id')} · Dr. {p.get('doctor_name')} · {p.get('medicines')} · {str(p.get('created_at',''))[:10]}")
            else:
                st.caption("No history")


def show_add():
    st.markdown("##### Register Patient")

    with st.form("add_patient"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name *")
            age = st.number_input("Age", min_value=0, max_value=150, value=25)
            phone = st.text_input("Phone")
        with col2:
            caregiver = st.text_input("Caregiver")
            blood = st.selectbox("Blood Group", ["", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
            notes = st.text_area("Medical Notes", placeholder="Allergies, conditions...")

        if st.form_submit_button("Register", use_container_width=True):
            if name:
                create_patient({
                    "name": name, "age": age, "phone": phone,
                    "caregiver": caregiver, "blood_group": blood,
                    "medical_notes": notes, "medications": [], "medical_history": []
                })
                st.success(f"Patient '{name}' registered")
                st.balloons()
            else:
                st.error("Name is required")


def show_search():
    query = st.text_input("Search", placeholder="Name or phone")
    if query:
        results = search_patients(query)
        if results:
            st.success(f"{len(results)} found")
            for p in results:
                active = [m for m in p.get("medications", []) if m.get("status") == "active"]
                with st.expander(f"{p.get('name')} · Age {p.get('age', '—')}"):
                    st.write(f"Phone: {p.get('phone', '—')}")
                    st.write(f"Caregiver: {p.get('caregiver', '—')}")
                    if active:
                        for m in active:
                            st.write(f"• {m.get('name')} — {m.get('dosage', '')}")
        else:
            st.info("No results")
