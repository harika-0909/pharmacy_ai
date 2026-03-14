"""Add Age column to prescriptions.csv"""

import csv
import random
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'data' / 'prescriptions.csv'

# Read existing data
rows = []
with path.open(newline='') as f:
    reader = csv.DictReader(f)
    rows = [row for row in reader]

# Add Age column with random values
random.seed(42)
for row in rows:
    row['Age'] = str(random.randint(18, 85))

# Write back with new Age column
with path.open('w', newline='') as f:
    fieldnames = ['PrescriptionID', 'Patient', 'Doctor', 'Medicines', 'Caregiver', 'CaregiverPhone', 'Age']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Added Age column to {path}")
print(f"Total rows: {len(rows)}")