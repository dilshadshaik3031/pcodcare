"""Shared look and feel for every page (PCODCare design)."""
import base64
import os
import streamlit as st

PAGES = [("home.py", "Home"), ("screening.py", "Risk Check"), ("learn.py", "Learn"),
         ("lifestyle.py", "Diet & Exercise"), ("resources.py", "Resources"), ("about.py", "About")]

LOGO = """<svg width="44" height="44" viewBox="0 0 48 48" fill="none" aria-hidden="true">
<path d="M24 42C15 36 8 27 8 14c6 1 12 5 16 12 4-7 10-11 16-12 0 13-7 22-16 28Z" stroke="#D9487A" stroke-width="3.2"
 stroke-linejoin="round"/>
<path d="M24 42c-3-6-4-12-2-19M24 42c3-6 4-12 2-19" stroke="#D9487A" stroke-width="2.4" stroke-linecap="round"/>
<path d="M24 26c-2-6-1-12 0-18 1 6 2 12 0 18Z" fill="#D9487A"/></svg>"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&display=swap');
:root{
  --brand:#D9487A; --brand-dark:#B93563; --brand-soft:#FCE9EF; --tint:#FDF7F8;
  --ink:#0F2233; --muted:#5E6B78; --line:#EFE4E7;
  --low:#2F7D62; --unclear:#B7791F; --high:#C2414B;
}
html, body, [class*="css"], .stMarkdown, button, input, label, p, li { font-family:'Figtree', system-ui, sans-serif; }
#MainMenu, footer, header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] { display:none !important; }
.block-container { max-width:1200px; padding-top:1.1rem; padding-bottom:3rem; }

/* ---------- navigation ---------- */
.brandmark { display:flex; align-items:center; gap:.55rem; text-decoration:none; }
.brandmark .word { font-size:1.75rem; color:var(--ink); letter-spacing:-.01em; }
.brandmark .word b { font-weight:800; } .brandmark .word span { font-weight:500; }
.navactive { display:block; text-align:center; color:var(--brand); font-weight:600; font-size:1.02rem;
             padding:.45rem 0 .35rem 0; border-bottom:3px solid var(--brand); }
[data-testid="stPageLink"] a { justify-content:center; padding:.4rem .3rem; border-radius:8px; }
[data-testid="stPageLink"] a p { font-size:1.02rem; color:var(--ink); font-weight:500; }
[data-testid="stPageLink"] a:hover { background:var(--tint); }
[data-testid="stPageLink"] a:hover p { color:var(--brand); }
.navline { border-bottom:1px solid var(--line); margin:.4rem -100vw 0 -100vw; }

/* ---------- buttons ---------- */
div.stButton > button { border-radius:12px; min-height:3rem; font-size:1rem; font-weight:600; }
div.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"] { background:var(--brand); border-color:var(--brand); color:#fff; }
div.stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover { background:var(--brand-dark); border-color:var(--brand-dark); }
div.stButton > button[kind="secondary"], [data-testid="stBaseButton-secondary"] { border:1.5px solid var(--line); background:#fff; color:var(--ink); }
div.stButton > button[kind="secondary"]:hover, [data-testid="stBaseButton-secondary"]:hover { border-color:var(--brand); color:var(--brand); background:var(--tint); }
div.stButton > button:focus-visible { outline:3px solid #F4A9C1; outline-offset:2px; }
.st-key-hero_cta button, .st-key-band_cta button, .st-key-nav_cta button, .st-key-start_cta button {
  border-radius:999px; min-height:3.6rem; font-size:1.2rem; padding:0 2.2rem; }
.st-key-nav_cta button { min-height:2.8rem; font-size:1rem; padding:0 1.3rem; }
[data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"] { display:none; }

/* ---------- home ---------- */
.hero-h { font-size:4.1rem; line-height:1.06; font-weight:800; color:var(--ink); letter-spacing:-.025em; margin:2.2rem 0 1.2rem 0; }
.hero-h em { font-style:normal; color:var(--brand); }
.hero-p { font-size:1.2rem; line-height:1.6; color:var(--muted); max-width:34ch; margin-bottom:1.8rem; }
.hero-img { width:100%; display:block;
  -webkit-mask-image:linear-gradient(to bottom, #000 80%, transparent); mask-image:linear-gradient(to bottom, #000 80%, transparent); }
.hero-meta { color:var(--muted); font-size:.95rem; margin-top:.9rem; }
.sec-h { font-size:2.1rem; font-weight:800; color:var(--ink); letter-spacing:-.015em; margin:4rem 0 .5rem 0; }
.sec-p { font-size:1.08rem; color:var(--muted); max-width:60ch; line-height:1.6; }
.how { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:2rem; margin-top:2rem; }
.how .n { width:2.4rem; height:2.4rem; border-radius:50%; background:var(--brand-soft); color:var(--brand); font-weight:800;
          display:flex; align-items:center; justify-content:center; margin-bottom:.9rem; }
.how b { display:block; font-size:1.2rem; color:var(--ink); margin-bottom:.35rem; }
.how p { color:var(--muted); line-height:1.6; margin:0; }
.why { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:2.4rem; margin-top:2rem; }
.why div { border-top:3px solid var(--brand); padding-top:1rem; }
.why b { display:block; font-size:1.15rem; color:var(--ink); margin-bottom:.4rem; }
.why p { color:var(--muted); line-height:1.6; margin:0; }
.st-key-band { background:var(--tint); border-radius:28px; padding:2.4rem 2.8rem; margin-top:4.5rem; }
.band-h { font-size:1.9rem; font-weight:800; color:var(--ink); margin:0 0 .3rem 0; padding:0; }
.band-p { color:var(--muted); font-size:1.05rem; margin:0; }

/* ---------- content pages ---------- */
.h1 { font-size:2.8rem; font-weight:800; color:var(--ink); line-height:1.12; margin:2rem 0 .9rem 0; letter-spacing:-.02em; max-width:22ch; }
.lead { font-size:1.15rem; color:var(--muted); line-height:1.65; max-width:64ch; }
.sec { font-size:1.4rem; font-weight:700; color:var(--ink); margin:2.4rem 0 .6rem 0; }
.body { font-size:1.04rem; color:var(--ink); line-height:1.7; max-width:70ch; }
.body li { margin-bottom:.35rem; }
.muted { color:var(--muted); }
.callout { border-left:4px solid var(--brand); padding:.8rem 1.1rem; background:var(--tint); border-radius:0 14px 14px 0;
           max-width:70ch; margin:1rem 0; color:var(--ink); line-height:1.6; }
.criteria { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1.2rem; margin:1.2rem 0; max-width:980px; }
.criteria div { background:var(--tint); border-radius:16px; padding:1.1rem 1.2rem; }
.criteria b { display:block; color:var(--ink); margin-bottom:.3rem; }
.criteria p { margin:0; color:var(--muted); line-height:1.55; font-size:.97rem; }
.linkrow { display:block; padding:1rem 0; border-bottom:1px solid var(--line); text-decoration:none; max-width:760px; }
.linkrow b { color:var(--ink); font-size:1.05rem; } .linkrow span { display:block; color:var(--muted); font-size:.95rem; margin-top:.2rem; }
.linkrow:hover b { color:var(--brand); }

/* ---------- risk check ---------- */
.st-key-riskpanel { background:#fff; border:1.5px solid var(--line); border-radius:22px; padding:1.3rem 1.5rem .6rem 1.5rem; margin-top:1.6rem; }
.steps { display:flex; gap:.5rem; margin:1.6rem 0 1.6rem 0; flex-wrap:wrap; }
.step { display:flex; align-items:center; gap:.5rem; padding:.4rem .9rem .4rem .45rem; border-radius:999px;
        font-size:.92rem; color:var(--muted); border:1.5px solid var(--line); background:#fff; }
.step b { display:inline-flex; width:1.6rem; height:1.6rem; border-radius:50%; align-items:center; justify-content:center;
          font-size:.82rem; background:var(--tint); color:var(--muted); }
.step.now { color:var(--ink); border-color:var(--brand); } .step.now b { background:var(--brand); color:#fff; }
.step.done b { background:var(--brand-soft); color:var(--brand); }
.predline { background:var(--tint); border-left:4px solid var(--brand); border-radius:0 12px 12px 0;
            padding:.75rem 1rem; color:var(--ink); font-size:.98rem; line-height:1.55; margin:0 0 1.4rem 0; max-width:62ch; }
.predline b { font-weight:700; }
.qmeta { color:var(--muted); font-size:.93rem; margin-bottom:.35rem; }
.qtext { font-size:2.1rem; line-height:1.22; font-weight:700; color:var(--ink); margin:0 0 .6rem 0; max-width:28ch; letter-spacing:-.01em; }
.qhelp { color:var(--muted); font-size:1.03rem; margin-bottom:1.2rem; max-width:60ch; line-height:1.6; }
.why-q { margin-top:1.4rem; padding:.8rem 1rem; background:var(--tint); border-radius:12px; color:var(--muted);
         font-size:.92rem; max-width:62ch; line-height:1.55; }
.panel { background:#fff; border:1.5px solid var(--line); border-radius:22px; padding:1.4rem 1.5rem 1rem 1.5rem; margin-top:1.6rem; }
.panel-label { color:var(--muted); font-size:.92rem; margin-bottom:.15rem; }
.risk-num { font-size:3.6rem; font-weight:800; line-height:1; color:var(--ink); letter-spacing:-.02em; }
.band-tag { display:inline-block; margin-left:.6rem; font-weight:700; font-size:.95rem; vertical-align:middle;
            padding:.2rem .7rem; border-radius:999px; }
.band-tag.low{color:var(--low); background:#E6F2EC;} .band-tag.unclear{color:var(--unclear); background:#F8EEDC;}
.band-tag.high{color:var(--high); background:#F8E1E4;}
.unc { font-size:.92rem; color:var(--muted); margin-top:.55rem; line-height:1.5; }
.bar { position:relative; display:flex; height:12px; margin:1.1rem 0 .35rem 0; }
.bar .z { height:100%; } .bar .z1{background:#CFE6DB; border-radius:6px 0 0 6px;} .bar .z2{background:#F3E6CB;}
.bar .z3{background:#F2D0D5; border-radius:0 6px 6px 0;}
.bar .mk { position:absolute; top:-6px; width:4px; height:24px; background:var(--ink); border-radius:2px;
           transform:translateX(-2px); transition:left .5s ease; }
.barlab { display:flex; justify-content:space-between; font-size:.8rem; color:var(--muted); }
.empty { color:var(--muted); font-size:.92rem; padding:1rem 0 .4rem 0; border-top:1px dashed var(--line); margin-top:1.3rem; }
.result-h { font-size:2.4rem; font-weight:800; color:var(--ink); margin:.2rem 0 .7rem 0; line-height:1.15; letter-spacing:-.015em; }
.result-p { font-size:1.08rem; color:var(--ink); max-width:56ch; line-height:1.65; }
.stats { display:flex; gap:2.4rem; margin:1.5rem 0; flex-wrap:wrap; }
.stats div { font-size:.92rem; color:var(--muted); } .stats b { display:block; font-size:1.8rem; color:var(--ink); font-weight:800; }
.plan { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1.6rem; margin:2rem 0; }
.plan div { background:var(--tint); border-radius:18px; padding:1.1rem 1.2rem; }
.plan b { display:block; color:var(--ink); font-size:1.05rem; margin:.3rem 0 .3rem 0; }
.plan span.n { color:var(--brand); font-weight:700; font-size:.9rem; }
.plan p { color:var(--muted); font-size:.95rem; line-height:1.55; margin:0; }

.tips { margin-top:2rem; background:var(--tint); border-radius:18px; padding:1.2rem 1.4rem; max-width:62ch; }
.tips b.t { display:block; font-size:1.1rem; color:var(--ink); margin-bottom:.5rem; }
.tips ul { margin:0 0 .2rem 1.1rem; padding:0; color:var(--ink); line-height:1.6; }
.note { font-size:.86rem; color:var(--muted); margin-top:4rem; padding-top:1.4rem; border-top:1px solid var(--line);
        max-width:none; line-height:1.6; }
@media (max-width: 860px){
  .hero-h{font-size:2.7rem;} .how,.why,.criteria,.plan{grid-template-columns:1fr;} .qtext{font-size:1.6rem;}
  .st-key-band{padding:1.6rem;} }
@media (prefers-reduced-motion: reduce){ .bar .mk{ transition:none; } }
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)


def img_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def nav(active):
    """Logo on the left, page links in the middle, a Risk Check button on the right."""
    cols = st.columns([2.1, .75, 1.0, .7, 1.35, .95, .7, 1.45], vertical_alignment="center")
    cols[0].markdown(f'<div class="brandmark">{LOGO}<div class="word"><b>PCOD</b><span>Care</span></div></div>',
                     unsafe_allow_html=True)
    for col, (page, label) in zip(cols[1:7], PAGES):
        if label == active:
            col.markdown(f'<span class="navactive">{label}</span>', unsafe_allow_html=True)
        else:
            col.page_link(page, label=label)
    if active != "Risk Check":
        if cols[7].button("Start Risk Check", key="nav_cta", type="primary", width="stretch"):
            st.session_state.autostart = True
            st.switch_page("screening.py")
    st.markdown('<div class="navline"></div>', unsafe_allow_html=True)


def footer():
    st.markdown('<div class="note"><b>PCODCare</b> is a research prototype for a study on adaptive PCOD screening at '
                'Auburn University at Montgomery. Its models were trained on synthetic data, so results are for '
                'demonstration only. It cannot diagnose PCOD or replace a doctor. Nothing you enter is stored after you '
                'close the page.</div>', unsafe_allow_html=True)