import pandas as pd

def detect_interaction(medicines):

    interactions = {
        ("ibuprofen","aspirin"):"Risk of stomach bleeding",
        ("paracetamol","alcohol"):"Risk of liver damage",
        ("amoxicillin","methotrexate"):"Toxicity risk"
    }

    meds = [m.strip().lower() for m in medicines.split(",")]

    warnings = []

    for i in range(len(meds)):
        for j in range(i+1,len(meds)):

            pair = (meds[i],meds[j])
            reverse = (meds[j],meds[i])

            if pair in interactions:
                warnings.append(interactions[pair])

            if reverse in interactions:
                warnings.append(interactions[reverse])

    return warnings