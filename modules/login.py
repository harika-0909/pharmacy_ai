"""
Login & Registration Module — Minimalist B&W
"""
import streamlit as st
from modules.utils.jwt_auth import (
    authenticate_user, hash_password, decode_token,
    get_role_permissions
)
from modules.utils.db import create_user, seed_default_data, seed_medicine_catalog


def login():
    seed_default_data()
    seed_medicine_catalog()

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.jwt_token = None

    if not st.session_state.logged_in:
        _, col, _ = st.columns([1.2, 1.6, 1.2])

        with col:
            st.markdown("""
            <div style="text-align:center; padding:60px 0 30px 0;">
                <p style="font-size:48px; margin:0;">💊</p>
                <h1 style="color:#fff; font-size:28px; font-weight:900; margin:12px 0 0 0; letter-spacing:-1px;">
                    Smart Pharmacy AI
                </h1>
                <p style="color:#555; font-size:12px; margin:6px 0 0 0; letter-spacing:2px; text-transform:uppercase;">
                    Secure Login
                </p>
            </div>
            """, unsafe_allow_html=True)

            tab1, tab2 = st.tabs(["Sign In", "Create Account"])

            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="Enter username")
                    password = st.text_input("Password", type="password", placeholder="Enter password")
                    submitted = st.form_submit_button("Sign In", use_container_width=True)

                    if submitted:
                        if not username or not password:
                            st.error("Fill in all fields")
                        else:
                            token, role = authenticate_user(username, password)
                            if token:
                                st.session_state.logged_in = True
                                st.session_state.role = role
                                st.session_state.username = username
                                st.session_state.jwt_token = token
                                st.rerun()
                            else:
                                st.error("Invalid credentials")

                with st.expander("Default Credentials"):
                    st.markdown("""
                    | Role | Username | Password |
                    |------|----------|----------|
                    | Admin | `admin` | `admin123` |
                    | Doctor | `doctor1` | `doctor123` |
                    | Pharmacy | `pharmacy1` | `pharmacy123` |
                    | Caregiver | `caregiver1` | `caregiver123` |
                    """)

            with tab2:
                with st.form("register_form"):
                    new_username = st.text_input("Username", placeholder="Choose username")
                    new_password = st.text_input("Password", type="password", placeholder="Min 6 characters")
                    confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
                    role = st.selectbox("Role", ["doctor", "caregiver", "pharmacy"])
                    submitted = st.form_submit_button("Create Account", use_container_width=True)

                    if submitted:
                        if not new_username or not new_password:
                            st.error("Fill in all fields")
                        elif new_password != confirm:
                            st.error("Passwords don't match")
                        elif len(new_password) < 6:
                            st.error("Password must be at least 6 characters")
                        else:
                            hashed = hash_password(new_password)
                            success, msg = create_user(new_username, hashed, role)
                            if success:
                                st.success("Account created. Sign in now.")
                            else:
                                st.error(msg)

            st.markdown("""
            <p style="text-align:center; color:#333; font-size:10px; margin-top:40px;">
                Secured with JWT · bcrypt · MongoDB
            </p>
            """, unsafe_allow_html=True)


def verify_session():
    if st.session_state.get("jwt_token"):
        payload = decode_token(st.session_state.jwt_token)
        if payload is None:
            st.session_state.logged_in = False
            st.session_state.role = None
            st.session_state.username = None
            st.session_state.jwt_token = None
            return False
        return True
    return False


def get_menu_options(role):
    return get_role_permissions(role)


def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.jwt_token = None
