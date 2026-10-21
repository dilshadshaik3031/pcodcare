"""
Shared logic used by both train.py and app.py.
Keeping it in one place means the website encodes data exactly the way the model was trained.
"""
import numpy as np
import pandas as pd

# ---------- Columns in each level (same names as the Excel sheet) ----------
LEVEL1 = ["Age_years", "Height_cm", "Weight_kg", "BMI", "Age_at_Menarche", "Cycle_Pattern",
          "Cycle_Length_days", "Period_Duration_days", "Pregnancies_Count", "Recent_Weight_Gain",
          "Hair_Growth_Excess", "Acne", "Hair_Loss", "Skin_Darkening", "Regular_Exercise",
          "Fast_Food_Weekly", "Family_Hx_PCOD", "Family_Hx_Diabetes", "On_Hormonal_Meds"]

LEVEL2_EXAM = ["Waist_cm", "Hip_cm", "Waist_Hip_Ratio", "Systolic_BP", "Diastolic_BP", "Pulse_bpm",
               "mFG_Score"]
LEVEL2_LABS = ["Total_Testosterone_ng_dL", "Free_Testosterone_pg_mL", "SHBG_nmol_L", "DHEAS_ug_dL",
               "LH_mIU_mL", "FSH_mIU_mL", "LH_FSH_Ratio", "AMH_ng_mL", "TSH_mIU_L", "Prolactin_ng_mL",
               "17OHP_ng_dL", "Fasting_Glucose_mg_dL", "Fasting_Insulin_uIU_mL", "HOMA_IR", "HbA1c_pct",
               "Total_Cholesterol_mg_dL", "HDL_mg_dL", "LDL_mg_dL", "Triglycerides_mg_dL",
               "Vitamin_D_ng_mL"]
LEVEL2 = LEVEL2_EXAM + LEVEL2_LABS

LEVEL3 = ["US_Type", "Follicle_Count_Left", "Follicle_Count_Right", "Avg_Follicle_Size_Left_mm",
          "Avg_Follicle_Size_Right_mm", "Ovarian_Volume_Left_mL", "Ovarian_Volume_Right_mL",
          "Endometrium_mm"]

ALL_RAW = LEVEL1 + LEVEL2 + LEVEL3
TARGET = "PCOD_Diagnosis"

# ---------- Adaptive policy settings ----------
LOW = 0.15      # below this = confident low risk, stop
HIGH = 0.85     # above this = confident high risk, stop and see a doctor
STABLE = 0.05   # if risk moved less than this after new results, more tests won't help much


def encode(raw: pd.DataFrame) -> pd.DataFrame:
    """Turn sheet-style data into numbers (Step 2 of the tutorial). Blanks and 'Unknown' stay NaN."""
    raw = raw.copy()
    for c in ALL_RAW:                       # columns not filled in yet become blank
        if c not in raw.columns:
            raw[c] = np.nan
    yn = {"Yes": 1, "No": 0}
    X = pd.DataFrame(index=raw.index)
    for col in ALL_RAW:
        if col == "Cycle_Pattern":
            X["Cycle_Irregular"] = raw[col].map({"Regular": 0, "Irregular": 1, "Absent": 1})
            X["Cycle_Absent"] = raw[col].map({"Regular": 0, "Irregular": 0, "Absent": 1})
        elif col == "US_Type":
            X["US_Transvaginal"] = raw[col].map({"Transvaginal": 1, "Transabdominal": 0})
        elif pd.api.types.is_numeric_dtype(raw[col]):
            X[col] = raw[col]
        else:
            X[col] = raw[col].map(yn)
    return X.astype(float)


def encoded_names(raw_cols):
    out = []
    for c in raw_cols:
        if c == "Cycle_Pattern":
            out += ["Cycle_Irregular", "Cycle_Absent"]
        elif c == "US_Type":
            out.append("US_Transvaginal")
        else:
            out.append(c)
    return out


# Rotterdam-defining features (part of how PCOD is diagnosed). Leakage-aware mode leaves them out.
LEAKAGE_RAW = ["Cycle_Pattern", "Cycle_Length_days", "Hair_Growth_Excess", "mFG_Score",
               "Total_Testosterone_ng_dL", "Free_Testosterone_pg_mL", "DHEAS_ug_dL",
               "Follicle_Count_Left", "Follicle_Count_Right",
               "Ovarian_Volume_Left_mL", "Ovarian_Volume_Right_mL"]


def stage_cols(leakage_free=False):
    drop = set(encoded_names(LEAKAGE_RAW)) if leakage_free else set()
    groups = {1: LEVEL1, 2: LEVEL1 + LEVEL2, 3: LEVEL1 + LEVEL2 + LEVEL3}
    return {k: [c for c in encoded_names(v) if c not in drop] for k, v in groups.items()}


# Columns each stage model sees
STAGE_COLS = {
    1: encoded_names(LEVEL1),
    2: encoded_names(LEVEL1 + LEVEL2),
    3: encoded_names(LEVEL1 + LEVEL2 + LEVEL3),
}


