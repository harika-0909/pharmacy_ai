import streamlit as st

def show():

    st.header("👨‍⚕️ Doctor Prescription Module")

    col1, col2 = st.columns(2)

    with col1:
        patient = st.text_input("Patient Name")
        doctor = st.text_input("Doctor Name")
        medicines = st.text_area("Medicines")
        dosage = st.text_input("Dosage")

        if st.button("Save Prescription"):
            st.success("Prescription Saved Successfully")

    with col2:
        st.image(
        "https://images.unsplash.com/photo-1582750433449-648ed127bb54",
        use_container_width=True
        )