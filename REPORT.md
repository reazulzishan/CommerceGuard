# CommerceGuard — Project Report

**Author:** Reazul Akter Zishan · CS Funda (YouTube [@csfunda.official](https://www.youtube.com/@csfunda.official))
**Goal:** predict e-commerce losses *before* they happen — late deliveries, cancellations, refunds and unhappy customers — with honest, leakage-safe machine learning.

All numbers below are copied from the executed notebooks in `notebooks/`.

---

## Episode 1 · Delivery-promise risk (Olist, Brazil)
Notebook: `notebooks/01_commerceguard_delivery_risk.ipynb`

**Problem.** At checkout, will this order arrive after the promised date? Unit: one order. Primary metric: PR-AUC.
Rules: only checkout-time features, chronological split, test set used once.

**Data.** Olist public dataset: 99,441 orders (8 tables). After keeping delivered orders from 2017-01-01 to 2018-08-01: **89,852 orders**, late rate **6.83 %**. Promised delivery: median 24 days; actual: median 11 days (orders arrive 13 days early on median).

**Features.** 22 checkout-time features (distance, freight, product size, seller's past late rate and volume, state, month…). Leakage audit: none are known only after checkout.

**Split.** Chronological 70/15/15 plus a locked month:
train 58,587 (7.2 % late) · val 12,554 (9.7 %) · test 12,555 (4.0 %) · fresh July 2018: 6,156 (3.4 %).

**Models (validation PR-AUC).** always-on-time 0.097 · logistic regression 0.220 · LightGBM 0.299 (best iteration 78).
**Final test (used once).** LightGBM PR-AUC 0.102, ROC-AUC 0.737 (random = 0.040); calibrated LightGBM 0.092.
**Risk bands (test).** Low 3.3 % actual late · Moderate 11.3 % · High 20.0 %.
**Promise model.** Quantile regression on delivery days: promises 9.3 days shorter on average, but late rate rose from 4.0 % to 10.9 % — Experiment 1 failed, and the video explains why (delivery got faster in the test period; the late base rate fell from 9.7 % to 4.0 %).
**Experiment 2.** Added "how late is delivery right now" (known at checkout). Fresh July 2018 check: PR-AUC 0.066 vs 0.063 (random 0.034); promise 17.0 days with 5.8 % late vs Olist's 20.3 days with 3.4 % late.

**Lesson.** Real-world drift dominates; an honest locked test shows modest gains. The report keeps the failure visible.

---

## Episode 2 · From one model to a risk system (Bangladesh context)
Notebook: `notebooks/02_commerceguard_multimodel.ipynb`

### Model 1 · Customer voice (Daraz + Pickaboo reviews, Bangladesh)
- Data: Rashid et al. (2023), Mendeley Data, CC BY 4.0 — 78,130 reviews (Daraz 72,732, Pickaboo 5,398), 37.1 % Bangla.
- **Trap 1 · copies:** 13,983 duplicate texts → 64,147 unique reviews, 16.3 % negative.
- **Trap 2 · products:** split by product (GroupShuffleSplit): train 43,773 reviews / 1,652 products, val 9,691 / 354, test 10,683 / 355. No product appears on both sides.
- Unhappy reviews mention returns/refunds 15× and damaged products 12× more than happy ones.
- Text only (no star rating, since a chat has none): character + word TF-IDF with logistic regression.
- Validation PR-AUC: random 0.142 · Naive Bayes 0.702 · logistic regression 0.799.
- **Test (unseen products):** PR-AUC **0.821** (random 0.170), ROC-AUC 0.959, F1 0.774. Bangla reviews 0.859, English 0.774.
- It learned negation in Banglish: "valo na" (not good) pushes towards unhappy, "kharap na" (not bad) towards happy.

### Model 2 · Order risk in a cash-on-delivery market (Pakistan, 2016–2018)
- No public Bangladeshi order-outcome data exists, so the closest real dataset was used: 580,286 order items with clean outcomes (ok 53.7 %, cancel 34.7 %, refund 11.6 %).
- **Cash on delivery:** cancelled 8.1 % vs 57.8 % for online payments, but refunded **20.2 % vs 4.2 %** — the seller's problem.
- Customer history from the past only (cancellations from earlier days; refunds only from orders placed 30+ days earlier, via `merge_asof`).
- Chronological split: train 406,200 · val 87,043 · test 87,043.
- **Test (used once):** cancellation PR-AUC **0.789** (base 0.455); refund PR-AUC **0.349** (base 0.172). Isotonic calibration on validation only.

### The CommerceGuard engine
Expected loss per item = P(cancel) × handling cost + P(refund) × value × 15 % (costs are illustrative inputs).
Reviewing the top 5 / 10 / 20 % of items catches **36.8 / 51.3 / 64.9 %** of the loss.

### Demo
The customer-voice model scores a chat it never saw: 20 % → 90 % → 95 % → 94 % unhappy, and 0 % for a happy Banglish message.

### Honest limits
Reviews are a proxy for complaints; the order data is from Pakistan, not Bangladesh; costs are examples. Real data from Bangladeshi sellers would make this much stronger.

---

## Reproduce
```
python -m venv .venv && .venv/bin/pip install -r requirements.txt   # pandas, scikit-learn, lightgbm, shap, jupyterlab …
# place the datasets in data/raw/ (Olist) and data/raw_ep2/ (reviews CSV, Pakistan e-commerce CSV); they are not redistributed here
python notebooks/make_notebook.py && python notebooks/make_notebook_ep2.py
jupyter lab notebooks/
```

## Video production (in this repo)
- `recording/` — Playwright + JupyterLab live recording of each notebook, per-cell stills, highlight boxes.
- `video/`, `video_ep2/` — HyperFrames (HTML → video) builds: scenes, captions from the voice transcript, real cell captures with camera moves, charts drawn from the exported results.
- Licensed media (stock footage, music, sound effects) and datasets are **not** redistributed; see the video descriptions for credits.

## Credits
Olist Brazilian E-Commerce Public Dataset (Kaggle) · Rashid et al. (2023), Mendeley Data, doi:10.17632/rzjfg7t9kf.1, CC BY 4.0 · Pakistan's Largest E-Commerce Dataset (Kaggle) · Footage: Pexels · Music: Pixabay ("Science Ambient Technology" by BerryDeep).
