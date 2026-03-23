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
    st.markdown("""
    <div style="margin-bottom: 16px; padding: 10px 0 6px 0; border-bottom: 1px solid #1a1a1a;">
        <span style="color:#888; font-size:11px; font-weight:600; letter-spacing:1.5px; text-transform:uppercase;">Order Details</span>
    </div>
    """, unsafe_allow_html=True)

    for order in orders:
        order_id = str(order.get("_id", ""))
        status = order.get("status", "pending")
        presc_id = order.get("prescription_id", "")
        patient = order.get("patient_name", "")

        status_badge = {"pending": "🟡", "processing": "🔵", "dispensed": "🟣", "completed": "🟢", "cancelled": "🔴"}.get(status, "⚪")
        label = f"{status_badge}  {presc_id}   ·   {patient}   ·   {status.upper()}"

        with st.expander(label):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Prescription:** {presc_id}")
                st.write(f"**Patient:** {patient}")
                st.write(f"**Doctor:** {order.get('doctor_name', '')}")
                st.write(f"**Treatment:** {order.get('treatment_type', '')}")

            with col2:
                st.write(f"**Medicines:** {order.get('medicines', '')}")
                st.write(f"**Dosage:** {order.get('dosage', '')}")
                st.write(f"**Status:** {status.upper()}")
                st.write(f"**Created:** {str(order.get('created_at', ''))[:16]}")
                if order.get("updated_by"):
                    st.write(f"**Updated by:** {order.get('updated_by')}")

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
