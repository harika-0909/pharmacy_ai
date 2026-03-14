import pandas as pd

def predict_demand(history):

    demand = history.mean()

    if demand > 50:
        return "High Demand - Restock Soon"

    elif demand > 20:
        return "Moderate Demand"

    else:
        return "Low Demand"