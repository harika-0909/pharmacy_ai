import streamlit as st
import pandas as pd
from modules.utils.db import get_all_prescriptions
from collections import Counter


def show():

    st.title("AI Analytics Dashboard")

    df = get_all_prescriptions()

    if df.empty:
        st.warning("No prescription data found")
        return

    st.write("Prescription Data")
    st.dataframe(df)

    st.subheader("Treatment Trends")

    treatment_counts = df["treatment_type"].value_counts()
    st.bar_chart(treatment_counts)

    st.subheader("Medicine Usage")

    medicines = []

    for m in df["medicines"]:
        for med in m.split(","):
            medicines.append(med.strip().lower())

    count = Counter(medicines)

    med_df = pd.DataFrame(count.items(), columns=["Medicine","Usage"])

    st.dataframe(med_df)

    st.bar_chart(med_df.set_index("Medicine"))