"""Home page."""
import streamlit as st

import style


def go():
    st.session_state.autostart = True
    st.switch_page("screening.py")


style.nav("Home")

left, right = st.columns([1.08, 1], vertical_alignment="center", gap="large")
with left:
    st.markdown('<div class="hero-h">Understand Your<br><em>PCOD Risk</em> Earlier</div>'
                '<div class="hero-p">A free screening that starts with simple questions about you and asks for tests '
                'only when they would change the answer.</div>', unsafe_allow_html=True)
    if st.button("Start Risk Check  →", key="hero_cta", type="primary"):
        go()
    st.markdown('<div class="hero-meta">Takes a few minutes · Skip anything you don\'t know · Not a diagnosis</div>',
                unsafe_allow_html=True)
with right:
    st.markdown(f'<img class="hero-img" alt="" src="data:image/jpeg;base64,{style.img_b64("assets/hero.jpg")}">',
                unsafe_allow_html=True)

st.markdown("""
<div class="sec-h">How it works</div>
<div class="sec-p">Most PCOD checks ask everyone for everything. This one asks for the next thing only if it is
likely to change your result.</div>
<div class="how">
  <div><div class="n">1</div><b>Answer questions about you</b>
    <p>It asks the most useful question for you, predicts, and stops if the result is clear. If not, it asks the next one.</p></div>
  <div><div class="n">2</div><b>Add more only if needed</b>
    <p>If questions about you aren't enough, it asks whether you have exam or blood test results to add.</p></div>
  <div><div class="n">3</div><b>Add ultrasound only if it helps</b>
    <p>Ultrasound is the costliest step, so it comes last and only when the earlier answers aren't enough.</p></div>
</div>

<div class="sec-h">Why it's different</div>
<div class="why">
  <div><b>One question at a time</b><p>The next question is chosen for you, based on what is most likely to make
    your estimate clearer.</p></div>
  <div><b>Only the tests you need</b><p>It stops as soon as the picture is clear, so many people never need blood
    tests or a scan to get a useful answer.</p></div>
  <div><b>Practical next steps</b><p>Every result comes with first steps for diet and exercise, based on the
    international PCOS guideline.</p></div>
</div>
""", unsafe_allow_html=True)

with st.container(key="band"):
    t, b = st.columns([2.2, 1], vertical_alignment="center")
    t.markdown('<h3 class="band-h">Ready to check?</h3><p class="band-p">Start with a few questions. You can stop or '
               'skip at any point.</p>', unsafe_allow_html=True)
    if b.button("Start Risk Check  →", key="band_cta", type="primary", width="stretch"):
        go()

style.footer()