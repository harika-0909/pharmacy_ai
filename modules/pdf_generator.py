from fpdf import FPDF
import pandas as pd
from datetime import datetime
import os

class PrescriptionPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Smart Pharmacy AI - Prescription', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()} - Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')

def generate_prescription_pdf(prescription_data):
    pdf = PrescriptionPDF()
    pdf.add_page()

    # Title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'PRESCRIPTION', 0, 1, 'C')
    pdf.ln(10)

    # Patient Information
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Patient Information:', 0, 1)
    pdf.set_font('Arial', '', 11)

    pdf.cell(50, 8, f'Name: {prescription_data.get("Patient", "N/A")}', 0, 1)
    pdf.cell(50, 8, f'Age: {prescription_data.get("Age", "N/A")}', 0, 1)
    pdf.cell(50, 8, f'Phone: {prescription_data.get("Phone", "N/A")}', 0, 1)
    pdf.ln(5)

    # Doctor Information
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Doctor Information:', 0, 1)
    pdf.set_font('Arial', '', 11)

    pdf.cell(50, 8, f'Name: {prescription_data.get("Doctor", "N/A")}', 0, 1)
    pdf.cell(50, 8, f'Specialty: {prescription_data.get("Specialty", "General")}', 0, 1)
    pdf.ln(5)

    # Medicines
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Prescribed Medicines:', 0, 1)
    pdf.set_font('Arial', '', 11)

    medicines = prescription_data.get("Medicines", "").split(",")
    for i, med in enumerate(medicines, 1):
        pdf.cell(0, 8, f'{i}. {med.strip()}', 0, 1)

    pdf.ln(5)

    # Instructions
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Instructions:', 0, 1)
    pdf.set_font('Arial', '', 11)

    instructions = prescription_data.get("Instructions", "Take as directed. Consult doctor if symptoms persist.")
    pdf.multi_cell(0, 8, instructions)

    pdf.ln(10)

    # Caregiver Info
    if prescription_data.get("Caregiver"):
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Caregiver:', 0, 1)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, prescription_data.get("Caregiver", "N/A"), 0, 1)

    # Signature
    pdf.ln(20)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'Dr. {prescription_data.get("Doctor", "N/A")}', 0, 1)
    pdf.cell(0, 10, 'Signature: ___________________________', 0, 1)

    # Pharmacy Stamp
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, 'Smart Pharmacy AI - Verified Digital Prescription', 0, 1, 'C')

    return pdf

def generate_pdf_for_prescription(prescription_id):
    try:
        df = pd.read_csv("data/prescriptions.csv")
        if prescription_id < len(df):
            prescription_data = df.iloc[prescription_id].to_dict()
            pdf = generate_prescription_pdf(prescription_data)

            # Save PDF
            filename = f"prescription_{prescription_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join("data", filename)
            os.makedirs("data", exist_ok=True)
            pdf.output(filepath)

            return filepath
    except Exception as e:
        print(f"Error generating PDF: {e}")
    return None