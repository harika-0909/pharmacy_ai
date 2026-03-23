"""
Orders Module — Clean labels, no broken emoji
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from modules.utils.db import (
    get_all_orders, get_orders_by_status, update_order_status,
    get_order_by_prescription, update_order
)


def show():
    st.title("Orders")

    role = st.session_state.get("role", "")
    username = st.session_state.get("username", "")

    col1, col2 = st.columns([1, 3])
    with col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "pending", "processing", "dispensed", "completed", "cancelled"],
            key="order_status_filter"
        )

    if status_filter == "All":
        orders = get_all_orders()
    else:
        orders = get_orders_by_status(status_filter)

    if not orders:
        st.info("No orders found.")
        return

    # Metrics
    all_orders = get_all_orders()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pending", len([o for o in all_orders if o.get("status") == "pending"]))
    col2.metric("Processing", len([o for o in all_orders if o.get("status") == "processing"]))
    col3.metric("Dispensed", len([o for o in all_orders if o.get("status") == "dispensed"]))
    col4.metric("Completed", len([o for o in all_orders if o.get("status") == "completed"]))

    st.divider()

    # Table
    table_data = []
    for order in orders:
        meds = order.get("medicines", "")
        if len(meds) > 40:
            meds = meds[:40] + "..."
        table_data.append({
            "ID": order.get("prescription_id", ""),
            "Patient": order.get("patient_name", ""),
            "Doctor": order.get("doctor_name", ""),
            "Medicines": meds,
            "Status": order.get("status", "pending").upper(),
            "Date": str(order.get("created_at", ""))[:10],
        })

    st.dataframe(pd.DataFrame(table_data), use_container_width=True)

    st.divider()

    # Order Details — select-based UI (no expander = no icon overlap)
    st.markdown("""
    <div style="margin-bottom: 12px; padding: 10px 0 6px 0; border-bottom: 1px solid #1a1a1a;">
        <span style="color:#888; font-size:11px; font-weight:600; letter-spacing:1.5px; text-transform:uppercase;">Order Details</span>
    </div>
    """, unsafe_allow_html=True)

    status_icons = {"pending": "🟡", "processing": "🔵", "dispensed": "🟣", "completed": "🟢", "cancelled": "🔴"}
    options = []
    for order in orders:
        status = order.get("status", "pending")
        presc_id = order.get("prescription_id", "")
        patient = order.get("patient_name", "")
        icon = status_icons.get(status, "⚪")
        options.append((f"{icon} {presc_id} · {patient} · {status.upper()}", order))

    selected_label = st.selectbox(
        "Select an order to view details",
        options=[o[0] for o in options],
        key="order_detail_select",
        label_visibility="collapsed"
    )

    if selected_label:
        idx = next(i for i, (lbl, _) in enumerate(options) if lbl == selected_label)
        order = options[idx][1]
        order_id = str(order.get("_id", ""))
        status = order.get("status", "pending")
        presc_id = order.get("prescription_id", "")
        patient = order.get("patient_name", "")

        # Detail card
        st.markdown(f"""
        <div style="background:#0d0d0d; border:1px solid #1e1e1e; border-radius:10px; padding:20px; margin-top:12px;">
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:16px;">
                <div>
                    <p style="color:#555;font-size:11px;text-transform:uppercase;margin:0 0 4px 0;">Prescription</p>
                    <p style="color:#fff;font-weight:600;margin:0;">{presc_id}</p>
                    <p style="color:#555;font-size:11px;text-transform:uppercase;margin:12px 0 4px 0;">Patient</p>
                    <p style="color:#e0e0e0;margin:0;">{patient}</p>
                    <p style="color:#555;font-size:11px;text-transform:uppercase;margin:12px 0 4px 0;">Doctor</p>
                    <p style="color:#e0e0e0;margin:0;">{order.get('doctor_name', '—')}</p>
                    <p style="color:#555;font-size:11px;text-transform:uppercase;margin:12px 0 4px 0;">Treatment</p>
                    <p style="color:#e0e0e0;margin:0;">{order.get('treatment_type', '—')}</p>
                </div>
                <div>
                    <p style="color:#555;font-size:11px;text-transform:uppercase;margin:0 0 4px 0;">Medicines</p>
                    <p style="color:#e0e0e0;margin:0;">{order.get('medicines', '—')}</p>
                    <p style="color:#555;font-size:11px;text-transform:uppercase;margin:12px 0 4px 0;">Dosage</p>
                    <p style="color:#e0e0e0;margin:0;">{order.get('dosage', '—')}</p>
                    <p style="color:#555;font-size:11px;text-transform:uppercase;margin:12px 0 4px 0;">Status · Created</p>
                    <p style="color:#e0e0e0;margin:0;">{status.upper()} · {str(order.get('created_at', ''))[:16]}</p>
                    {('<p style="color:#555;font-size:11px;margin-top:8px;">Updated by: ' + str(order.get('updated_by', '')) + '</p>') if order.get('updated_by') else ''}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if order.get("pharmacy_notes"):
            st.info(f"Notes: {order['pharmacy_notes']}")

        if role in ["pharmacy", "admin"]:
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button("Processing", key=f"op_{order_id}"):
                    update_order_status(presc_id, "processing", username)
                    st.rerun()
            with c2:
                if st.button("Dispensed", key=f"od_{order_id}"):
                    update_order_status(presc_id, "dispensed", username)
                    st.rerun()
            with c3:
                if st.button("Complete", key=f"oc_{order_id}"):
                    update_order_status(presc_id, "completed", username)
                    st.rerun()
            with c4:
                if st.button("Cancel", key=f"ox_{order_id}"):
                    update_order_status(presc_id, "cancelled", username)
                    st.rerun()
