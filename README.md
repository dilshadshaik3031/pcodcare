# PCODCare (research prototype)

A local website built on the proposed direction of the literature review
"Knowing When to Stop: Adaptive Test Selection for Low-Burden PCOD Screening".

Trained on SYNTHETIC data. Not a diagnosis. Not medical advice.

## Pages
- Home: hero, how it works, why it's different
- Risk Check: one question at a time; risk updates after every answer; stops on risk + uncertainty + stability;
  research setting for a leakage-aware mode without diagnosis-defining questions
- Learn: what PCOD is, signs, Rotterdam criteria, why early checks matter, management
- Resources: when to see a doctor, what to bring, trusted reading
- About: the study, research question and design, with a link to the Evaluation results

## Files
- app.py           page menu (run this)
- home.py, learn.py, resources.py   new pages
- assets/          hero image
- screening.py     Risk Check page
- evaluation.py    Evaluation page (reads results/)
- about.py         About page
- style.py         colors and fonts
- adaptive.py      question bank, next-question choice, the three stopping signals, model training
- pcod_core.py     column lists, leakage list, text-to-number encoding
- train.py         trains the website models
- evaluate.py      runs the experiments for the Evaluation page
- data/            the Excel data
- results/         evaluation results (included from a small sample run)

## Run (VS Code terminal, Windows)
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python train.py
    python evaluate.py        (optional: refreshes the Evaluation page, a few minutes)
    streamlit run app.py

Mac/Linux: use python3 and `source venv/bin/activate`.
Open http://localhost:8501 if the browser does not open by itself. Stop with Ctrl+C.

## Real data later
Put the de-identified file in data/ with the same column names, then:
    python train.py --data data/your_file.xlsx
    python evaluate.py --data data/your_file.xlsx --n 1000
Keep real patient data on your own machine only.
