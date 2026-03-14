def detect_duplicate(patient, medicine, history):
    for record in history:
        if record["patient"] == patient and record["medicine"] == medicine:
            return True
    return False