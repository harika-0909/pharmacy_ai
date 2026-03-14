import streamlit as st
import pandas as pd

def show():

    st.header("🤖 AI Medicine Demand Prediction")

    data = {
        "Medicine": ["Paracetamol","Amoxicillin","Insulin","Vitamin D"],
        "Usage": [40,30,15,20]
    }

    df = pd.DataFrame(data)

    st.subheader("Current Usage")
    st.dataframe(df)

    st.subheader("Demand Prediction Chart")
    st.bar_chart(df.set_index("Medicine"))

    st.info("⚠ Paracetamol demand increasing")

    import streamlit as st
import pandas as pd

def show():

    st.header("🤖 AI Medicine Demand Prediction")

    data = {
        "Medicine":["Paracetamol","Amoxicillin","Insulin","Vitamin D"],
        "Usage":[40,30,20,15]
    }

    df = pd.DataFrame(data)

    st.dataframe(df)

    st.bar_chart(df.set_index("Medicine"))

    st.info("⚠ Paracetamol demand increasing")