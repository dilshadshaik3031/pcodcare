"""Learn page: plain-language background on PCOD."""
import streamlit as st

import style

style.nav("Learn")
st.markdown("""
<div class="h1">What is PCOD?</div>
<div class="lead">Polycystic ovarian disease is one of the most common hormone conditions in women of reproductive
age, affecting more than one in ten women worldwide. You may also see it called PCOS (polycystic ovary syndrome). In
2026 an international group of experts renamed it PMOS, polyendocrine metabolic ovarian syndrome, to reflect that it
affects hormones and metabolism, not just the ovaries. All three names describe the same condition.</div>

<div class="sec">Common signs</div>
<div class="body">PCOD looks different from person to person. Common signs include:
<ul>
<li>Irregular periods, or periods that stop for months</li>
<li>Extra hair on the face, chest or belly</li>
<li>Acne that keeps coming back</li>
<li>Thinning hair on the scalp</li>
<li>Weight gain, or finding it hard to lose weight</li>
<li>Dark, velvety patches of skin on the neck, armpits or skin folds</li>
<li>Difficulty getting pregnant</li>
</ul>
Having one or two of these doesn't mean you have PCOD, and some women with PCOD have very few of them.</div>

<div class="sec">How doctors diagnose it</div>
<div class="body">Most doctors use the Rotterdam criteria. A diagnosis needs at least two of these three, after other
causes have been ruled out:</div>
<div class="criteria">
  <div><b>Irregular ovulation</b><p>Periods that are irregular, far apart or missing.</p></div>
  <div><b>Signs of high androgens</b><p>Extra hair growth or acne, or high androgen levels such as testosterone in a
    blood test.</p></div>
  <div><b>Polycystic ovaries</b><p>Many small follicles or larger ovaries on an ultrasound.</p></div>
</div>
<div class="body">"Ruling out other causes" matters. Thyroid problems, high prolactin and some adrenal conditions can
look like PCOD, which is why doctors usually order blood tests before deciding.</div>

<div class="sec">Why it's worth checking early</div>
<div class="body">PCOD is linked to a higher chance of type 2 diabetes, high cholesterol and blood pressure, problems
with the lining of the womb when periods are very infrequent, and difficulty getting pregnant. It's also linked to
anxiety and low mood. Many women go years without a diagnosis. Knowing early means you can work with a doctor on the
things that help most, before problems build up.</div>

<div class="sec">How it's managed</div>
<div class="body">There is no single cure, but it can be managed well. Depending on your symptoms and goals, a doctor
may suggest changes to diet, activity and sleep, medicines to regulate periods or reduce hair growth and acne, medicines
that help the body use insulin, or fertility treatment if you're trying to get pregnant. The right plan depends on you,
so it's a decision to make with your doctor.</div>
<div class="callout">This page gives general information. It isn't medical advice. If you're worried about any of
these signs, talk to a doctor or gynecologist.</div>
""", unsafe_allow_html=True)
style.footer()
