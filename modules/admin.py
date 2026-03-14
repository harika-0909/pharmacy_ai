"""
Admin Panel — User & Medicine Catalog Management
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from modules.utils.db import (
    get_all_users, get_all_prescriptions, get_all_orders,
    get_all_patients, delete_user, get_collection,
    get_inventory, get_low_stock_items,
    get_all_medicines, add_medicine, update_medicine, delete_medicine,
    seed_medicine_catalog
)
from modules.utils.jwt_auth import hash_password
from modules.utils.db import create_user


def show():
    st.title("Admin Panel")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Analytics", "Medicine Catalog", "Users", "Prescriptions", "Orders"
    ])

    with tab1:
        show_analytics()
    with tab2:
        show_medicine_catalog()
    with tab3:
        show_user_management()
    with tab4:
        show_prescriptions()
    with tab5:
        show_orders_overview()


def show_analytics():
    prescriptions = get_all_prescriptions()
    orders = get_all_orders()
    patients = get_all_patients()
    users = get_all_users()
    medicines = get_all_medicines()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Prescriptions", len(prescriptions))
    col2.metric("Patients", len(patients))
    col3.metric("Orders", len(orders))
    col4.metric("Users", len(users))
    col5.metric("Medicines", len(medicines))

    st.divider()

    if orders:
        st.markdown("##### Order Status")
        status_counts = {}
        for o in orders:
            s = o.get("status", "pending")
            status_counts[s] = status_counts.get(s, 0) + 1
        st.bar_chart(pd.DataFrame(list(status_counts.items()), columns=["Status", "Count"]).set_index("Status"))

    if prescriptions:
        st.markdown("##### Top Medicines")
        all_meds = []
        for p in prescriptions:
            meds = p.get("medicines", "")
            if meds:
                all_meds.extend([m.strip() for m in meds.split(",")])
        if all_meds:
            st.bar_chart(pd.Series(all_meds).value_counts().head(15))

    low_stock = get_low_stock_items()
    if low_stock:
        st.markdown("##### Low Stock Alerts")
        for item in low_stock:
            st.warning(f"{item.get('medicine_name')} — {item.get('stock', 0)} units left")


def show_medicine_catalog():
    """Admin manages the medicine catalog that doctors pick from."""
    st.markdown("##### Medicine Catalog")
    st.caption("Add medicines here. Doctors will select from this list when creating prescriptions.")

    # Add medicine form
    with st.expander("➕ Add New Medicine", expanded=False):
        with st.form("add_medicine_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Medicine Name *", placeholder="e.g. Paracetamol")
                category = st.selectbox("Category", [
                    "Pain Relief", "Antibiotic", "Diabetes", "Cardiovascular",
                    "Gastrointestinal", "Respiratory", "Antihistamine",
                    "Psychiatric", "Supplement", "Dermatology", "Other"
                ])
            with col2:
                dosage_form = st.selectbox("Dosage Form", [
                    "Tablet", "Capsule", "Syrup", "Injection", "Inhaler",
                    "Cream", "Drops", "Powder", "Patch", "Other"
                ])
                strength = st.text_input("Strength", placeholder="e.g. 500mg")

            if st.form_submit_button("Add Medicine", use_container_width=True):
                if name:
                    success, msg = add_medicine({
                        "name": name.strip(),
                        "category": category,
                        "dosage_form": dosage_form,
                        "strength": strength,
                    })
                    if success:
                        st.success(f"{name} added to catalog")
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("Medicine name is required")

    # Display existing medicines
    medicines = get_all_medicines()

    if medicines:
        st.markdown(f"**{len(medicines)} medicines in catalog**")

        # Group by category
        categories = {}
        for med in medicines:
            cat = med.get("category", "Other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(med)

        for cat, meds in sorted(categories.items()):
            with st.expander(f"{cat} ({len(meds)})"):
                for med in meds:
                    med_id = str(med["_id"])
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    with col1:
                        st.write(f"**{med['name']}**")
                    with col2:
                        st.write(med.get("dosage_form", ""))
                    with col3:
                        st.write(med.get("strength", ""))
                    with col4:
                        if st.button("✕", key=f"del_med_{med_id}"):
                            delete_medicine(med_id)
                            st.rerun()
    else:
        st.info("No medicines in catalog. Add some above or seed defaults.")
        if st.button("Seed Default Medicines"):
            seed_medicine_catalog()
            st.rerun()


def show_user_management():
    st.markdown("##### User Management")

    with st.expander("➕ Add User", expanded=False):
        with st.form("admin_add_user"):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
            with col2:
                new_role = st.selectbox("Role", ["doctor", "pharmacy", "caregiver", "admin"])
            if st.form_submit_button("Create User", use_container_width=True):
                if new_username and new_password:
                    hashed = hash_password(new_password)
                    success, msg = create_user(new_username, hashed, new_role)
                    if success:
                        st.success(f"User '{new_username}' created")
                        st.rerun()
                    else:
                        st.error(msg)

    users = get_all_users()
    if users:
        data = [{"Username": u.get("username"), "Role": u.get("role", "").upper(), "Created": str(u.get("created_at", ""))[:10]} for u in users]
        st.dataframe(pd.DataFrame(data), use_container_width=True)

        st.markdown("---")
        usernames = [u.get("username") for u in users if u.get("username") != "admin"]
        if usernames:
            to_delete = st.selectbox("Delete user", usernames)
            if st.button("Delete"):
                delete_user(to_delete)
                st.success(f"Deleted {to_delete}")
                st.rerun()


def show_prescriptions():
    st.markdown("##### All Prescriptions")
    prescriptions = get_all_prescriptions()
    if not prescriptions:
        st.info("No prescriptions yet.")
        return

    data = [{
        "ID": p.get("prescription_id"), "Patient": p.get("patient_name"),
        "Doctor": p.get("doctor_name"), "Medicines": p.get("medicines"),
        "Date": str(p.get("created_at", ""))[:10]
    } for p in prescriptions]
    st.dataframe(pd.DataFrame(data), use_container_width=True)


def show_orders_overview():
    st.markdown("##### All Orders")
    orders = get_all_orders()
    if not orders:
        st.info("No orders yet.")
        return

    data = [{
        "Prescription": o.get("prescription_id"), "Patient": o.get("patient_name"),
        "Doctor": o.get("doctor_name"), "Status": o.get("status", "").upper(),
        "Notes": o.get("pharmacy_notes", ""), "Date": str(o.get("created_at", ""))[:16]
    } for o in orders]
    st.dataframe(pd.DataFrame(data), use_container_width=True)