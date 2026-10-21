"""Diet & Exercise page: first steps for healthy habits, based on the 2023 International PCOS Guideline."""
import streamlit as st

import style

style.nav("Diet & Exercise")
st.markdown("""
<div class="h1">Diet and exercise for PCOD</div>
<div class="lead">Healthy habits are the first thing doctors recommend for PCOD, at every stage. They can help make
periods more regular, improve how your body uses insulin, and lower the long-term risk of diabetes and heart problems.
Small, steady changes work better than strict plans.</div>
<div class="callout">There is no single "PCOD diet" that works best for everyone. The international guideline
recommends a healthy eating pattern you can keep up, plus regular movement. If you are pregnant, have another health
condition, or are thinking about supplements, talk to your doctor first.</div>
""", unsafe_allow_html=True)

eat, move, rest, week = st.tabs(["Eating well", "Moving more", "Sleep and stress", "A sample week"])

with eat:
    st.markdown("""
<div class="sec">Build a balanced plate</div>
<div class="criteria">
  <div><b>Half: vegetables</b><p>Leafy greens, beans, okra, cauliflower, carrots, salad. Different colors through the
    week.</p></div>
  <div><b>A quarter: protein</b><p>Dal, chana, rajma, eggs, fish, chicken, paneer, tofu, Greek yogurt.</p></div>
  <div><b>A quarter: whole grains</b><p>Whole wheat roti, brown rice, millets like ragi or jowar, oats, quinoa.</p></div>
</div>

<div class="sec">Simple swaps</div>
<div class="body"><ul>
<li><b>White bread, maida, white rice</b> → whole wheat, millets, brown rice. They keep blood sugar steadier.</li>
<li><b>Sugary drinks and fruit juice</b> → water, buttermilk, unsweetened tea. Eat whole fruit instead of juice.</li>
<li><b>Fried snacks</b> → roasted chana, a handful of nuts, fruit, sprouts salad.</li>
<li><b>Sweets every day</b> → keep them for occasions. Fruit or a little dark chocolate in between.</li>
<li><b>Large late dinners</b> → an earlier, lighter dinner, with most of your food earlier in the day.</li>
</ul></div>

<div class="sec">Habits that help</div>
<div class="body"><ul>
<li>Eat regular meals and don't skip breakfast. Skipping meals often leads to overeating later.</li>
<li>Add fiber to every meal: vegetables, dal, whole grains, seeds. It keeps you full and helps blood sugar.</li>
<li>Use oil in small amounts and prefer healthier ones like mustard, olive or groundnut oil.</li>
<li>Avoid crash diets and cutting out whole food groups. They're hard to keep up and often backfire.</li>
<li>If you're above a healthy weight, losing even 5 to 10 percent of your body weight can improve periods and
symptoms. If you're at a healthy weight, the same habits still help.</li>
</ul></div>

<div class="sec">Meal ideas</div>
""", unsafe_allow_html=True)
    a, b = st.columns(2, gap="large")
    a.markdown("""
<div class="body"><b>Indian-style day</b><ul>
<li><b>Breakfast:</b> vegetable poha or besan chilla with curd</li>
<li><b>Lunch:</b> 2 whole wheat or millet rotis, dal, sabzi, salad</li>
<li><b>Snack:</b> roasted chana or a fruit with a few almonds</li>
<li><b>Dinner:</b> brown rice or quinoa with rajma or fish curry, and vegetables</li>
</ul></div>""", unsafe_allow_html=True)
    b.markdown("""
<div class="body"><b>Western-style day</b><ul>
<li><b>Breakfast:</b> oatmeal with berries and nuts, or eggs with whole grain toast</li>
<li><b>Lunch:</b> grilled chicken or bean salad with greens and quinoa</li>
<li><b>Snack:</b> Greek yogurt or an apple with peanut butter</li>
<li><b>Dinner:</b> salmon or tofu, roasted vegetables, and a small portion of brown rice</li>
</ul></div>""", unsafe_allow_html=True)

with move:
    st.markdown("""
<div class="sec">How much to aim for</div>
<div class="criteria">
  <div><b>At least 150 minutes a week</b><p>of moderate activity, like brisk walking, cycling or dancing. That's about
    30 minutes, 5 days a week. Or 75 minutes of vigorous activity, like running.</p></div>
  <div><b>Strength training 2 days a week</b><p>on days that aren't back to back. Squats, lunges, wall push-ups,
    resistance bands or weights.</p></div>
  <div><b>Sit less</b><p>Break up long sitting every hour with a few minutes of walking or stretching.</p></div>
</div>
<div class="body">If you're also trying to lose weight, the guideline suggests building up toward about 250 minutes of
moderate activity a week. Moderate means you can talk but not sing.</div>

<div class="sec">Starting from zero</div>
<div class="body"><ul>
<li>Begin with a 10-minute walk after one or two meals a day. Walking after meals also helps blood sugar.</li>
<li>Add 5 minutes every week or two until you reach 30 minutes most days.</li>
<li>Pick something you enjoy: dance, yoga, swimming, a sport, or walking with a friend. You'll keep doing it.</li>
<li>Do strength moves at home. 2 rounds of 10 squats, 10 wall push-ups and a 20-second plank is a good start.</li>
</ul></div>
<div class="body muted" style="margin-top:.6rem">Stop and get medical advice if you feel chest pain, faintness or
unusual shortness of breath while exercising.</div>
""", unsafe_allow_html=True)

with rest:
    st.markdown("""
<div class="sec">Sleep</div>
<div class="body">Aim for 7 to 9 hours a night, at regular times. Poor sleep makes it harder for your body to manage
insulin and appetite. Keep screens away for the last half hour before bed.</div>
<div class="sec">Stress and mood</div>
<div class="body">PCOD is linked to anxiety and low mood, and stress can make symptoms feel worse. Short daily habits
help: a walk outside, breathing exercises, yoga, journaling, or time with people you trust. If low mood or worry lasts
for more than two weeks, talk to your doctor. That's a normal part of PCOD care.</div>
""", unsafe_allow_html=True)

with week:
    st.markdown('<div class="sec">A gentle first week</div><div class="body">Adjust times to fit your day. Rest days are '
                'part of the plan.</div>', unsafe_allow_html=True)
    st.table({
        "Day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "Movement": ["Brisk walk, 30 min", "Strength at home, 20 min", "Yoga or easy cycling, 30 min",
                     "Strength at home, 20 min", "Brisk walk or dance, 30 min", "Longer walk or sport, 45 min",
                     "Rest or gentle stretching"],
        "Food focus": ["Swap one refined grain for a whole grain", "Add a vegetable to breakfast",
                       "Water instead of sugary drinks all day", "Protein with every meal", "Earlier, lighter dinner",
                       "Cook a new healthy recipe", "Plan meals for next week"],
    })
    st.markdown('<div class="body muted">That adds up to about 175 minutes of activity, including 2 strength sessions, '
                'which meets the guideline.</div>', unsafe_allow_html=True)

st.markdown('<div class="callout" style="margin-top:2.4rem">This page gives general advice based on the 2023 '
            'International Evidence-based Guideline for PCOS. It isn\'t a personal diet or exercise plan. A doctor or '
            'dietitian can tailor one to you.</div>', unsafe_allow_html=True)
style.footer()
