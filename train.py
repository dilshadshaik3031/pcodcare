"""
Train everything the website needs and save it.

  - Standard setting: all questions
  - Leakage-aware setting: diagnosis-defining (Rotterdam) questions removed

Run:  python train.py
      python train.py --data data/your_real_file.xlsx
"""
import argparse
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, confusion_matrix

import pcod_core as core
import adaptive as A


def load_data(path):
    df = pd.read_excel(path)
    df = df[df[core.TARGET].isin(["Yes", "No"])].reset_index(drop=True)
    X = A.fill_derived(core.encode(df))[A.ALL_COLS]
    y = (df[core.TARGET] == "Yes").astype(int).values
    sites = df["Site_Code"].values if "Site_Code" in df.columns else np.array(["all"] * len(df))
    return X, y, sites


def report(y_true, prob):
    pred = (prob >= 0.5).astype(int)
    cm = confusion_matrix(y_true, pred, labels=[0, 1])
    return roc_auc_score(y_true, prob), cm[1, 1] / cm[1].sum(), cm[0, 0] / cm[0].sum(), cm[1, 0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/PCOD_Sample_Data_SYNTHETIC.xlsx")
    args = ap.parse_args()

    X, y, _ = load_data(args.data)
    print(f"Loaded {len(y)} records, PCOD = {y.sum()} ({100 * y.mean():.1f}%)")

    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    for leak in (False, True):
        print(f"\nFixed stage models, 5-fold CV ({'leakage-free' if leak else 'all features'})")
        for level, cols in core.stage_cols(leak).items():
            prob = cross_val_predict(HistGradientBoostingClassifier(random_state=0), X[cols], y,
                                     cv=folds, method="predict_proba")[:, 1]
            auc, sens, spec, missed = report(y, prob)
            print(f"  Level 1-{level}: AUC={auc:.3f}  Sensitivity={sens:.2f}  Specificity={spec:.2f}  Missed={missed}")

    print("\nTraining website models (this takes about half a minute)...")
    kits = {leak: A.train_kit(X, y, leakage_free=leak) for leak in (False, True)}
    os.makedirs("models", exist_ok=True)
    joblib.dump({"kits": kits, "trained_on": args.data}, "models/pcod_models.joblib")
    print("Saved models/pcod_models.joblib")
    print("Next: python evaluate.py   (builds the Evaluation page results)")


if __name__ == "__main__":
    main()
