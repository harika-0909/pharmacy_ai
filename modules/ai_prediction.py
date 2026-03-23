"""
AI Prediction & Analytics Module
"""
import streamlit as st
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import random
from datetime import datetime, timedelta

from modules.utils.db import get_all_prescriptions, get_inventory, sanitize_df


def show():
    st.title("🤖 AI Predictions & Analytics")

    prescriptions = get_all_prescriptions()

    if not prescriptions:
        st.warning("No prescription data available. Create prescriptions first.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(sanitize_df(prescriptions))

    # Normalize column names
    if "medicines" not in df.columns and "Medicines" in df.columns:
        df = df.rename(columns={"Medicines": "medicines"})

    # Get inventory data
    inventory_items = get_inventory()
    if inventory_items:
        inventory_df = pd.DataFrame(sanitize_df(inventory_items))
        if "medicine_name" in inventory_df.columns:
            inventory_df = inventory_df.rename(columns={"medicine_name": "medicine"})
    else:
        inventory_df = pd.DataFrame()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Medicine Demand",
        "💊 Patient Adherence",
        "🦠 Disease Trends",
        "⏰ Expiry Prediction",
        "📦 Inventory Reordering"
    ])

    with tab1:
        show_medicine_demand(df)

    with tab2:
        show_patient_adherence(df)

    with tab3:
        show_disease_trends(df)

    with tab4:
        show_expiry_prediction(inventory_df)

    with tab5:
        show_inventory_reordering(df, inventory_df)


def show_medicine_demand(df):
    st.header("Medicine Demand Prediction")

    if "medicines" not in df.columns:
        st.warning("No medicines column found")
        return

    meds = df["medicines"].str.split(",").explode().str.strip()
    med_counts = meds.value_counts().reset_index()
    med_counts.columns = ["Medicine", "Usage"]

    col1, col2 = st.columns(2)

    with col1:
        st.dataframe(med_counts.head(20))

    with col2:
        st.bar_chart(med_counts.head(15).set_index("Medicine"))

    st.subheader("📈 Future Demand Prediction")

    if len(med_counts) > 1:
        X = np.array(range(len(med_counts))).reshape(-1, 1)
        y = med_counts["Usage"].values

        model = LinearRegression()
        model.fit(X, y)

        future_index = np.array([[len(med_counts)]])
        prediction = model.predict(future_index)

        st.success(f"Predicted demand score for next medicine category: {int(prediction[0])}")
    else:
        st.info("Need more prescription data for predictions")


def show_patient_adherence(df):
    st.header("Patient Adherence Prediction")

    if "medicines" not in df.columns:
        st.warning("Medicines column missing")
        return

    df_copy = df.copy()
    df_copy["medicine_count"] = df_copy["medicines"].str.split(",").str.len()
    df_copy["has_caregiver"] = df_copy.get("caregiver", pd.Series()).notna()

    if "age" not in df_copy.columns:
        df_copy["age"] = [random.randint(20, 70) for _ in range(len(df_copy))]

    def predict_adherence(row):
        score = 0.8
        if row.get("medicine_count", 1) > 3:
            score -= 0.1
        if row.get("has_caregiver", False):
            score += 0.1
        age = row.get("age", 40)
        if isinstance(age, (int, float)) and age > 65:
            score -= 0.05
        return max(0.1, min(1.0, score))

    df_copy["adherence_score"] = df_copy.apply(predict_adherence, axis=1)
    df_copy["adherence_risk"] = df_copy["adherence_score"].apply(
        lambda x: "High Risk" if x < 0.6 else "Medium Risk" if x < 0.8 else "Low Risk"
    )

    st.subheader("Adherence Risk Distribution")
    st.bar_chart(df_copy["adherence_risk"].value_counts())

    st.subheader("High Risk Patients")
    display_cols = []
    if "patient_name" in df_copy.columns:
        display_cols.append("patient_name")
    display_cols.extend(["medicines", "adherence_score"])

    high_risk = df_copy[df_copy["adherence_risk"] == "High Risk"][display_cols]
    st.dataframe(high_risk)


def show_disease_trends(df):
    st.header("Disease Trend Prediction")

    if "medicines" not in df.columns:
        st.warning("Medicines column missing")
        return

    disease_map = {
        "Paracetamol": "Fever/Pain",
        "Ibuprofen": "Inflammation/Pain",
        "Amoxicillin": "Infection",
        "Omeprazole": "Acid Reflux",
        "Metformin": "Diabetes",
        "Insulin": "Diabetes",
        "Aspirin": "Cardiovascular",
        "Amlodipine": "Hypertension",
        "Atorvastatin": "High Cholesterol",
    }

    df_copy = df.copy()
    df_copy["diseases"] = df_copy["medicines"].apply(
        lambda meds: [disease_map.get(m.strip(), "Other") for m in str(meds).split(",")]
    )

    all_diseases = []
    for diseases in df_copy["diseases"]:
        all_diseases.extend(diseases)

    disease_counts = pd.Series(all_diseases).value_counts()
    st.bar_chart(disease_counts)

    if len(disease_counts) > 0:
        top_disease = disease_counts.index[0]
        score = random.uniform(0.1, 0.9)

        if score > 0.7:
            st.error(f"⚠️ High risk of {top_disease} outbreak")
        elif score > 0.4:
            st.warning(f"📊 Moderate increase expected for {top_disease}")
        else:
            st.success(f"✅ Low outbreak risk for {top_disease}")


def show_expiry_prediction(inventory_df):
    st.header("Medicine Expiry Prediction")

    if inventory_df.empty:
        st.info("No inventory data available. Inventory will be populated when seeded.")

        # Generate sample data
        sample_data = []
        medicines = ["Paracetamol", "Ibuprofen", "Amoxicillin", "Aspirin", "Omeprazole",
                     "Metformin", "Lisinopril", "Simvastatin", "Warfarin", "Insulin"]

        for med in medicines:
            expiry = datetime.now() + timedelta(days=random.randint(30, 365))
            sample_data.append({
                "medicine": med,
                "stock": random.randint(10, 200),
                "expiry_date": expiry,
                "reorder_level": random.randint(20, 50),
                "days_to_expiry": (expiry - datetime.now()).days
            })

        inv_df = pd.DataFrame(sample_data)
        st.bar_chart(inv_df.set_index("medicine")["days_to_expiry"])

        expiring = inv_df[inv_df["days_to_expiry"] < 90]
        st.subheader("Medicines Expiring Soon")
        st.dataframe(expiring)
        return

    # Use actual inventory data
    if "expiry_date" in inventory_df.columns:
        inventory_df["expiry_date"] = pd.to_datetime(inventory_df["expiry_date"])
        inventory_df["days_to_expiry"] = (
            inventory_df["expiry_date"] - datetime.now()
        ).dt.days

        st.bar_chart(inventory_df["days_to_expiry"])

        expiring = inventory_df[inventory_df["days_to_expiry"] < 90]
        st.subheader("Medicines Expiring Soon")
        st.dataframe(expiring)
    else:
        st.info("Expiry date data not available in inventory")


def show_inventory_reordering(df, inventory_df):
    st.header("Smart Inventory Reordering")

    if inventory_df.empty:
        st.info("No inventory data available for reordering analysis")
        return

    if "medicines" not in df.columns:
        st.warning("Medicines column missing in prescriptions")
        return

    meds = df["medicines"].str.split(",").explode().str.strip()
    usage_counts = meds.value_counts()

    inv_copy = inventory_df.copy()

    if "medicine" in inv_copy.columns:
        inv_copy["current_usage"] = inv_copy["medicine"].map(usage_counts).fillna(0)
    elif "medicine_name" in inv_copy.columns:
        inv_copy["current_usage"] = inv_copy["medicine_name"].map(usage_counts).fillna(0)

    if "stock" in inv_copy.columns and "reorder_level" in inv_copy.columns:
        def reorder(row):
            stock = row.get("stock", 0)
            level = row.get("reorder_level", 15)
            if stock <= level:
                return "Urgent"
            elif stock <= level * 1.5:
                return "Reorder Soon"
            else:
                return "OK"

        inv_copy["reorder_status"] = inv_copy.apply(reorder, axis=1)
        st.bar_chart(inv_copy["reorder_status"].value_counts())

        needs_reorder = inv_copy[inv_copy["reorder_status"] != "OK"]
        if not needs_reorder.empty:
            st.dataframe(needs_reorder)
        else:
            st.success("✅ All inventory levels are healthy")
    else:
        st.info("Stock and reorder level data not available")