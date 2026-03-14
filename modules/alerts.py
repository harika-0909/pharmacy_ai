"""
Alerts Module - Low stock alerts & medication reminders
"""
import streamlit as st
from datetime import datetime

from modules.utils.db import get_inventory, get_low_stock_items, get_all_prescriptions, seed_inventory

# Default inventory data for seeding
INVENTORY = {
    # Pain Relievers & Anti-inflammatory
    "Paracetamol": 50, "Ibuprofen": 10, "Aspirin": 5, "Naproxen": 25,
    "Diclofenac": 18, "Acetaminophen": 45, "Celecoxib": 12, "Meloxicam": 20,
    "Indomethacin": 15, "Ketorolac": 8,
    # Antibiotics
    "Amoxicillin": 20, "Azithromycin": 30, "Ciprofloxacin": 22, "Doxycycline": 28,
    "Metronidazole": 35, "Clindamycin": 16, "Erythromycin": 24, "Penicillin": 12,
    "Tetracycline": 18, "Vancomycin": 6, "Gentamicin": 14, "Levofloxacin": 19,
    "Trimethoprim": 26, "Sulfamethoxazole": 21, "Cephalexin": 32,
    # Vitamins & Supplements
    "Vitamin C": 30, "Vitamin D3": 40, "Vitamin B12": 35, "Multivitamin": 55,
    "Calcium": 28, "Iron": 22, "Zinc": 38, "Magnesium": 25, "Omega-3": 20,
    "Folic Acid": 42, "Vitamin A": 15, "Vitamin E": 33, "Vitamin K": 18,
    "Biotin": 27, "Vitamin B6": 31,
    # Diabetes
    "Insulin": 15, "Metformin": 45, "Glipizide": 28, "Glyburide": 22,
    "Pioglitazone": 16, "Sitagliptin": 19, "Liraglutide": 8, "Exenatide": 12,
    # Cardiovascular
    "Amlodipine": 38, "Lisinopril": 42, "Losartan": 35, "Metoprolol": 29,
    "Atorvastatin": 48, "Simvastatin": 33, "Warfarin": 11, "Clopidogrel": 26,
    "Digoxin": 9, "Furosemide": 37, "Hydrochlorothiazide": 41,
    # Respiratory
    "Albuterol": 44, "Salbutamol": 39, "Fluticasone": 25, "Budesonide": 31,
    "Montelukast": 36, "Theophylline": 13, "Prednisone": 34, "Dexamethasone": 28,
    # Gastrointestinal
    "Omeprazole": 52, "Pantoprazole": 46, "Ranitidine": 29, "Famotidine": 33,
    "Lansoprazole": 24, "Loperamide": 41,
    # Antihistamines
    "Loratadine": 47, "Cetirizine": 43, "Diphenhydramine": 39, "Fexofenadine": 36,
    # Psychiatric
    "Sertraline": 23, "Escitalopram": 19, "Fluoxetine": 26, "Gabapentin": 34,
    "Pregabalin": 27, "Carbamazepine": 20,
}

LOW_STOCK_THRESHOLD = 15


def get_low_stock_alerts():
    """Generate alerts for medicines with low stock from MongoDB."""
    alerts = []
    low_stock = get_low_stock_items(LOW_STOCK_THRESHOLD)
    for item in low_stock:
        name = item.get("medicine_name", "Unknown")
        stock = item.get("stock", 0)
        alerts.append(
            f"⚠️ Low Stock Alert: {name} has only {stock} units remaining. "
            f"Please restock immediately."
        )
    return alerts


def get_missed_medicine_alerts():
    """Generate alerts for missed medicines (simplified)."""
    alerts = []
    try:
        prescriptions = get_all_prescriptions()
        current_hour = datetime.now().hour

        for presc in prescriptions[:20]:  # Limit to recent
            medicines = presc.get("medicines", "")
            patient = presc.get("patient_name", "Unknown")

            if medicines:
                for med in medicines.split(","):
                    med = med.strip()
                    if current_hour > 10 and "morning" in med.lower():
                        alerts.append(
                            f"🚨 Missed Medicine: {patient} may have missed "
                            f"{med} (morning dose)"
                        )
                    elif current_hour > 20 and "evening" in med.lower():
                        alerts.append(
                            f"🚨 Missed Medicine: {patient} may have missed "
                            f"{med} (evening dose)"
                        )
    except Exception as e:
        pass
    return alerts


def get_all_alerts():
    """Get all active alerts."""
    # Ensure inventory is seeded
    seed_inventory(INVENTORY)

    alerts = []
    alerts.extend(get_low_stock_alerts())
    alerts.extend(get_missed_medicine_alerts())
    return alerts


def show_alerts():
    """Display alerts in Streamlit UI."""
    st.markdown("## 🚨 Alert System")

    alerts = get_all_alerts()

    if not alerts:
        st.success("✅ No alerts at this time. Everything is running smoothly!")
    else:
        st.warning(f"**{len(alerts)} active alerts found**")
        st.divider()

        # Categorize alerts
        low_stock_alerts = [a for a in alerts if "Low Stock" in a]
        missed_alerts = [a for a in alerts if "Missed" in a]

        if low_stock_alerts:
            st.subheader("📦 Low Stock Alerts")
            for alert in low_stock_alerts:
                st.warning(alert)

        if missed_alerts:
            st.subheader("💊 Missed Medicine Alerts")
            for alert in missed_alerts:
                st.error(alert)