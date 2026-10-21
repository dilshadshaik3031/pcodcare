"""Screening page: one question at a time, with risk, uncertainty and stability."""
import os
import pandas as pd
import joblib
import altair as alt
import streamlit as st

import adaptive as A
import style

MODEL_FILE = "models/pcod_models.joblib"


@st.cache_resource
def load():
    return joblib.load(MODEL_FILE)


if not os.path.exists(MODEL_FILE):
    style.nav("Risk Check")
    st.error("No trained models found. Run `python train.py` in the terminal, then refresh this page.")
    st.stop()

bundle = load()
if "kits" not in bundle:
    style.nav("Risk Check")
    st.error("The saved models are from an older version. Run `python train.py` again, then refresh.")
    st.stop()


# ---------------------------------------------------------------- session state
def kit():
    return bundle["kits"][st.session_state.get("leakage_free", False)]


def new_session():
    k = kit()
    S = dict(level=1, values={}, done_keys=set(), answered_in_level=0, phase="intro", current=None,
             stop=None, gate_reason="", log=[],
             history=[dict(p=A.predict(k, 1, {}), unc=A.uncertainty(k, 1, {}), level=1, label="Start")])
    st.session_state.S = S


def start():
    advance()


def restart():
    new_session()
    advance()


def advance():
    S = st.session_state.S
    act = A.next_action(kit(), S)
    if act[0] == "ask":
        S["phase"], S["current"] = "ask", (act[1], act[2])
    elif act[0] == "checkpoint":
        S["phase"] = "checkpoint"
    elif act[0] == "escalate":
        if S["level"] < 3:
            S["phase"], S["gate_reason"] = "gate", act[1]
        else:
            S["phase"], S["stop"] = "done", ("refer", act[1])
    else:
        S["phase"], S["stop"] = "done", (act[1], act[2])


def record(key, vals, shown):
    """Save one answer (or a skip when vals is None), update all three signals and move on."""
    S, k = st.session_state.S, kit()
    item = A.BY_KEY[key]
    prev = S["history"][-1]
    S["done_keys"].add(key)
    if vals is None:
        S["history"].append(dict(p=prev["p"], unc=prev["unc"], level=S["level"], delta=0.0, answered=False,
                                 label=item["text"]))
    else:
        S["values"].update(vals)
        p = A.predict(k, S["level"], S["values"])
        S["history"].append(dict(p=p, unc=A.uncertainty(k, S["level"], S["values"]), level=S["level"],
                                 delta=p - prev["p"], answered=True, label=item["text"]))
        S["answered_in_level"] += 1
        S["since_check"] = S.get("since_check", 0) + 1
    S["log"].append((S["level"], item["text"], shown, S["history"][-1]["p"]))
    advance()


def go_next_level():
    S, k = st.session_state.S, kit()
    S["level"] += 1
    S["answered_in_level"] = 0
    S["since_check"] = 0
    S["history"].append(dict(p=A.predict(k, S["level"], S["values"]), unc=A.uncertainty(k, S["level"], S["values"]),
                             level=S["level"], label=f"Moved to {A.LEVEL_NAMES[S['level']].lower()}"))
    advance()


def keep_going():
    st.session_state.S["since_check"] = 0
    advance()


def see_result_now():
    S = st.session_state.S
    S["phase"], S["stop"] = "done", ("early", "You chose to see your result now.")


def finish_here():
    S = st.session_state.S
    S["phase"], S["stop"] = "done", ("declined", S["gate_reason"])


if "S" not in st.session_state:
    new_session()
S = st.session_state.S
last = S["history"][-1]
p, unc = last["p"], last["unc"]


# ---------------------------------------------------------------- pieces
def steps():
    html = '<div class="steps">'
    for lvl, name in A.LEVEL_NAMES.items():
        if lvl == S["level"] and S["phase"] != "done":
            cls = "now"
        elif lvl < S["level"] or (S["phase"] == "done" and lvl <= S["level"]):
            cls = "done"
        else:
            cls = ""
        html += f'<div class="step {cls}"><b>{lvl}</b>{name}</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)


def signals_text():
    moves = [abs(h["delta"]) for h in S["history"] if h.get("answered")]
    recent = moves[-A.STABLE_RUN:]
    if not moves:
        return ('<div class="unc">Starting point: the share of women with PCOD in the training data. '
                'It changes as you answer.</div>')
    stab = ("estimate settling" if len(recent) == A.STABLE_RUN and all(m < A.STABLE_EPS for m in recent)
            else "estimate still moving")
    sure = "models agree" if unc < A.UNC_MAX else "models still disagree"
    return (f'<div class="unc">Likely range {max(0, p - 2 * unc):.0%} to {min(1, p + 2 * unc):.0%} · '
            f'{sure} · {stab}</div>')


def risk_panel():
    band = A.risk_band(p)
    label = {"low": "Low", "unclear": "Unclear", "high": "High"}[band]
    lo, hi = int(A.LOW * 100), int(A.HIGH * 100)
    st.markdown(f"""
      <div class="panel-label">Current estimate</div>
      <div><span class="risk-num">{p:.0%}</span><span class="band-tag {band}">{label}</span></div>
      {signals_text()}
      <div class="bar"><div class="z z1" style="width:{lo}%"></div><div class="z z2" style="width:{hi - lo}%"></div>
        <div class="z z3" style="width:{100 - hi}%"></div><div class="mk" style="left:{p * 100:.1f}%"></div></div>
      <div class="barlab"><span>Low, under {lo}%</span><span>Unclear</span><span>High, over {hi}%</span></div>
    """, unsafe_allow_html=True)

    h = pd.DataFrame({"Step": range(len(S["history"])), "Risk": [x["p"] for x in S["history"]],
                      "Low": [max(0, x["p"] - 2 * x["unc"]) for x in S["history"]],
                      "High": [min(1, x["p"] + 2 * x["unc"]) for x in S["history"]],
                      "What happened": [x["label"] for x in S["history"]]})
    if len(S["history"]) < 2:
        st.markdown('<div class="empty">A chart of how your estimate moves will appear here after your first '
                    'answer.</div>', unsafe_allow_html=True)
        return
    x = alt.X("Step:Q", axis=alt.Axis(title="Answers so far", tickMinStep=1, format="d", grid=False),
              scale=alt.Scale(domain=[0, max(4, len(S["history"]) - 1)]))
    yax = alt.Axis(format="%", title=None, grid=False)
    band_ = alt.Chart(h).mark_area(color="#D9487A", opacity=0.12).encode(
        x=x, y=alt.Y("Low:Q", scale=alt.Scale(domain=[0, 1]), axis=yax), y2="High:Q")
    base = alt.Chart(h).encode(x=x, y=alt.Y("Risk:Q", scale=alt.Scale(domain=[0, 1]), axis=yax),
                               tooltip=[alt.Tooltip("What happened:N"), alt.Tooltip("Risk:Q", format=".0%")])
    line = base.mark_line(color="#D9487A", strokeWidth=2.5) + base.mark_circle(color="#D9487A", size=55)
    rules = alt.Chart(pd.DataFrame({"y": [A.LOW, A.HIGH]})).mark_rule(strokeDash=[4, 4], color="#9AA9A4").encode(y="y:Q")
    st.markdown('<div class="panel-label" style="margin-top:1.6rem">How the estimate has moved</div>',
                unsafe_allow_html=True)
    st.altair_chart((rules + band_ + line).properties(height=210).configure_view(stroke=None), width="stretch")

    if S["log"]:
        with st.expander(f"Your answers ({len(S['log'])})"):
            for lvl, text, shown, pp in S["log"]:
                st.markdown(f"**{text}**  \n{shown} · estimate {pp:.0%}")


def ask_card():
    key, score = S["current"]
    item = A.BY_KEY[key]
    n = len(S["log"]) + 1
    answered = sum(1 for h in S["history"] if h.get("answered"))
    if answered:
        band = A.risk_band(p)
        label = {"low": "low", "unclear": "unclear", "high": "high"}[band]
        reason = ("it is between low and high risk" if band == "unclear"
                  else "the models don't fully agree yet")
        st.markdown(f'<div class="predline"><b>Prediction after {answered} answer{"s" if answered > 1 else ""}: '
                    f'{p:.0%}, {label}.</b> That isn\'t clear enough yet because {reason}, so one more answer is '
                    f'needed.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="qmeta">Question {n} · Level {S["level"]}, {A.LEVEL_NAMES[S["level"]].lower()}</div>'
                f'<div class="qtext">{item["text"]}</div>'
                + (f'<div class="qhelp">{item["help"]}</div>' if item["help"] else '<div style="height:.6rem"></div>'),
                unsafe_allow_html=True)

    kind = item["kind"]
    if kind == "yn":
        c1, c2, c3 = st.columns(3)
        c1.button("Yes", key=f"{key}_y", width="stretch", on_click=record, args=(key, {item["cols"][0]: 1.0}, "Yes"))
        c2.button("No", key=f"{key}_n", width="stretch", on_click=record, args=(key, {item["cols"][0]: 0.0}, "No"))
        c3.button("Not sure", key=f"{key}_s", width="stretch", on_click=record, args=(key, None, "Not sure"))
    elif kind == "choice":
        for i, (opt, code) in enumerate(item["options"].items()):
            st.button(opt, key=f"{key}_{i}", width="stretch",
                      on_click=record, args=(key, dict(zip(item["cols"], map(float, code))), opt))
        st.button("I don't know", key=f"{key}_skip", on_click=record, args=(key, None, "Don't know"))
    else:
        if kind == "num":
            v = st.number_input(item["unit"].capitalize() if item.get("unit") else "Your answer",
                                min_value=item["lo"], max_value=item["hi"], value=None, step=item["step"],
                                key=f"{key}_v")
            vals = None if v is None else {item["cols"][0]: float(v)}
            shown = "" if v is None else f"{v:g} {item.get('unit', '')}".strip()
        else:
            a, b = st.columns(2)
            v1 = a.number_input(item["labels"][0], min_value=item["lo"][0], max_value=item["hi"][0], value=None,
                                step=item["step"][0], key=f"{key}_v1")
            v2 = b.number_input(item["labels"][1], min_value=item["lo"][1], max_value=item["hi"][1], value=None,
                                step=item["step"][1], key=f"{key}_v2")
            vals = None if v1 is None or v2 is None else {item["cols"][0]: float(v1), item["cols"][1]: float(v2)}
            shown = "" if vals is None else f"{item['labels'][0]} {v1:g}, {item['labels'][1]} {v2:g}"
        c1, c2, _ = st.columns([1, 1, 2])
        if c1.button("Continue", key=f"{key}_go", type="primary", width="stretch"):
            if vals is None:
                st.warning("Enter a value to continue, or choose Skip.")
            else:
                record(key, vals, shown)
                st.rerun()
        c2.button("Skip", key=f"{key}_skip", width="stretch", on_click=record, args=(key, None, "Skipped"))

    st.markdown(f'<div class="why-q">Asked now because your answer is expected to shift the estimate by about '
                f'{score * 100:.0f} percentage points, more than any other question at this level.</div>',
                unsafe_allow_html=True)
    if sum(1 for h in S["history"] if h.get("answered")):
        st.button("Stop and see my result now", key=f"{key}_now", type="tertiary", on_click=see_result_now)


def checkpoint_card():
    answered = sum(1 for h in S["history"] if h.get("answered"))
    first = answered <= A.ROUND
    head = (f"Here's your estimate from your top {answered} answers" if first
            else f"Here's your estimate from {answered} answers")
    band = A.risk_band(p)
    why = ("the models don't agree enough yet" if band != "unclear" else "it is between low and high risk")
    st.markdown(f'<div class="qmeta">More information needed</div>'
                f'<div class="qtext">{head}: {p:.0%}</div>'
                f'<div class="qhelp">That isn\'t clear enough to give you a result, because {why}. Answering a few '
                f'more questions would make it clearer. You can also see your result now.</div>',
                unsafe_allow_html=True)
    c1, c2, _ = st.columns([1.4, 1.3, 1.3])
    c1.button(f"Answer {A.ROUND} more questions", type="primary", width="stretch", on_click=keep_going)
    c2.button("See my result now", width="stretch", on_click=see_result_now)


def gate_card():
    nxt = S["level"] + 1
    what = {2: ("results from a clinic visit", "a physical exam or blood tests"),
            3: ("ultrasound results", "a pelvic ultrasound report")}[nxt]
    st.markdown(f'<div class="qmeta">{S["gate_reason"]}</div>'
                f'<div class="qtext">Do you have {what[0]}?</div>'
                f'<div class="qhelp">Your estimate is {p:.0%}, which is still unclear. Information from {what[1]} '
                f'would help the most. You only need to enter the results you have.</div>', unsafe_allow_html=True)
    c1, c2, _ = st.columns([1.2, 1.2, 1.6])
    c1.button("Yes, add them", type="primary", width="stretch", on_click=go_next_level)
    c2.button("No, finish here", width="stretch", on_click=finish_here)


def done_card():
    status, reason = S["stop"]
    lvl = S["level"]
    nxt_test = {1: "a clinic visit with blood tests", 2: "an ultrasound", 3: "a doctor's review"}[lvl]
    head, body = {
        "low": ("Your estimated risk is low",
                "If your periods change or new symptoms appear, it is still worth talking to a doctor."),
        "high": ("Your estimated risk is high",
                 "Please book a visit with a doctor or gynecologist. Bring this summary with you so they can see "
                 "what you have already shared."),
        "refer": ("Your result is unclear",
                  "We have used all the information available, and the picture is still mixed. A doctor should "
                  "review it with you."),
        "early": ("Your result is not clear yet",
                  "With the answers so far, your estimate sits in the unclear range. Answering more questions, or "
                  f"adding results from {nxt_test}, would make it clearer."),
        "declined": ("Your result is still unclear",
                     f"The most useful next step would be {nxt_test}. You can come back and continue once you "
                     f"have the results."),
    }[status]
    answered = sum(1 for h in S["history"] if h.get("answered"))
    possible = len(kit()["items"])
    st.markdown(f'<div class="qmeta">{reason}</div><div class="result-h">{head}</div>'
                f'<div class="result-p">{body} Only a doctor can diagnose PCOD.</div>'
                f'<div class="stats"><div><b>{answered}</b>questions answered</div>'
                f'<div><b>{possible - answered}</b>questions not needed</div>'
                f'<div><b>Level {lvl}</b>reached of 3</div></div>', unsafe_allow_html=True)
    tips = {
        "low": ("Habits that help you stay well",
                ["Keep moving: about 30 minutes of brisk walking, 5 days a week",
                 "Build meals around vegetables, protein and whole grains",
                 "Keep track of your periods so you notice any change early"]),
        "high": ("First steps while you arrange a doctor's visit",
                 ["Start with a 10-minute walk after meals, building up to 30 minutes most days",
                  "Swap refined grains and sugary drinks for whole grains and water",
                  "Note your period dates and symptoms to share with your doctor"]),
    }.get(status, ("First steps you can start now",
                   ["Aim for 150 minutes of activity a week, plus 2 short strength sessions",
                    "Fill half your plate with vegetables and choose whole grains",
                    "Get 7 to 9 hours of sleep and keep regular meal times"]))
    st.markdown(f'<div class="tips"><b class="t">{tips[0]}</b><ul>' + "".join(f"<li>{t}</li>" for t in tips[1]) +
                '</ul></div>', unsafe_allow_html=True)
    st.page_link("lifestyle.py", label="See the full diet and exercise guide  →")
    st.button("Start over", type="primary", on_click=restart)


def on_leak_toggle():
    started = st.session_state.S["phase"] != "intro"
    new_session()
    if started:
        advance()


def intro():
    st.markdown('<div class="h1">Check your PCOD risk, one question at a time</div>'
                '<div class="lead">Start with questions you can answer at home. After every answer your estimate '
                'updates, and the next question is the one most likely to make it clearer. The tool asks for clinic '
                'or ultrasound results only if they would change the answer, and stops as soon as the picture is '
                'clear.</div>'
                '<div class="plan">'
                '<div><span class="n">Level 1</span><b>About you</b><p>One question at a time, with a prediction after '
                'every answer. It stops as soon as your result is clear.</p></div>'
                '<div><span class="n">Level 2</span><b>Clinic results</b><p>Only if the result is still unclear. '
                'Enter whichever exam and blood test results you have.</p></div>'
                '<div><span class="n">Level 3</span><b>Ultrasound</b><p>Only if it would still help. Values come '
                'from a pelvic ultrasound report.</p></div></div>', unsafe_allow_html=True)
    c1, _ = st.columns([1, 3])
    c1.button("Start screening", type="primary", width="stretch", on_click=start)
    st.markdown('<div class="qhelp" style="margin-top:1rem">You can skip any question. This gives an estimate, '
                'not a diagnosis.</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- page
style.nav("Risk Check")
if st.session_state.pop("autostart", False) and S["phase"] == "intro":
    advance()
if S["phase"] == "intro":
    intro()
    style.footer()
    st.stop()

left, gap, right = st.columns([1.55, 0.12, 1])
with left:
    steps()
    if S["phase"] == "ask":
        ask_card()
    elif S["phase"] == "checkpoint":
        checkpoint_card()
    elif S["phase"] == "gate":
        gate_card()
    else:
        done_card()
    if S["phase"] != "done" and S["log"]:
        st.button("Start over", key="restart_small", on_click=restart)
with right, st.container(key="riskpanel"):
    risk_panel()
    with st.expander("Research settings"):
        st.toggle("Leave out diagnosis-defining questions", key="leakage_free", on_change=on_leak_toggle,
                  help="Removes questions that are part of how PCOD is diagnosed (cycle pattern, excess hair, "
                       "testosterone, follicle count and others), so the model cannot just read the answer back. "
                       "Starts a new screening.")
        st.caption(f"Stops when risk is below {A.LOW:.0%} or above {A.HIGH:.0%} and the models agree "
                   f"(spread under {A.UNC_MAX:.0%}), or when {A.STABLE_RUN} answers in a row move the estimate "
                   f"by less than {A.STABLE_EPS:.0%}.")

style.footer()