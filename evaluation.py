"""Evaluation page: results produced by evaluate.py (Section 9.3 of the review)."""
import json
import os
import altair as alt
import pandas as pd
import streamlit as st

import style

style.nav("About")
st.markdown('<div class="h1">How the adaptive policy compares</div>'
            '<div class="lead">Each policy screens the same held-out patients. Answers are revealed one question at a '
            'time from their recorded data, so the comparison shows how much information each policy needs and how '
            'well it does with it.</div>', unsafe_allow_html=True)

if not os.path.exists("results/comparison.csv"):
    st.info("No results yet. In the terminal, run `python evaluate.py`, then refresh this page. "
            "It takes about five minutes.")
    st.stop()

cmp = pd.read_csv("results/comparison.csv")
rob = pd.read_csv("results/robustness.csv") if os.path.exists("results/robustness.csv") else pd.DataFrame()
ext = pd.read_csv("results/external.csv") if os.path.exists("results/external.csv") else pd.DataFrame()
info = json.load(open("results/run_info.json")) if os.path.exists("results/run_info.json") else {}

st.markdown(f'<div class="callout">Results below come from <b>{info.get("data", "the dataset")}</b>, '
            f'{int(cmp["Patients"].iloc[0])} held-out patients across 5 folds, run on {info.get("created", "")}. '
            f'With synthetic data these numbers only show that the pipeline works. They are not study findings.</div>',
            unsafe_allow_html=True)

PROPOSED = "Proposed (risk + uncertainty + stability)"
setting = st.segmented_control("Features", ["All features", "Leakage-free"], default="All features",
                               help="Leakage-free removes the diagnosis-defining (Rotterdam) questions, as the review "
                                    "recommends reporting both.")
setting = setting or "All features"
d = cmp[cmp["Setting"] == setting].copy()

# ---------------------------------------------------------------- headline
pr = d[d["Policy"] == PROPOSED].iloc[0]
full = d[d["Policy"] == "Full-feature model"].iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("AUC, proposed", f"{pr['AUC']:.3f}", f"{pr['AUC'] - full['AUC']:+.3f} vs full model", delta_color="off")
c2.metric("Questions per patient", f"{pr['Questions per patient']:.1f}",
          f"{pr['Questions per patient'] - full['Questions per patient']:+.1f} vs full model", delta_color="off")
c3.metric("Burden per patient", f"{pr['Burden per patient']:.1f}",
          f"{100 * (pr['Burden per patient'] / full['Burden per patient'] - 1):+.0f}% vs full model", delta_color="off")
c4.metric("Reached ultrasound", f"{pr['Reached Level 3 (%)']:.0f}%")

# ---------------------------------------------------------------- AUC vs burden
st.markdown('<div class="sec">Accuracy against burden</div>'
            '<div class="body muted">Further up is more accurate, further left asks for less. Burden uses the Li et al. '
            'levels: 1 point per self-reported answer, 2 per clinic result, 3 per ultrasound finding.</div>',
            unsafe_allow_html=True)
d["Type"] = d["Policy"].map(lambda x: "Proposed" if x == PROPOSED else "Baseline")
pts = alt.Chart(d).mark_circle(size=170).encode(
    x=alt.X("Burden per patient:Q", title="Average burden per patient", scale=alt.Scale(zero=True)),
    y=alt.Y("AUC:Q", scale=alt.Scale(zero=False), title="AUC"),
    color=alt.Color("Type:N", scale=alt.Scale(domain=["Proposed", "Baseline"], range=["#D9487A", "#9AA9A4"]),
                    legend=None),
    tooltip=["Policy", alt.Tooltip("AUC:Q", format=".3f"), alt.Tooltip("Burden per patient:Q", format=".1f"),
             alt.Tooltip("Questions per patient:Q", format=".1f")])
labels = pts.mark_text(align="left", dx=10, fontSize=12, color="#1E2B33").encode(text="Policy:N")
st.altair_chart((pts + labels).properties(height=360).configure_view(stroke=None), width="stretch")

# ---------------------------------------------------------------- full table
st.markdown('<div class="sec">All metrics</div>', unsafe_allow_html=True)
cols = ["Policy", "AUC", "Sensitivity", "Specificity", "Caught incl. referral", "Brier", "ECE",
        "Questions per patient", "Burden per patient", "Reached Level 2 (%)", "Reached Level 3 (%)",
        "Flips across 50%", "Movement in last 3 answers"]
fmt = {c: "{:.3f}" for c in ["AUC", "Sensitivity", "Specificity", "Caught incl. referral", "Brier", "ECE",
                             "Movement in last 3 answers", "Flips across 50%"]}
fmt.update({c: "{:.1f}" for c in ["Questions per patient", "Burden per patient", "Reached Level 2 (%)",
                                  "Reached Level 3 (%)"]})
st.dataframe(d[cols].style.format(fmt), hide_index=True, width="stretch")
with st.expander("What the columns mean"):
    st.markdown("""
- **AUC**: how well the final risk separates PCOD from non-PCOD (0.5 is guessing, 1 is perfect).
- **Sensitivity / Specificity**: share of PCOD and non-PCOD patients classified correctly at a 50% cut-off.
- **Caught incl. referral**: PCOD patients either flagged as high risk or sent to a doctor as unclear. This is the
  number that matters most for screening safety.
- **Brier / ECE**: calibration, whether a "30% risk" really means about 30%. Lower is better.
- **Burden**: total cost of the information used, by the Li et al. difficulty levels.
- **Flips across 50%**: how often the estimate switched sides on the way. **Movement in last 3 answers**: how much it
  was still changing when the policy stopped. Lower means a more stable estimate.
""")

# ---------------------------------------------------------------- leakage
both = cmp.pivot_table(index="Policy", columns="Setting", values="AUC").reset_index()
if {"All features", "Leakage-free"} <= set(both.columns):
    st.markdown('<div class="sec">Effect of removing diagnosis-defining features</div>'
                '<div class="body muted">If AUC drops a lot without them, part of the accuracy came from the model '
                'reading the diagnosis back.</div>', unsafe_allow_html=True)
    long = both.melt("Policy", var_name="Setting", value_name="AUC")
    bars = alt.Chart(long).mark_bar().encode(
        y=alt.Y("Policy:N", title=None, sort="-x"), x=alt.X("AUC:Q", scale=alt.Scale(domain=[0.5, 1])),
        yOffset="Setting:N",
        color=alt.Color("Setting:N", scale=alt.Scale(range=["#D9487A", "#C9B37E"]), legend=alt.Legend(orient="top")),
        tooltip=["Policy", "Setting", alt.Tooltip("AUC:Q", format=".3f")])
    st.altair_chart(bars.properties(height=320).configure_view(stroke=None), width="stretch")

# ---------------------------------------------------------------- robustness
if not rob.empty:
    st.markdown('<div class="sec">Robustness to imperfect answers</div>'
                f'<div class="body muted">{int(rob["Patients"].iloc[0])} held-out patients, with answers hidden, '
                'measurements made noisy, or yes/no answers flipped to simulate contradictions.</div>',
                unsafe_allow_html=True)
    kind = st.segmented_control("Problem", ["missing", "noisy", "contradictory"], default="missing",
                                format_func=lambda k: {"missing": "Missing answers", "noisy": "Noisy measurements",
                                                       "contradictory": "Contradictory answers"}[k])
    kind = kind or "missing"
    r = rob[rob["Corruption"] == kind]
    metric = st.radio("Show", ["AUC", "Caught incl. referral", "Questions per patient"], horizontal=True)
    ch = alt.Chart(r).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X("Level:Q", title="Share of answers affected" if kind != "noisy" else "Noise level (relative)",
                axis=alt.Axis(format="%")),
        y=alt.Y(f"{metric}:Q", scale=alt.Scale(zero=False)),
        color=alt.Color("Policy:N", scale=alt.Scale(range=["#9AA9A4", "#C9B37E", "#D9487A"]),
                        legend=alt.Legend(orient="top", title=None)),
        tooltip=["Policy", alt.Tooltip(f"{metric}:Q", format=".3f")])
    st.altair_chart(ch.properties(height=300).configure_view(stroke=None), width="stretch")

# ---------------------------------------------------------------- external
if not ext.empty:
    e = ext.iloc[0]
    st.markdown('<div class="sec">External check</div>'
                f'<div class="body muted">Trained on sites {e["Train"]}, tested on site {e["Test"]}, which the models '
                'never saw. With real data this is where a second hospital belongs.</div>', unsafe_allow_html=True)
    st.dataframe(ext[["Policy", "Patients", "AUC", "Sensitivity", "Caught incl. referral", "ECE",
                      "Questions per patient", "Burden per patient"]].style.format(
        {"AUC": "{:.3f}", "Sensitivity": "{:.3f}", "Caught incl. referral": "{:.3f}", "ECE": "{:.3f}",
         "Questions per patient": "{:.1f}", "Burden per patient": "{:.1f}"}), hide_index=True, width="stretch")

st.markdown('<div class="note">Progressive acquisition is simulated: the data records each patient at a single visit, '
            'and answers are revealed one question at a time. Policies: full-feature model; fixed low-to-high order '
            '(AutoPCOS); two-stage class-conditional conformal escalation, α = 0.05 (Adegoke et al.); random order; '
            'greedy expected-move selection stopping on risk alone (EDDI-style); and the proposed policy, which stops '
            'on risk, uncertainty and stability together.</div>', unsafe_allow_html=True)

style.footer()
