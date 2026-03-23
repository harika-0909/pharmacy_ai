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

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Analytics", "Medicine Catalog", "Users", "Prescriptions", "Orders", "🚨 Alerts"
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
    with tab6:
        show_alert_management()


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


def show_alert_management():
    """Admin view: full alert log + inventory restock + dose schedules."""
    from modules.utils.db import (
        get_alert_log, acknowledge_alert, clear_acked_alerts,
        restock_item, get_all_dose_schedules, get_inventory,
        get_low_stock_items
    )
    username = st.session_state.get("username", "admin")

    inner_tabs = st.tabs(["📋 Alert Log", "📦 Restock Manager", "📅 All Dose Schedules"])

    # ── Alert Log ──
    with inner_tabs[0]:
        st.markdown("##### System Alert Log")
        col1, col2, col3 = st.columns([1,1,4])
        with col1:
            show_all = st.checkbox("Show acknowledged", key="admin_log_all")
        with col2:
            if st.button("🗑️ Clear Acknowledged", key="admin_clear_acked"):
                clear_acked_alerts()
                st.success("Cleared acknowledged alerts.")
                st.rerun()

        logs = get_alert_log(limit=200, only_unacked=not show_all)
        if not logs:
            st.info("No alert log entries.")
        else:
            st.caption(f"{len(logs)} entries")
            sev_icons = {"critical":"🔴","warning":"🟡","info":"🔵","high":"🟣","success":"🟢"}
            for entry in logs:
                eid    = str(entry.get("_id",""))
                sev    = entry.get("severity","info")
                msg    = entry.get("message","—")
                acked  = entry.get("acknowledged", False)
                ack_by = entry.get("ack_by","")
                ts     = str(entry.get("created_at",""))[:16]
                icon   = sev_icons.get(sev,"⚪")
                c1, c2 = st.columns([7,1])
                with c1:
                    ack_txt = f"  ✓ {ack_by}" if acked else ""
                    st.markdown(
                        f"{icon} `{sev.upper()}` **{msg}**{ack_txt} — _{ts}_"
                    )
                with c2:
                    if not acked:
                        if st.button("✓", key=f"adm_ack_{eid}"):
                            acknowledge_alert(eid, username)
                            st.rerun()

    # ── Restock Manager ──
    with inner_tabs[1]:
        st.markdown("##### Inventory Restock Manager")
        inventory = get_inventory()
        low  = get_low_stock_items(15)
        low_names = {i["medicine_name"] for i in low}

        if not inventory:
            st.info("No inventory data.")
        else:
            df = pd.DataFrame([{
                "Medicine": i.get("medicine_name",""),
                "Stock":    i.get("stock",0),
                "Status":   "🔴 Critical" if i.get("stock",0)<=5
                             else ("🟡 Low" if i.get("stock",0)<=15 else "🟢 OK"),
                "Last Restocked": str(i.get("last_restocked_at",""))[:16] or "—",
                "By": i.get("last_restocked_by","—"),
            } for i in inventory])
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("##### Quick Restock")
            med_names = [i["medicine_name"] for i in inventory]
            col1, col2, col3 = st.columns([3,1,1])
            with col1:
                sel_med = st.selectbox("Medicine", med_names, key="admin_restock_med")
            with col2:
                qty = st.number_input("Units", min_value=1, value=50, key="admin_restock_qty")
            with col3:
                st.write("")
                if st.button("📦 Restock", key="admin_restock_btn"):
                    ok = restock_item(sel_med, qty, username)
                    if ok:
                        st.success(f"✅ Restocked {sel_med} +{qty}")
                        st.rerun()
                    else:
                        st.error("Item not found.")

    # ── Dose Schedules ──
    with inner_tabs[2]:
        st.markdown("##### All Custom Dose Schedules")
        schedules = get_all_dose_schedules()
        if not schedules:
            st.info("No schedules configured yet.")
        else:
            rows = [{"Caregiver": s.get("caregiver",""),
                     "Patient":   s.get("patient",""),
                     "Medicine":  s.get("medicine",""),
                     "Times":     " · ".join(s.get("times",[])),
                     "Updated":   str(s.get("updated_at",""))[:16]} for s in schedules]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)