"""
Evaluation following Section 9.3 of the literature review.

  1. Baselines vs the proposed policy, with and without diagnosis-defining features
       - Full-feature model (every question, every patient)
       - Fixed low-to-high order (as in AutoPCOS [12]), same stopping rule
       - Two-stage conformal escalation (as in Adegoke et al. [13])
       - Random question order, same stopping rule
       - Greedy expected-move selection, stopping on risk alone (EDDI-style [17])
       - Proposed: greedy selection + risk + uncertainty + stability
  2. Metrics: AUC, sensitivity, specificity, calibration (Brier, ECE), questions per patient,
     burden (Li et al. levels [16]), how far patients went, stability of the estimate
  3. Robustness: missing, noisy and contradictory answers
  4. External check: train on two hospital sites, test on the third

Progressive acquisition is simulated: each patient's recorded values are revealed one question at a time.

Run:  python evaluate.py              (a few minutes on a laptop)
      python evaluate.py --n 1000      (every patient, slower)
      python evaluate.py --only robust (re-run one part: all, leakfree, robust or external)
"""
import argparse
import json
import os
import time
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.model_selection import StratifiedKFold, train_test_split

import adaptive as A
from train import load_data

POLICIES = {
    "Proposed (risk + uncertainty + stability)": dict(rule="proposed", order="adaptive"),
    "Greedy, risk only (EDDI-style)": dict(rule="risk_only", order="adaptive"),
    "Fixed low-to-high order": dict(rule="proposed", order="fixed"),
    "Random order": dict(rule="proposed", order="random"),
}


# ---------------------------------------------------------------- one simulated patient
def answer_for(item, row):
    vals = {c: row[c] for c in item["cols"] if not np.isnan(row[c])}
    return vals or None


def has_level(kit, row, level):
    return any(answer_for(it, row) for it in kit["items"] if it["level"] == level)


def simulate(kit, row, rule, order, rng):
    S = dict(level=1, values={}, done_keys=set(), answered_in_level=0, history=[])
    S["history"].append(dict(p=A.predict(kit, 1, {}), unc=A.uncertainty(kit, 1, {}), level=1))
    cost, status = 0, None
    while True:
        act = A.next_action(kit, S, rule=rule, order=order, rng=rng)
        if act[0] == "ask":
            item = A.BY_KEY[act[1]]
            S["done_keys"].add(act[1])
            vals = answer_for(item, row)
            prev = S["history"][-1]["p"]
            if vals is None:                                  # patient doesn't have this answer
                S["history"].append(dict(p=prev, unc=S["history"][-1]["unc"], level=S["level"],
                                         delta=0.0, answered=False))
                continue
            S["values"].update(vals)
            p = A.predict(kit, S["level"], S["values"])
            S["history"].append(dict(p=p, unc=A.uncertainty(kit, S["level"], S["values"]), level=S["level"],
                                     delta=p - prev, answered=True))
            S["answered_in_level"] += 1
            cost += A.COST[item["level"]]
        elif act[0] == "escalate":
            if S["level"] == 3 or not has_level(kit, row, S["level"] + 1):
                status = "refer" if S["level"] == 3 else "needs_tests"
                break
            S["level"] += 1
            S["answered_in_level"] = 0
            S["history"].append(dict(p=A.predict(kit, S["level"], S["values"]),
                                     unc=A.uncertainty(kit, S["level"], S["values"]), level=S["level"]))
        else:
            status = act[1]
            break
    ps = [h["p"] for h in S["history"]]
    moves = [abs(h["delta"]) for h in S["history"] if h.get("answered")]
    return dict(p=ps[-1], status=status, questions=sum(1 for h in S["history"] if h.get("answered")),
                cost=cost, level=S["level"],
                flips=int(np.sum(np.diff(np.array(ps) >= 0.5) != 0)),
                last_moves=float(np.mean(moves[-3:])) if moves else 0.0)


def full_feature(kit, row):
    vals, cost, n = {}, 0, 0
    for it in kit["items"]:
        a = answer_for(it, row)
        if a:
            vals.update(a); cost += A.COST[it["level"]]; n += 1
    return dict(p=A.predict(kit, 3, vals), status="full", questions=n, cost=cost, level=3, flips=0, last_moves=0.0)


# ---------------------------------------------------------------- two-stage conformal baseline
def conformal_setup(Xtr, ytr, leak, alpha=0.05, seed=0):
    cols1 = A.core.stage_cols(leak)[1]
    Xa, Xc, ya, yc = train_test_split(Xtr, ytr, test_size=0.25, stratify=ytr, random_state=seed)
    m1 = HistGradientBoostingClassifier(random_state=seed).fit(Xa[cols1], ya)
    pc = m1.predict_proba(Xc[cols1])[:, 1]
    q = {}
    for c in (0, 1):                                    # class-conditional split conformal
        s = 1 - (pc[yc == c] if c == 1 else 1 - pc[yc == c])
        k = int(np.ceil((len(s) + 1) * (1 - alpha))) - 1
        q[c] = np.sort(s)[min(k, len(s) - 1)]
    return m1, cols1, q


def two_stage(kit, row, conf):
    m1, cols1, q = conf
    l1 = [it for it in kit["items"] if it["level"] == 1]
    vals, cost, n = {}, 0, 0
    for it in l1:
        a = answer_for(it, row)
        if a:
            vals.update(a); cost += 1; n += 1
    X1 = A._row(kit, 1, vals)[cols1]
    p1 = float(m1.predict_proba(X1)[:, 1][0])
    pred_set = [c for c in (0, 1) if (1 - (p1 if c == 1 else 1 - p1)) <= q[c]]
    if len(pred_set) == 1:
        return dict(p=p1, status="stage1", questions=n, cost=cost, level=1, flips=0, last_moves=0.0)
    out = full_feature(kit, row)
    out["flips"] = int((p1 >= 0.5) != (out["p"] >= 0.5))
    return out


# ---------------------------------------------------------------- scoring
def ece(y, p, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    return float(sum(abs(p[idx == b].mean() - y[idx == b].mean()) * (idx == b).mean()
                     for b in range(bins) if (idx == b).any()))


def summarize(y, recs):
    p = np.array([r["p"] for r in recs])
    pred = p >= 0.5
    unclear = np.array([A.LOW <= r["p"] <= A.HIGH and r["status"] in ("refer", "needs_tests") for r in recs])
    lv = np.array([r["level"] for r in recs])
    return {
        "AUC": roc_auc_score(y, p),
        "Sensitivity": pred[y == 1].mean(),
        "Specificity": (~pred)[y == 0].mean(),
        "Caught incl. referral": (pred | unclear)[y == 1].mean(),
        "Brier": brier_score_loss(y, p),
        "ECE": ece(y, p),
        "Questions per patient": np.mean([r["questions"] for r in recs]),
        "Burden per patient": np.mean([r["cost"] for r in recs]),
        "Reached Level 2 (%)": 100 * (lv >= 2).mean(),
        "Reached Level 3 (%)": 100 * (lv >= 3).mean(),
        "Flips across 50%": np.mean([r["flips"] for r in recs]),
        "Movement in last 3 answers": np.mean([r["last_moves"] for r in recs]),
    }


def corrupt(row, kind, level, rng, items):
    """Robustness settings: hide answers, add measurement noise, or flip yes/no answers."""
    r = row.copy()
    for it in items:
        if kind == "missing" and rng.random() < level:
            r[it["cols"]] = np.nan
        elif kind == "noisy" and it["kind"] in ("num", "pair"):
            for c in it["cols"]:
                if not np.isnan(r[c]):
                    r[c] = r[c] * (1 + rng.normal(0, level))
        elif kind == "contradictory" and it["kind"] == "yn":
            c = it["cols"][0]
            if not np.isnan(r[c]) and rng.random() < level:
                r[c] = 1 - r[c]
    return r


# ---------------------------------------------------------------- the three experiments
def run_comparison(X, y, leak, n, rng):
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    recs = {name: [] for name in list(POLICIES) + ["Two-stage conformal [13]", "Full-feature model"]}
    ys = []
    for f, (tr, te) in enumerate(folds.split(X, y)):
        print(f"[{'leakage-free' if leak else 'all features'}] fold {f + 1}/5", flush=True)
        kit = A.train_kit(X.iloc[tr], y[tr], leakage_free=leak, seed=f)
        conf = conformal_setup(X.iloc[tr], y[tr], leak, seed=f)
        for i in rng.choice(te, size=min(max(1, n // 5), len(te)), replace=False):
            row = X.iloc[i]
            for name, cfg in POLICIES.items():
                recs[name].append(simulate(kit, row, cfg["rule"], cfg["order"], rng))
            recs["Two-stage conformal [13]"].append(two_stage(kit, row, conf))
            recs["Full-feature model"].append(full_feature(kit, row))
            ys.append(y[i])
    ys = np.array(ys)
    rows = []
    for name, r in recs.items():
        row = summarize(ys, r)
        row.update(Policy=name, Setting="Leakage-free" if leak else "All features", Patients=len(ys))
        rows.append(row)
    return rows


def run_robustness(X, y, n, rng):
    print("Robustness tests", flush=True)
    tr, te = next(StratifiedKFold(n_splits=5, shuffle=True, random_state=42).split(X, y))
    kit = A.train_kit(X.iloc[tr], y[tr], seed=0)
    idx = rng.choice(te, size=min(n, len(te)), replace=False)
    out = []
    for kind, levels in (("missing", [0.0, 0.2, 0.4]), ("noisy", [0.1, 0.2]), ("contradictory", [0.1, 0.2])):
        for lvl in levels:
            rrng = np.random.default_rng(1)
            rows = [corrupt(X.iloc[i], kind, lvl, rrng, kit["items"]) for i in idx]
            for name, fn in (("Proposed (risk + uncertainty + stability)",
                              lambda r: simulate(kit, r, "proposed", "adaptive", rrng)),
                             ("Fixed low-to-high order", lambda r: simulate(kit, r, "proposed", "fixed", rrng)),
                             ("Full-feature model", lambda r: full_feature(kit, r))):
                srow = summarize(y[idx], [fn(r) for r in rows])
                srow.update(Policy=name, Corruption=kind, Level=lvl, Patients=len(idx))
                out.append(srow)
    clean = [r for r in out if r["Level"] == 0.0]          # the clean run is the starting point of every curve
    for kind in ("noisy", "contradictory"):
        out += [{**r, "Corruption": kind} for r in clean]
    return out


def run_external(X, y, sites, n, rng):
    print("External site check", flush=True)
    uniq = sorted(s for s in pd.unique(sites) if s != "all")
    if len(uniq) < 2:
        return []
    test_site = uniq[-1]
    tr, te = np.where(sites != test_site)[0], np.where(sites == test_site)[0]
    te = rng.choice(te, size=min(n, len(te)), replace=False)
    kit = A.train_kit(X.iloc[tr], y[tr], seed=7)
    out = []
    for name, fn in (("Proposed (risk + uncertainty + stability)",
                      lambda r: simulate(kit, r, "proposed", "adaptive", rng)),
                     ("Full-feature model", lambda r: full_feature(kit, r))):
        srow = summarize(y[te], [fn(X.iloc[i]) for i in te])
        srow.update(Policy=name, Train=", ".join(uniq[:-1]), Test=test_site, Patients=len(te))
        out.append(srow)
    return out


# ---------------------------------------------------------------- main
PARTS = ["all", "leakfree", "robust", "external"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/PCOD_Sample_Data_SYNTHETIC.xlsx")
    ap.add_argument("--n", type=int, default=300, help="patients evaluated (spread across the 5 folds)")
    ap.add_argument("--robust-n", type=int, default=150)
    ap.add_argument("--only", choices=PARTS, help="run just one part (results from earlier parts are kept)")
    args = ap.parse_args()
    t0 = time.time()
    X, y, sites = load_data(args.data)
    rng = np.random.default_rng(0)
    os.makedirs("results", exist_ok=True)
    parts = [args.only] if args.only else PARTS

    for part in parts:
        if part == "all":
            rows = run_comparison(X, y, False, args.n, rng)
        elif part == "leakfree":
            rows = run_comparison(X, y, True, args.n, rng)
        elif part == "robust":
            rows = run_robustness(X, y, args.robust_n, rng)
        else:
            rows = run_external(X, y, sites, args.n // 2, rng)
        pd.DataFrame(rows).to_csv(f"results/part_{part}.csv", index=False)

    # combine whatever parts exist into the files the website reads
    read = lambda p: pd.read_csv(f"results/part_{p}.csv") if os.path.exists(f"results/part_{p}.csv") else None
    comp = [d for d in (read("all"), read("leakfree")) if d is not None]
    if comp:
        pd.concat(comp).to_csv("results/comparison.csv", index=False)
    for p, name in (("robust", "robustness"), ("external", "external")):
        if read(p) is not None:
            read(p).to_csv(f"results/{name}.csv", index=False)
    json.dump(dict(data=args.data, created=time.strftime("%Y-%m-%d %H:%M")),
              open("results/run_info.json", "w"), indent=2)
    print(f"Done in {(time.time() - t0) / 60:.1f} min. Results saved in results/")
    if comp:
        print(pd.concat(comp)[["Setting", "Policy", "AUC", "Caught incl. referral", "Questions per patient",
                               "Burden per patient"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
