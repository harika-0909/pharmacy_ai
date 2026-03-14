import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

def send_whatsapp_reminder(patient_name, phone, medicine, time):
    """
    Mock WhatsApp reminder function
    In a real implementation, this would integrate with WhatsApp Business API
    """
    message = f"""
🔔 Medicine Reminder from Smart Pharmacy AI

Hello {patient_name},

It's time to take your medicine: {medicine}

⏰ Scheduled Time: {time}
💊 Please take as prescribed

Stay healthy! 💪

Smart Pharmacy AI
    """

    # Mock sending - in reality, use WhatsApp API
    print(f"WhatsApp message sent to {phone}: {message}")

    return True, message

def show_whatsapp_reminders():
    st.header("📱 WhatsApp Medicine Reminder AI")

    try:
        df = pd.read_csv("data/prescriptions.csv")
    except:
        st.error("Prescription data not found")
        return

    # Get patients with phone numbers
    patients_with_phones = df.dropna(subset=['Phone'])

    if patients_with_phones.empty:
        st.warning("No patients with phone numbers found")
        return

    st.subheader("Send Medicine Reminders")

    # Select patient
    patient_names = patients_with_phones['Patient'].unique()
    selected_patient = st.selectbox("Select Patient", patient_names)

    if selected_patient:
        patient_data = patients_with_phones[patients_with_phones['Patient'] == selected_patient].iloc[0]
        medicines = patient_data['Medicines'].split(',')

        col1, col2 = st.columns(2)

        with col1:
            selected_medicine = st.selectbox("Select Medicine", [m.strip() for m in medicines])

        with col2:
            reminder_time = st.time_input("Reminder Time", datetime.now().time())

        if st.button("📱 Send WhatsApp Reminder", type="primary"):
            success, message = send_whatsapp_reminder(
                selected_patient,
                patient_data['Phone'],
                selected_medicine,
                reminder_time.strftime("%H:%M")
            )

            if success:
                st.success(f"✅ WhatsApp reminder sent to {selected_patient}!")
                with st.expander("Message Preview"):
                    st.code(message, language="text")
            else:
                st.error("Failed to send reminder")

    st.subheader("📋 Scheduled Reminders")

    # Mock scheduled reminders
    scheduled_reminders = [
        {"patient": "John Doe", "medicine": "Paracetamol", "time": "08:00", "status": "Scheduled"},
        {"patient": "Jane Smith", "medicine": "Amoxicillin", "time": "14:00", "status": "Sent"},
        {"patient": "Bob Johnson", "medicine": "Ibuprofen", "time": "20:00", "status": "Scheduled"},
    ]

    for reminder in scheduled_reminders:
        status_icon = "🟢" if reminder["status"] == "Sent" else "🟡"
        st.write(f"{status_icon} **{reminder['patient']}** - {reminder['medicine']} at {reminder['time']} ({reminder['status']})")

    st.info("💡 WhatsApp reminders help improve patient adherence by sending timely notifications directly to their phones.")

def ai_reminder_scheduler():
    """
    AI function to automatically schedule reminders based on prescription data
    """
    try:
        df = pd.read_csv("data/prescriptions.csv")

        # Simple AI logic: schedule reminders for patients with multiple medicines
        high_priority_patients = df[df['Medicines'].str.count(',') >= 2]

        reminders = []
        for _, patient in high_priority_patients.iterrows():
            medicines = patient['Medicines'].split(',')
            for med in medicines[:2]:  # Schedule for first 2 medicines
                reminders.append({
                    "patient": patient['Patient'],
                    "phone": patient.get('Phone', 'N/A'),
                    "medicine": med.strip(),
                    "time": "08:00" if random.choice([True, False]) else "20:00"
                })

        return reminders
    except:
        return []