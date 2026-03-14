"""
Pharmacy Verification & Order Management — Minimalist
"""
import streamlit as st
import json
from datetime import datetime

from modules.utils.qr_scanner import scan_qr
from modules.utils.db import (
    get_prescription_by_id, get_all_orders,
    get_orders_by_status, update_order_status,
    get_order_by_prescription, get_inventory,
    update_order
)


def show():
    st.title("💊 Pharmacy")

    tab1, tab2, tab3 = st.tabs(["Verify", "Orders", "Inventory"])

    with tab1:
        show_verification()
    with tab2:
        show_orders()
    with tab3:
        show_inventory()


def show_verification():
    option = st.radio("", ["Prescription ID", "QR Code"], horizontal=True, label_visibility="collapsed")

    if option == "Prescription ID":
        prescription_id = st.text_input("Prescription ID", placeholder="e.g. RX12345")
        if st.button("Verify") and prescription_id:
            result = get_prescription_by_id(prescription_id)
            if result:
                st.success("Valid prescription")
                display_prescription(result)
            else:
                st.error("Not found")

    else:
        uploaded = st.file_uploader("Upload QR Image", type=['png', 'jpg', 'jpeg'])
        if uploaded:
            with open("temp_qr.png", "wb") as f:
                f.write(uploaded.read())
            qr_data = scan_qr("temp_qr.png")
            if qr_data:
                try:
                    data = json.loads(qr_data)
                    st.success("QR verified")
                    display_prescription_qr(data)
                except json.JSONDecodeError:
                    result = get_prescription_by_id(qr_data)
                    if result:
                        display_prescription(result)
                    else:
                        st.error("Not found")
            else:
                st.error("Could not read QR")


def show_orders():
    col1, col2 = st.columns([1, 3])
    with col1:
        status_filter = st.selectbox("Status", ["All", "pending", "processing", "dispensed", "completed", "cancelled"])

    if status_filter == "All":
        orders = get_all_orders()
    else:
        orders = get_orders_by_status(status_filter)

    if not orders:
        st.info("No orders found.")
        return

    all_orders = get_all_orders()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pending", len([o for o in all_orders if o.get("status") == "pending"]))
    col2.metric("Processing", len([o for o in all_orders if o.get("status") == "processing"]))
    col3.metric("Dispensed", len([o for o in all_orders if o.get("status") == "dispensed"]))
    col4.metric("Completed", len([o for o in all_orders if o.get("status") == "completed"]))

    st.divider()

    for order in orders:
        status = order.get("status", "pending")
        order_id = str(order.get("_id", ""))

        with st.expander(f"{order.get('prescription_id', '')} · {order.get('patient_name', '')} · {status.upper()}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Patient:** {order.get('patient_name', '')}")
                st.write(f"**Doctor:** {order.get('doctor_name', '')}")
                st.write(f"**Treatment:** {order.get('treatment_type', '')}")
            with col2:
                st.write(f"**Medicines:** {order.get('medicines', '')}")
                st.write(f"**Dosage:** {order.get('dosage', '')}")
                st.write(f"**Created:** {str(order.get('created_at', ''))[:16]}")

            st.markdown("---")
            current_notes = order.get("pharmacy_notes", "")
            notes = st.text_area("Notes", value=current_notes, key=f"n_{order_id}")
            current_meds = order.get("medicines", "")
            edited_meds = st.text_input("Edit Medicines", value=current_meds, key=f"m_{order_id}")

            c1, c2, c3, c4 = st.columns(4)
            username = st.session_state.get("username", "pharmacy")

            with c1:
                if st.button("Processing", key=f"p_{order_id}"):
                    update_order_status(order.get("prescription_id"), "processing", username)
                    _save_changes(order_id, notes, current_notes, edited_meds, current_meds)
                    st.rerun()
            with c2:
                if st.button("Dispensed", key=f"d_{order_id}"):
                    update_order_status(order.get("prescription_id"), "dispensed", username)
                    _save_changes(order_id, notes, current_notes, edited_meds, current_meds)
                    st.rerun()
            with c3:
                if st.button("Complete", key=f"c_{order_id}"):
                    update_order_status(order.get("prescription_id"), "completed", username)
                    _save_changes(order_id, notes, current_notes, edited_meds, current_meds)
                    st.rerun()
            with c4:
                if st.button("Save", key=f"s_{order_id}"):
                    _save_changes(order_id, notes, current_notes, edited_meds, current_meds)
                    st.success("Saved")
                    st.rerun()


def _save_changes(order_id, notes, old_notes, meds, old_meds):
    data = {}
    if notes != old_notes:
        data["pharmacy_notes"] = notes
    if meds != old_meds:
        data["medicines"] = meds
    if data:
        update_order(order_id, data)


def show_inventory():
    import pandas as pd
    inventory = get_inventory()
    if not inventory:
        from modules.alerts import INVENTORY
        from modules.utils.db import seed_inventory
        seed_inventory(INVENTORY)
        inventory = get_inventory()

    if not inventory:
        st.info("No inventory data.")
        return

    data = [{
        "Medicine": i.get("medicine_name", ""),
        "Stock": i.get("stock", 0),
        "Status": "Low" if i.get("stock", 0) <= 15 else "OK",
    } for i in inventory]

    st.dataframe(pd.DataFrame(data), use_container_width=True)

    col1, col2 = st.columns(2)
    col1.metric("Total Items", len(inventory))
    low = len([i for i in inventory if i.get("stock", 0) <= 15])
    col2.metric("Low Stock", low)


def display_prescription(result):
    st.markdown(f"""
    | Field | Value |
    |-------|-------|
    | **Patient** | {result.get('patient_name', '')} |
    | **Doctor** | {result.get('doctor_name', '')} |
    | **Medicines** | {result.get('medicines', '')} |
    | **Dosage** | {result.get('dosage', '')} |
    | **Caregiver** | {result.get('caregiver', '')} |
    | **ID** | {result.get('prescription_id', '')} |
    """)
    qr = result.get("qr_code_url")
    if qr:
        st.image(qr, width=150)
    order = get_order_by_prescription(result.get("prescription_id"))
    if order:
        st.write(f"**Order Status:** {order.get('status', '').upper()}")


def display_prescription_qr(data):
    st.markdown(f"""
    | Field | Value |
    |-------|-------|
    | **Patient** | {data.get('patient_name', '')} |
    | **Doctor** | {data.get('doctor_name', '')} |
    | **Medicines** | {data.get('medicines', '')} |
    | **ID** | {data.get('prescription_id', '')} |
    """)
    presc_id = data.get("prescription_id")
    if presc_id:
        order = get_order_by_prescription(presc_id)
        if order:
            st.write(f"**Order Status:** {order.get('status', '').upper()}")
        if st.button("Dispense"):
            update_order_status(presc_id, "dispensed", st.session_state.get("username", "pharmacy"))
            st.success("Dispensed")
            st.rerun()