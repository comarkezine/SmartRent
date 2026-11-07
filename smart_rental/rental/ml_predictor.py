import joblib
import pandas as pd
from pathlib import Path
from functools import lru_cache


MODEL_PATH = (
    Path(__file__).resolve().parent
    / "ml_models"
    / "smartrent_rental_risk_model.joblib"
)


@lru_cache(maxsize=1)
def load_risk_model():
    """Load the trained Random Forest pipeline once."""
    return joblib.load(MODEL_PATH)


def predict_rental_risk(income, expense_difficulty, household_size):
    """Classify current rental arrears status."""

    data = pd.DataFrame({
        "INCOME": [int(income)],
        "EXPNS_DIF": [int(expense_difficulty)],
        "THHLD_NUMPER": [int(household_size)]
    })

    model = load_risk_model()

    prediction = int(model.predict(data)[0])

    risk_score = float(
        model.predict_proba(data)[0][1]
    )

    return {
        "prediction": prediction,
        "risk_score": round(risk_score * 100, 2),
        "classification": (
            "Behind on Rent"
            if prediction == 1
            else "Caught Up"
        )
    }