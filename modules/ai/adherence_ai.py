import random

def predict_adherence(age, medicines_count, past_missed):

    score = 100

    score -= medicines_count * 5
    score -= past_missed * 10

    if age > 65:
        score -= 10

    score = max(score, 0)

    return score