import streamlit as st

def show():

    st.header("💊 Pharmacy Inventory")

    col1, col2 = st.columns(2)

    with col1:
        medicine = st.text_input("Medicine Name")
        stock = st.number_input("Stock Quantity")
        expiry = st.date_input("Expiry Date")

        if st.button("Add Medicine"):
            st.success("Medicine Added Successfully")

    with col2:
        st.image(
        "https://images.unsplash.com/photo-1587854692152-cbe660dbde88",
        use_container_width=True
        )

        import streamlit as st

def show():

    st.header("💊 Pharmacy Inventory")

    col1,col2 = st.columns([2,1])

    with col1:

        medicine = st.text_input("Medicine Name")
        stock = st.number_input("Stock Quantity")
        expiry = st.date_input("Expiry Date")

        if st.button("Add Medicine"):
            st.success("Medicine Added")

    with col2:

        st.image(
        "https://images.unsplash.com/photo-1587854692152-cbe660dbde88",
        width=350
        )