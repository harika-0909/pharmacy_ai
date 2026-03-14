import streamlit as st
import pandas as pd
import numpy as np

def show():

    st.markdown("# 🏥 Smart Pharmacy AI Dashboard")
    st.caption("AI-Driven Pharmacy Inventory & Patient Adherence System")

    st.divider()

    # ---------------- KPI CARDS ----------------

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💊 Total Medicines", "120", "+5 today")
    col2.metric("🧾 Prescriptions", "48", "+10 today")
    col3.metric("👨‍⚕️ Doctors", "12")
    col4.metric("⚠ Low Stock", "3")

    st.divider()

    # ---------------- CHARTS ----------------

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("💊 Medicine Usage")

        medicine_data = pd.DataFrame({
            "Medicine":["Paracetamol","Amoxicillin","Insulin","Vitamin D","Metformin"],
            "Usage":[40,30,15,20,18]
        })

        st.bar_chart(
            medicine_data.set_index("Medicine"),
            use_container_width=True
        )

    with col2:

        st.subheader("📈 Prescription Trends")

        trend_data = pd.DataFrame({
            "Day":["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
            "Prescriptions":[10,15,8,16,20,14,18]
        })

        st.line_chart(
            trend_data.set_index("Day"),
            use_container_width=True
        )

    st.divider()

    # ---------------- AI DEMAND PREDICTION ----------------

    st.subheader("🤖 AI Medicine Demand Prediction")

    demand_data = pd.DataFrame({
        "Medicine":["Paracetamol","Amoxicillin","Insulin","Vitamin D","Metformin"],
        "Predicted Demand":[55,40,22,25,30]
    })

    st.dataframe(demand_data, use_container_width=True)

    st.bar_chart(
        demand_data.set_index("Medicine"),
        use_container_width=True
    )

    st.divider()

    # ---------------- LOW STOCK ALERTS ----------------

    st.subheader("⚠ Low Stock Alerts")

    low_stock = pd.DataFrame({
        "Medicine":["Insulin","Metformin","Vitamin D"],
        "Stock Remaining":[5,8,6],
        "Reorder Level":[10,10,10]
    })

    st.dataframe(low_stock, use_container_width=True)

    st.warning("Some medicines are below reorder level. Please restock.")

    st.divider()

    # ---------------- AI INSIGHTS ----------------

    st.subheader("🧠 AI Insights")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
        """
        **Demand Prediction**

        Paracetamol demand expected to increase next week.
        """
        )

    with col2:
        st.warning(
        """
        **Low Stock Alert**

        Insulin stock may run out in 2 days.
        """
        )

    with col3:
        st.success(
        """
        **Patient Adherence**

        92% patients are following prescriptions.
        """
        )

    st.divider()

    # ---------------- QUICK ACTIONS ----------------

    st.subheader("⚡ Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.button("➕ Add Medicine")

    with col2:
        st.button("📋 View Prescriptions")

    with col3:
        st.button("📊 Generate Report")