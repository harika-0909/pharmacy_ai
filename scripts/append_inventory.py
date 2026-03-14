"""Append new medicine entries to data/inventory.csv.

This script avoids pandas dependency by using the standard library csv module.
"""

import csv
import random
import datetime
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[1] / 'data' / 'inventory.csv'

# Load existing medicine names
with CSV_PATH.open(newline='') as f:
    reader = csv.DictReader(f)
    existing = {row['Medicine'] for row in reader}

# Generate new unique medicine rows
random.seed(42)

PREFIXES = ['Nova', 'Ultra', 'Aero', 'Zen', 'Tri', 'Bio', 'Neo', 'Max', 'Pro', 'Eco']
SUFFIXES = ['zol', 'tab', 'cyn', 'lex', 'rid', 'nex', 'tin', 'rol', 'dex', 'fin']

start = datetime.date(2026, 1, 1)
end = datetime.date(2029, 12, 31)
delta_days = (end - start).days

new_rows = []

while len(new_rows) < 1000:
    name = f"{random.choice(PREFIXES)}{random.choice(SUFFIXES)}{random.randint(100, 999)}"
    if name in existing:
        continue
    existing.add(name)

    stock = random.randint(10, 500)
    expiry = (start + datetime.timedelta(days=random.randint(0, delta_days))).isoformat()
    reorder = random.randint(10, 100)

    new_rows.append([name, stock, expiry, reorder])

# Append to CSV
with CSV_PATH.open('a', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(new_rows)

print(f"Appended {len(new_rows)} new medicines to {CSV_PATH}")
print(f"New total rows: {sum(1 for _ in CSV_PATH.open())-1}")
