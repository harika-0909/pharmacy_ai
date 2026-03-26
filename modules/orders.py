"""
Orders Module — Clean labels, no broken emoji
"""
from html import escape
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
    st.markdown(
        '<div style="margin-bottom:12px;padding:10px 0 6px 0;border-bottom:1px solid rgba(72,184,206,0.45);">'
        '<span style="color:#2d5c6a;font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;">'
        "Order Details</span></div>",
        unsafe_allow_html=True,
    )

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

        # Detail card — no indented HTML (Markdown treats 4+ spaces as code → stray </div> on screen)
        pid_e = escape(str(presc_id))
        pat_e = escape(str(patient))
        doc_e = escape(str(order.get("doctor_name", "—")))
        tr_e = escape(str(order.get("treatment_type", "—")))
        med_e = escape(str(order.get("medicines", "—")))
        dose_e = escape(str(order.get("dosage", "—")))
        stat_e = escape(str(status.upper()))
        dt_e = escape(str(order.get("created_at", ""))[:16])
        upd_html = ""
        if order.get("updated_by"):
            upd_html = (
                '<p style="color:#2d5c6a;font-size:11px;margin-top:8px;">Updated by: '
                f"{escape(str(order.get('updated_by', '')))}</p>"
            )
        card = (
            '<div style="background:rgba(255,255,255,0.9);border:1px solid rgba(72,184,206,0.55);'
            'border-radius:10px;padding:20px;margin-top:12px;box-shadow:0 2px 12px rgba(13,76,92,0.08);">'
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:16px;">'
            "<div>"
            '<p style="color:#2d5c6a;font-size:11px;text-transform:uppercase;margin:0 0 4px 0;">Prescription</p>'
            f'<p style="color:#0a3d47;font-weight:600;margin:0;">{pid_e}</p>'
            '<p style="color:#2d5c6a;font-size:11px;text-transform:uppercase;margin:12px 0 4px 0;">Patient</p>'
            f'<p style="color:#0a3d47;margin:0;">{pat_e}</p>'
            '<p style="color:#2d5c6a;font-size:11px;text-transform:uppercase;margin:12px 0 4px 0;">Doctor</p>'
            f'<p style="color:#0a3d47;margin:0;">{doc_e}</p>'
            '<p style="color:#2d5c6a;font-size:11px;text-transform:uppercase;margin:12px 0 4px 0;">Treatment</p>'
            f'<p style="color:#0a3d47;margin:0;">{tr_e}</p>'
            "</div><div>"
            '<p style="color:#2d5c6a;font-size:11px;text-transform:uppercase;margin:0 0 4px 0;">Medicines</p>'
            f'<p style="color:#0a3d47;margin:0;">{med_e}</p>'
            '<p style="color:#2d5c6a;font-size:11px;text-transform:uppercase;margin:12px 0 4px 0;">Dosage</p>'
            f'<p style="color:#0a3d47;margin:0;">{dose_e}</p>'
            '<p style="color:#2d5c6a;font-size:11px;text-transform:uppercase;margin:12px 0 4px 0;">Status · Created</p>'
            f'<p style="color:#0a3d47;margin:0;">{stat_e} · {dt_e}</p>'
            f"{upd_html}</div></div></div>"
        )
        st.markdown(card, unsafe_allow_html=True)

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
