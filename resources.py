"""Resources page: when to see a doctor, how to prepare, trusted reading."""
import streamlit as st

import style

style.nav("Resources")
st.markdown("""
<div class="h1">Getting help</div>
<div class="lead">A risk check is a starting point. These resources help you take the next step with a doctor.</div>

<div class="sec">When to see a doctor</div>
<div class="body"><ul>
<li>Your periods have been irregular for several months, or have stopped without pregnancy</li>
<li>You've noticed new hair growth on your face or body, or ongoing acne or hair thinning</li>
<li>You've been trying to get pregnant for a year, or six months if you're over 35</li>
<li>Your risk check result was high or unclear</li>
<li>Very heavy bleeding, severe pelvic pain, or feeling faint. Get care promptly for these</li>
</ul></div>

<div class="sec">What to bring to your appointment</div>
<div class="body"><ul>
<li>Dates of your last few periods. A period tracking app makes this easy</li>
<li>A list of your symptoms and when they started</li>
<li>Any medicines you take, including birth control pills</li>
<li>Family history of PCOD, diabetes or thyroid problems</li>
<li>Any past blood test or ultrasound reports, and your risk check summary</li>
</ul></div>

<div class="sec">Trusted reading</div>
<a class="linkrow" href="https://www.womenshealth.gov/a-z-topics/polycystic-ovary-syndrome" target="_blank">
  <b>Office on Women's Health (U.S.)</b><span>Plain-language overview of symptoms, diagnosis and treatment.</span></a>
<a class="linkrow" href="https://www.acog.org/womens-health/faqs/polycystic-ovary-syndrome-pcos" target="_blank">
  <b>American College of Obstetricians and Gynecologists</b><span>Patient FAQ written by gynecologists.</span></a>
<a class="linkrow" href="https://www.nhs.uk/conditions/polycystic-ovary-syndrome-pcos/" target="_blank">
  <b>NHS (UK)</b><span>Symptoms, causes and treatment options explained simply.</span></a>
<a class="linkrow" href="https://www.monash.edu/medicine/mchri/pcos" target="_blank">
  <b>International PCOS Guideline, Monash University</b><span>The evidence-based guideline doctors follow, with
  patient resources.</span></a>

<div class="sec">Looking after your wellbeing</div>
<div class="body">Living with PCOD can be stressful, and it's linked to anxiety and low mood. If you're finding it hard,
tell your doctor. They can connect you with support, and you don't have to manage it alone.</div>
""", unsafe_allow_html=True)
style.footer()
