"""About the study: the idea behind the site, from the literature review."""
import streamlit as st

import style

style.nav("About")
st.markdown("""
<div class="h1">Knowing when to stop</div>
<div class="lead">Adaptive test selection for low-burden PCOD screening. A research project by Dilshad Shaik,
Department of Computer Science, Auburn University at Montgomery.</div>

<div class="sec">The problem</div>
<div class="body">PCOD, also called PCOS and since 2026 PMOS, affects more than one in ten women of reproductive age.
Diagnosing it usually needs a clinical history, hormone tests and often a transvaginal ultrasound. For many women
that full workup is expensive, slow or out of reach, and many cases go undiagnosed.</div>
<div class="body" style="margin-top:.8rem">Machine learning models for PCOD now report accuracies above 90%, but almost
all of them assume every measurement is known for every patient. Real screening doesn't work that way. Information
arrives step by step, some tests are far harder to get than others, and a clinician stops once the picture is clear
enough.</div>

<div class="sec">What earlier work leaves open</div>
<div class="body">The literature moves through three stages: static classifiers that use every feature, multimodal
systems that add even more data, and staged systems that start cheap and escalate when needed. The staged systems,
such as AutoPCOS and two-stage conformal triage, are the most realistic. But they send every patient through the same
fixed steps, and use uncertainty only once, at the escalation point. In the conformal triage study, escalating by
uncertainty alone did worse than simple risk ranking.</div>
<div class="body" style="margin-top:.8rem">Outside PCOD, active feature acquisition methods choose the next test for
each patient and learn when to stop. None has been applied to PCOD, and no PCOD study has tested how predictions
behave when inputs are missing, noisy or contradictory, or whether they settle as information accumulates.</div>

<div class="sec">Research question</div>
<div class="callout">Can a per-patient information-acquisition policy achieve accuracy comparable to full-feature PCOD
models while requiring fewer and lower-burden tests, and remain reliable when inputs are incomplete, noisy or
stripped of diagnosis-defining features?</div>

<div class="sec">How this site puts it into practice</div>
<div class="body"><b>Start from low burden.</b> Level 1 is only what a woman can report herself. Clinic exam and blood
tests are Level 2, ultrasound is Level 3, adapted from the difficulty levels of Li et al. (2025).</div>
<div class="body" style="margin-top:.6rem"><b>Choose the next question for this patient.</b> After every answer, the
model scores every remaining question by how much it is expected to move the estimate, imagining plausible answers
from real records, and asks the best one. This follows the greedy information approach of EDDI (Ma et al., 2019).</div>
<div class="body" style="margin-top:.6rem"><b>Stop on three signals together.</b> Risk must be clearly low or high,
a small ensemble of models must agree (uncertainty), and the estimate must have stopped moving (stability). This
responds directly to the finding that uncertainty alone is a poor basis for escalation.</div>
<div class="body" style="margin-top:.6rem"><b>Control for leakage.</b> Cycle irregularity, hirsutism, testosterone
and follicle count are part of how PCOD is diagnosed. A research setting removes them so the model cannot simply read
the answer back, and the evaluation reports results both ways.</div>

<div class="sec">Data</div>
<div class="body">The planned study collects de-identified hospital records at all three levels, aiming for more than
1,000 patients, after IRB approval. Until then, every number on this site comes from synthetic data with the same
columns. Because hospital records capture each patient at one visit, progressive acquisition is simulated by
revealing answers one at a time. The contribution is the first application and careful evaluation of adaptive
acquisition for PCOD, not a new general algorithm.</div>

<div class="sec">Key references</div>
<div class="body muted" style="font-size:.92rem">
Teede et al., Polyendocrine metabolic ovarian syndrome, the new name for PCOS, <i>The Lancet</i>, 2026.<br>
Hou et al., AutoPCOS: a stepwise multimodal framework for PCOS risk stratification, <i>Front. Endocrinol.</i>, 2026.<br>
Adegoke et al., Staged modelling with uncertainty-aware triage and conformal prediction for PCOS, medRxiv, 2025.<br>
Li et al., Intelligent detection for PCOS: taxonomy, datasets and detection tools, <i>Comput. Struct. Biotechnol. J.</i>, 2025.<br>
Katarynczuk et al., Adversarial validation reveals diagnostic workflow leakage in PCOS models, medRxiv, 2026.<br>
Ma et al., EDDI: efficient dynamic discovery of high-value information with partial VAE, ICML, 2019.<br>
Bernardino et al., Reinforcement learning for active modality selection during diagnosis, MICCAI, 2022.
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="sec">Results so far</div><div class="body">See how the adaptive method compares with the '
            'approaches in the literature, on accuracy, test burden, calibration, stability and robustness.</div>',
            unsafe_allow_html=True)
st.page_link("evaluation.py", label="View the evaluation  →")

style.footer()
