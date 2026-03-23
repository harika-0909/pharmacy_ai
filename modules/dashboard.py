"""
Dashboard — Minimalist B&W
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from modules.utils.db import (
    get_all_prescriptions, get_all_orders,
    get_all_patients, get_low_stock_items
)


def show():
    st.title("Dashboard")

    # Live alert widget (non-blocking — wrapped in try)
    try:
        from modules.alerts import show_dashboard_widget
        show_dashboard_widget()
    except Exception:
        pass

    prescriptions = get_all_prescriptions()
    orders = get_all_orders()
    patients = get_all_patients()

    doctors = set(p.get("doctor_name", "") for p in prescriptions if p.get("doctor_name"))
    pending = [o for o in orders if o.get("status") == "pending"]
    low_stock = get_low_stock_items()

    role = st.session_state.get('role', 'guest')

    # Alerts
    if role in ['pharmacy', 'admin'] and (pending or low_stock):
        alert_parts = []
        if pending:
            alert_parts.append(f"{len(pending)} pending orders")
        if low_stock:
            alert_parts.append(f"{len(low_stock)} low stock items")
        st.warning(" · ".join(alert_parts))

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Patients", len(patients))
    col2.metric("Prescriptions", len(prescriptions))
    col3.metric("Orders", len(orders))
    col4.metric("Doctors", len(doctors))

    # Order pipeline
    if orders and role in ['pharmacy', 'admin', 'doctor']:
        st.divider()
        st.markdown("##### Orders")
        status_counts = {}
        for o in orders:
            s = o.get("status", "pending")
            status_counts[s] = status_counts.get(s, 0) + 1

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Pending", status_counts.get("pending", 0))
        col2.metric("Processing", status_counts.get("processing", 0))
        col3.metric("Dispensed", status_counts.get("dispensed", 0))
        col4.metric("Completed", status_counts.get("completed", 0))

    # Two columns
    st.divider()
    left, right = st.columns([3, 2])

    with left:
        st.markdown("##### Top Medicines")
        if prescriptions:
            all_meds = []
            for p in prescriptions:
                meds = p.get("medicines", "")
                if meds:
                    all_meds.extend([m.strip() for m in meds.split(",")])
            if all_meds:
                counts = pd.Series(all_meds).value_counts().head(10)
                st.bar_chart(counts)
            else:
                st.caption("No data yet")
        else:
            st.caption("No prescriptions yet.")

    with right:
        st.markdown("##### Recent Activity")
        if prescriptions:
            recent = sorted(prescriptions, key=lambda x: x.get("created_at", datetime.min), reverse=True)[:8]
            for p in recent:
                doctor = p.get("doctor_name", "—")
                patient = p.get("patient_name", "—")
                meds = p.get("medicines", "—")
                if len(meds) > 35:
                    meds = meds[:35] + "…"
                date = str(p.get("created_at", ""))[:10]
                st.markdown(f"**{patient}** ← Dr. {doctor}  \n{meds} · _{date}_")
                st.markdown("---")
        else:
            st.caption("No activity yet.")