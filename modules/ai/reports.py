import streamlit as st

def show():

    st.header("📊 Reports")

    st.subheader("Prescription Reports")

    st.write("Generate reports for prescriptions and medicine usage.")

    if st.button("Download Report"):
        st.success("Report Generated")

        import streamlit as st

def show():

    st.header("📊 Reports")

    st.write("Generate and download reports")

    if st.button("Download Report"):
        st.success("Report Generated")