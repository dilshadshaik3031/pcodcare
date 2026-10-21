"""
One-question-at-a-time adaptive screening, following the proposed direction of the literature review:
start from low-burden questions, update the patient's risk after every answer, choose the next question
for this patient, and stop using three signals together: risk, uncertainty and stability.

After every answer the model re-estimates PCOD risk. It then picks the next question that is
expected to move the estimate the most, and stops as soon as more questions are unlikely to help.

How "expected to move the estimate" is measured (greedy, EDDI-style):
  For each unanswered question we imagine plausible answers, taken from real training records.
  Answers from PCOD records are weighted by the current risk p, answers from non-PCOD records by 1 - p.
  We predict the new risk for each imagined answer and average how far it moves from the current risk.
  The question with the biggest expected move is asked next.
"""
import numpy as np
import pandas as pd

import pcod_core as core

# ---------------------------------------------------------------- stopping settings
LOW, HIGH = core.LOW, core.HIGH   # risk signal: confident low / high risk
UNC_MAX = 0.06                     # uncertainty signal: model disagreement (std) must be below this to stop
MIN_ANSWERS = 1                    # predict after every answer; can stop as soon as the first answer is clear
ROUND = 0                          # 0 = no batch checkpoints: one question at a time
MIN_GAIN = 0.015                   # best remaining question expected to move risk less than this -> leave level
STABLE_EPS = 0.02                  # stability signal: an answer that moved risk less than this = "no change"
STABLE_RUN = 3                     # this many "no change" answers in a row -> estimate has settled
MIN_PER_LEVEL = 3                  # ask at least this many questions in a level before calling it settled
SAMPLES = 12                       # imagined answers per class when scoring a question
COST = {1: 1, 2: 2, 3: 3}          # burden per question, from the Li et al. difficulty levels

LEVEL_NAMES = {1: "About you", 2: "Clinic results", 3: "Ultrasound"}

# ---------------------------------------------------------------- question bank
# kind: yn (yes/no), choice, num (one number), pair (two numbers asked together)
Q = []


def q(key, level, text, kind, cols, help_text="", **kw):
    Q.append(dict(key=key, level=level, text=text, kind=kind, cols=cols, help=help_text, **kw))


# Level 1: self-reported
q("age", 1, "How old are you?", "num", ["Age_years"], unit="years", lo=18, hi=45, step=1)
q("hw", 1, "What are your height and weight?", "pair", ["Height_cm", "Weight_kg"],
  "Your best estimate is fine.", labels=["Height (cm)", "Weight (kg)"], lo=[120.0, 30.0], hi=[200.0, 200.0],
  step=[1.0, 0.5])
q("cycle", 1, "In the past year, how regular have your periods been?", "choice",
  ["Cycle_Irregular", "Cycle_Absent"],
  options={"Regular, about the same each month": (0, 0),
           "Irregular, the timing changes a lot": (1, 0),
           "No period for three months or more": (1, 1)})
q("cycle_len", 1, "How many days are there usually from the start of one period to the start of the next?",
  "num", ["Cycle_Length_days"], unit="days", lo=15, hi=180, step=1)
q("period_len", 1, "How many days does your period usually last?", "num", ["Period_Duration_days"],
  unit="days", lo=1, hi=15, step=1)
q("menarche", 1, "How old were you when you had your first period?", "num", ["Age_at_Menarche"],
  unit="years", lo=8, hi=20, step=1)
q("preg", 1, "How many times have you been pregnant?", "num", ["Pregnancies_Count"], lo=0, hi=15, step=1)
q("weight_gain", 1, "Have you gained weight recently without a clear reason?", "yn", ["Recent_Weight_Gain"])
q("hair", 1, "Do you have more facial or body hair than you would expect?", "yn", ["Hair_Growth_Excess"],
  "For example on the chin, upper lip, chest or lower belly.")
q("acne", 1, "Do you have acne that keeps coming back?", "yn", ["Acne"])
q("hair_loss", 1, "Has the hair on your scalp been getting thinner?", "yn", ["Hair_Loss"])
q("skin", 1, "Do you have darker, velvety patches of skin on your neck, armpits or skin folds?", "yn",
  ["Skin_Darkening"])
q("exercise", 1, "Do you exercise at least three times a week?", "yn", ["Regular_Exercise"])
q("fast_food", 1, "Do you eat fast food more than twice a week?", "yn", ["Fast_Food_Weekly"])
q("fam_pcod", 1, "Has your mother or a sister been diagnosed with PCOD or PCOS?", "yn", ["Family_Hx_PCOD"])
q("fam_dm", 1, "Does a parent, brother or sister have type 2 diabetes?", "yn", ["Family_Hx_Diabetes"])
q("meds", 1, "Are you taking birth control pills or other hormone medicine right now?", "yn",
  ["On_Hormonal_Meds"], "These can change hormone levels and some symptoms.")

# Level 2: clinic visit (exam and blood tests)
q("waist_hip", 2, "What were your waist and hip measurements?", "pair", ["Waist_cm", "Hip_cm"],
  labels=["Waist (cm)", "Hip (cm)"], lo=[50.0, 60.0], hi=[170.0, 180.0], step=[1.0, 1.0])
q("bp", 2, "What was your blood pressure reading?", "pair", ["Systolic_BP", "Diastolic_BP"],
  "The two numbers, for example 120 over 80.", labels=["Top number", "Bottom number"],
  lo=[70, 40], hi=[200, 130], step=[1, 1])
q("pulse", 2, "What was your resting pulse?", "num", ["Pulse_bpm"], unit="beats per minute", lo=40, hi=150, step=1)
q("mfg", 2, "What hair growth (mFG) score did your doctor record?", "num", ["mFG_Score"],
  "A score from 0 to 36 from the physical exam.", lo=0, hi=36, step=1)
for key, col, name, unit, hi in [
    ("tt", "Total_Testosterone_ng_dL", "total testosterone", "ng/dL", 300),
    ("ft", "Free_Testosterone_pg_mL", "free testosterone", "pg/mL", 50),
    ("shbg", "SHBG_nmol_L", "SHBG", "nmol/L", 300),
    ("dheas", "DHEAS_ug_dL", "DHEA-S", "µg/dL", 1000),
    ("lh", "LH_mIU_mL", "LH", "mIU/mL", 100),
    ("fsh", "FSH_mIU_mL", "FSH", "mIU/mL", 100),
    ("amh", "AMH_ng_mL", "AMH", "ng/mL", 30),
    ("tsh", "TSH_mIU_L", "TSH (thyroid)", "mIU/L", 20),
    ("prl", "Prolactin_ng_mL", "prolactin", "ng/mL", 200),
    ("ohp", "17OHP_ng_dL", "17-OH progesterone", "ng/dL", 1000),
    ("glu", "Fasting_Glucose_mg_dL", "fasting glucose", "mg/dL", 400),
    ("ins", "Fasting_Insulin_uIU_mL", "fasting insulin", "µIU/mL", 200),
    ("a1c", "HbA1c_pct", "HbA1c", "%", 15),
    ("chol", "Total_Cholesterol_mg_dL", "total cholesterol", "mg/dL", 400),
    ("hdl", "HDL_mg_dL", "HDL cholesterol", "mg/dL", 150),
    ("ldl", "LDL_mg_dL", "LDL cholesterol", "mg/dL", 300),
    ("tg", "Triglycerides_mg_dL", "triglycerides", "mg/dL", 1000),
    ("vitd", "Vitamin_D_ng_mL", "vitamin D", "ng/mL", 150),
]:
    q(key, 2, f"What was your {name} result?", "num", [col], "You will find it on your lab report.",
      unit=unit, lo=0.0, hi=float(hi), step=0.1)

# Level 3: ultrasound
q("us_type", 3, "What kind of ultrasound did you have?", "choice", ["US_Transvaginal"],
  options={"Transvaginal (internal)": (1,), "Transabdominal (over the belly)": (0,)})
q("foll", 3, "How many follicles were counted in each ovary?", "pair",
  ["Follicle_Count_Left", "Follicle_Count_Right"], "Listed on the ultrasound report.",
  labels=["Left ovary", "Right ovary"], lo=[0, 0], hi=[100, 100], step=[1, 1])
q("fsize", 3, "What was the average follicle size in each ovary?", "pair",
  ["Avg_Follicle_Size_Left_mm", "Avg_Follicle_Size_Right_mm"],
  labels=["Left (mm)", "Right (mm)"], lo=[0.0, 0.0], hi=[30.0, 30.0], step=[0.5, 0.5])
q("ovol", 3, "What was the volume of each ovary?", "pair", ["Ovarian_Volume_Left_mL", "Ovarian_Volume_Right_mL"],
  labels=["Left (mL)", "Right (mL)"], lo=[0.0, 0.0], hi=[50.0, 50.0], step=[0.5, 0.5])
q("endo", 3, "What was the endometrial thickness?", "num", ["Endometrium_mm"], unit="mm", lo=0.0, hi=30.0, step=0.5)

BY_KEY = {x["key"]: x for x in Q}
ALL_COLS = core.STAGE_COLS[3]
_IX = {c: i for i, c in enumerate(ALL_COLS)}
LEAK_COLS = set(core.encoded_names(core.LEAKAGE_RAW))
for _x in Q:
    _x["leak"] = all(c in LEAK_COLS for c in _x["cols"])


def items_for(leakage_free):
    return [x for x in Q if not (leakage_free and x["leak"])]


# ---------------------------------------------------------------- data helpers
def fill_derived(df):
    """Recalculate BMI, waist-hip ratio, LH/FSH ratio and HOMA-IR from their parts (works on many rows)."""
    df = df.copy()
    df["BMI"] = (df["Weight_kg"] / (df["Height_cm"] / 100) ** 2).round(1)
    df["Waist_Hip_Ratio"] = (df["Waist_cm"] / df["Hip_cm"]).round(2)
    df["LH_FSH_Ratio"] = (df["LH_mIU_mL"] / df["FSH_mIU_mL"].where(df["FSH_mIU_mL"] > 0)).round(2)
    df["HOMA_IR"] = (df["Fasting_Glucose_mg_dL"] * df["Fasting_Insulin_uIU_mL"] / 405).round(2)
    return df


def to_frame(values: dict, n=1):
    row = np.array([values.get(c, np.nan) for c in ALL_COLS], dtype=float)
    return pd.DataFrame(np.tile(row, (n, 1)), columns=ALL_COLS)


def with_partial_answers(X, y, level, copies=10, seed=0):
    """
    Teach the model to work with only a few answers: add copies of the training data where a random
    share of questions (0 to 100 percent) is hidden for each patient.
    """
    rng = np.random.default_rng(seed)
    frames, ys = [X], [y]
    for _ in range(copies):
        Xc = X.copy()
        hide_rate = rng.random(len(X))
        for item in Q:
            if item["level"] <= level:
                hide = rng.random(len(X)) < hide_rate
                Xc.loc[hide, item["cols"]] = np.nan
        frames.append(fill_derived(Xc))
        ys.append(y)
    return pd.concat(frames, ignore_index=True), np.concatenate(ys)


def train_kit(X, y, leakage_free=False, n_ensemble=3, seed=0):
    """
    Everything the screening needs for one setting:
      models[level]   main model per level (risk signal)
      ens[level]      small bootstrap ensemble per level (uncertainty signal = disagreement)
    """
    from sklearn.ensemble import HistGradientBoostingClassifier
    X = X[ALL_COLS].reset_index(drop=True)
    y = np.asarray(y)
    cols = core.stage_cols(leakage_free)
    rng = np.random.default_rng(seed)
    models, ens = {}, {}
    for level in (1, 2, 3):
        Xa, ya = with_partial_answers(X, y, level, seed=seed + level)
        models[level] = HistGradientBoostingClassifier(random_state=seed).fit(Xa[cols[level]], ya)
        ens[level] = []
        for m in range(n_ensemble):
            idx = rng.integers(0, len(Xa), len(Xa))
            ens[level].append(HistGradientBoostingClassifier(random_state=seed + 10 + m, max_iter=80)
                              .fit(Xa.iloc[idx][cols[level]], ya[idx]))
    kit = dict(models=models, ens=ens, cols=cols, X=X, y=y, leakage_free=leakage_free,
               items=items_for(leakage_free))
    kit["samples"] = build_samples(kit)
    return kit


def build_samples(kit):
    """For each question, imagined answers taken from real training records, split by class."""
    X, y = kit["X"], kit["y"]
    rng = np.random.default_rng(0)
    out = {}
    for item in kit["items"]:
        ok = X[item["cols"]].notna().all(axis=1).values
        s = {}
        for cls in (0, 1):
            idx = np.where(ok & (y == cls))[0]
            s[cls] = None if len(idx) == 0 else X.iloc[rng.choice(idx, size=min(SAMPLES, len(idx)),
                                                                   replace=False)][item["cols"]].values
        out[item["key"]] = s
    return out


# ---------------------------------------------------------------- the three signals
def _row(kit, level, values):
    a = _derive_np(np.array([[values.get(c, np.nan) for c in ALL_COLS]], dtype=float))
    cols = kit["cols"][level]
    return pd.DataFrame(a[:, [_IX[c] for c in cols]], columns=cols)


def predict(kit, level, values: dict) -> float:
    return float(kit["models"][level].predict_proba(_row(kit, level, values))[:, 1][0])


def uncertainty(kit, level, values: dict) -> float:
    """How much the ensemble members disagree about this patient (standard deviation of their risks)."""
    X = _row(kit, level, values)
    return float(np.std([m.predict_proba(X)[:, 1][0] for m in kit["ens"][level]]))


def _derive_np(a):
    """Fast numpy version of fill_derived for many rows at once."""
    g = lambda c: a[:, _IX[c]]
    with np.errstate(divide="ignore", invalid="ignore"):
        a[:, _IX["BMI"]] = np.round(g("Weight_kg") / (g("Height_cm") / 100) ** 2, 1)
        a[:, _IX["Waist_Hip_Ratio"]] = np.round(g("Waist_cm") / g("Hip_cm"), 2)
        fsh = np.where(g("FSH_mIU_mL") > 0, g("FSH_mIU_mL"), np.nan)
        a[:, _IX["LH_FSH_Ratio"]] = np.round(g("LH_mIU_mL") / fsh, 2)
        a[:, _IX["HOMA_IR"]] = np.round(g("Fasting_Glucose_mg_dL") * g("Fasting_Insulin_uIU_mL") / 405, 2)
    return a


def rank_questions(kit, level, values, p_now, done_keys):
    """Expected move in risk for every unanswered question at this level, scored in one batch."""
    cands = [x for x in kit["items"] if x["level"] == level and x["key"] not in done_keys]
    base = np.array([values.get(c, np.nan) for c in ALL_COLS], dtype=float)
    parts, meta = [], []
    for item in cands:
        idx = [_IX[c] for c in item["cols"]]
        for cls, w in ((1, p_now), (0, 1 - p_now)):
            vals = kit["samples"][item["key"]][cls]
            if vals is None:
                continue
            block = np.tile(base, (len(vals), 1))
            block[:, idx] = vals
            parts.append(block)
            meta.append((item["key"], w, len(vals)))
    if not parts:
        return []
    big = _derive_np(np.vstack(parts))
    cols = kit["cols"][level]
    p_new = kit["models"][level].predict_proba(pd.DataFrame(big[:, [_IX[c] for c in cols]], columns=cols))[:, 1]
    scores, i = {}, 0
    for key, w, n in meta:
        scores[key] = scores.get(key, 0.0) + w * float(np.abs(p_new[i:i + n] - p_now).mean())
        i += n
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


def is_settled(S):
    moves = [abs(h["delta"]) for h in S["history"] if h.get("answered") and h["level"] == S["level"]]
    return (S["answered_in_level"] >= max(MIN_PER_LEVEL, STABLE_RUN) and len(moves) >= STABLE_RUN
            and all(m < STABLE_EPS for m in moves[-STABLE_RUN:]))


def next_action(kit, S, rule="proposed", order="adaptive", rng=None):
    """
    Decide what happens after the latest answer.
      rule:  "proposed"  = risk + uncertainty + stability (the review's proposed stopping rule)
             "risk_only" = stop on risk alone, otherwise keep asking until the level runs out
      order: "adaptive" (best expected move), "fixed" (sheet order) or "random"
    Returns ("ask", key, score) | ("checkpoint", reason) | ("escalate", reason) | ("stop", status, reason)
    A checkpoint means: the estimate is still unclear after a round of answers, so ask the person whether
    to answer more questions or see the result now.
    """
    level, last = S["level"], S["history"][-1]
    p, unc = last["p"], last.get("unc", 0.0)
    answered = sum(1 for h in S["history"] if h.get("answered"))
    sure = rule == "risk_only" or unc < UNC_MAX

    if answered >= MIN_ANSWERS and p < LOW and sure:
        return ("stop", "low", "Your answers point clearly to a low risk, and the model is consistent about it.")
    if answered >= MIN_ANSWERS and p > HIGH and sure:
        return ("stop", "high", "Your answers point clearly to a high risk, and the model is consistent about it.")

    if order == "adaptive":
        ranked = rank_questions(kit, level, S["values"], p, S["done_keys"])
    else:
        left = [x["key"] for x in kit["items"] if x["level"] == level and x["key"] not in S["done_keys"]]
        if order == "random" and left:
            left = list((rng or np.random.default_rng()).permutation(left))
        ranked = [(k, np.nan) for k in left]

    if not ranked:
        return ("escalate", "All questions at this level have been asked.")
    if rule == "proposed":
        if order == "adaptive" and S["answered_in_level"] >= MIN_PER_LEVEL and ranked[0][1] < MIN_GAIN:
            return ("escalate", "The remaining questions at this level are unlikely to change your estimate.")
        if is_settled(S):
            return ("escalate", "Your last few answers barely changed the estimate, so it has settled at this level.")
        if ROUND and S.get("since_check", 0) >= ROUND:
            return ("checkpoint", "More information is needed for a clear result.")
    return ("ask", ranked[0][0], ranked[0][1])


def risk_band(p):
    if p < LOW:
        return "low"
    if p > HIGH:
        return "high"
    return "unclear"