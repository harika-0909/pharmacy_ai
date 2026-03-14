def check_interactions(medicines):

    interactions = {
        ("ibuprofen", "aspirin"): "May cause stomach bleeding",
        ("paracetamol", "alcohol"): "May cause liver damage",
        ("amoxicillin", "methotrexate"): "May increase toxicity"
    }

    meds = [m.strip().lower() for m in medicines.split(",")]

    warnings = []

    for i in range(len(meds)):
        for j in range(i+1,len(meds)):

            pair = (meds[i], meds[j])
            pair_reverse = (meds[j], meds[i])

            if pair in interactions:
                warnings.append(interactions[pair])

            if pair_reverse in interactions:
                warnings.append(interactions[pair_reverse])

    return warnings