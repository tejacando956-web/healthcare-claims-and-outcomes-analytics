# Healthcare Claims and Cost Analytics: Claim Denials, Cost per Member and Readmissions

## In simple words — what is this project?

This project is my CVS Health data analyst job, done as one project.

I took 4 lists of healthcare data — patients, doctors, insurance claims and hospital visits.
I joined them together and cleaned them (removed duplicates, fixed missing values, checked wrong amounts).
Then I answered the normal questions a healthcare company asks every week:
- How much money did we pay on claims? ($1.69 million)
- How many claims were denied, and why? (11.5% denied; the top reason is missing prior authorization, 31.7%)
- How much does one member cost per month? ($235.39 — this is called PMPM)
- Which diseases cost the most money? (Diabetes, heart failure and kidney disease = 59.1% of all cost)
- How many patients came back to hospital within 30 days? (25.5% of hospital patients — readmission)
- Which doctors get the most claims denied? (from 0% to 25.9%)
- Which kinds of doctors (specialties) get the most claims denied? (Nephrology — kidney doctors — at 15.1%; Cardiology the least at 7.9%)
- Which diseases bring patients back within 30 days most often? (Back pain — 6.6% of its visits)
- Which insurance type pays the most money, and where do denials hit hardest? (Commercial pays 47.3% of all dollars; the worst denial combination is heart failure + Medicaid at 17.6%)

Finally I built a dashboard and reports so a manager can see all these numbers in one page.
Tools used: SQL, Python, Power BI, Tableau — the same tools from my 90-day study plan.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Pandas](https://img.shields.io/badge/Pandas-analysis-green) ![SQL](https://img.shields.io/badge/SQL-10%2B%20queries-orange) ![Power BI](https://img.shields.io/badge/Power%20BI-spec%20%2B%20DAX-yellow) ![Tests](https://img.shields.io/badge/tests-passing-brightgreen) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

> **Portfolio project — synthetic CMS-style data only. No PHI, no real patients, no employer data.** Built to mirror, end to end, the full job of a Healthcare Data Analyst at a payer / health company such as CVS Health.

## Why this project is different
Most portfolio projects show one chart. A real healthcare analyst job is a **pipeline plus five recurring responsibility areas**, and this repo is structured exactly that way — one data pipeline feeding five analysis modules, each with its own KPIs, SQL, outputs and dashboard page:

| Module | Real-world responsibility | What it answers |
|---|---|---|
| 0 — Pipeline | Ingest, clean, model, validate multi-source data | Can we trust this data? |
| 1 — Claims & Revenue Cycle | Claims reporting, denial management support | What was billed vs paid, and why are claims denied? |
| 2 — Cost & Utilization | Medical cost reporting, PMPM, utilization | What does care cost per member, and what drives it? |
| 3 — Patient Outcomes | Quality / outcomes reporting | How big are readmissions and high-cost patient concentration? |
| 4 — Provider Performance | Provider scorecards for network teams | Which providers are outliers, good or bad? |

## Headline KPIs (actual outputs of `analysis.py`)
| KPI | Value |
|---|---|
| Members / providers / claims / encounters | 600 / 80 / 2,500 / 1,200 |
| Total billed | $2,400,677 |
| Total paid | $1,694,783 |
| Paid ratio | 70.6% |
| Billed on approved claims | $2,122,516 |
| Billed on denied claims (money at risk) | $278,161 |
| Paid as share of approved billed | 79.8% |
| Denial rate | 11.5% |
| Top denial reason | Prior authorization — 31.7% of denials |
| PMPM (per member per month) | **$235.39** |
| Average cost per encounter | $686.15 |
| Largest payer — Commercial share of paid | 47.3% |
| Highest denial rate, one condition + payer | Heart Failure / Medicaid — 17.6% |
| Lowest denial rate, one condition + payer | Chronic Kidney Disease / Medicaid — 2.3% |
| Median cost per visit — inpatient / office visit | $1,442 / $320 |
| Encounters per 1,000 members | 2,000 |
| Top-3 conditions' share of paid | **59.1%** (Diabetes 23.6%, Heart Failure 18.2%, CKD 17.2%) |
| Readmission proxy — all encounters / inpatient | 3.8% / **25.5%** |
| Cost share of top 10% of patients | 25.7% |
| Highest provider denial rate | PR073 (Orthopedics) — 25.9% |
| Lowest provider denial rate (≥20 claims) | PR058 (Primary Care) — 0.0% |
| Highest denial rate by specialty | Nephrology — 15.1% (304 claims) |
| Lowest denial rate by specialty | Cardiology — 7.9% (290 claims) |
| Readmission by condition — highest / lowest | Back Pain 6.6% / COPD 2.5% |
| Busiest claim month | Month 9 — 237 claims |

Every KPI above is defined in plain words, with its exact formula, in [KPI_DICTIONARY.md](KPI_DICTIONARY.md).

## Dashboard

![Cost by condition](images/cost_by_condition.png)
![Monthly PMPM trend](images/monthly_pmpm_trend.png)
![Denial Pareto](images/denial_pareto.png)
![Provider scorecard scatter](images/provider_scorecard_scatter.png)
![Claims money funnel](images/claims_funnel.png)
*The money funnel: of $2.40M billed, $278K sat in denied claims and $1.69M was actually paid.*
![Denial heatmap](images/denial_heatmap.png)
*Denial rate for every disease-and-insurance combination — the darkest box (heart failure with Medicaid, 17.6%) is where denial work pays first.*
![Paid by payer donut](images/payer_mix_donut.png)
*Where the paid money comes from: Commercial insurance pays 47.3% of all dollars, Medicare 30.9%, Medicaid 21.8%.*
![Encounter cost box plot](images/encounter_cost_boxplot.png)
*What one visit costs by visit type: a hospital stay (median $1,442) costs about 4.5× an office visit (median $320), and a few very expensive stays pull the average far above the middle value.*
![Monthly billed vs paid area](images/monthly_paid_area.png)
*Billed versus paid money each month — the band between the two areas is money denied or not paid; the paid share stays near 70% all year.*
![Denial rate by specialty](images/denial_by_specialty.png)
*Denials by doctor type: kidney specialists (Nephrology) lose 15.1% of their claims, cardiology only 7.9% — denial fixes belong in specific specialties' paperwork, not spread evenly.*
![Monthly claim volume and denial rate](images/monthly_claims_volume.png)
*Claims per month (bars) with the denial rate (line): the busiest month (month 9, 237 claims) is not the worst denial month — February carries the highest denial rate (14.0%) on below-average volume.*
![Readmission rate by condition](images/readmission_by_condition.png)
*Share of visits that are a return within 30 days, by disease: back-pain patients come back most often (6.6%), COPD patients least (2.5%).*
![Patient cost concentration](images/patient_concentration.png)
*The concentration curve: the top 10% of patients (59 people) account for 25.7% of all paid money, and the top half for 77.3% — the curve bends far above the "spread evenly" line.*
![Condition cost versus denial scatter](images/condition_cost_denial_scatter.png)
*Each bubble is one disease (bubble size = number of claims): the most expensive disease per claim (kidney disease, $1,233) is not the most denied — asthma is denied most (14.2%) while paying only $405 per claim.*

## Key insights (per module)
- **Module 0:** All 4,380 loaded rows pass structural checks — zero duplicate keys, zero orphan foreign keys, denied ⇒ paid = 0, paid ≤ billed.
- **Module 1:** Denials are a Pareto problem: Prior authorization (31.7%) + Coding error (25.8%) = 57.5% of all denials. Fixing front-end authorization and coding workflows attacks most of the 11.5% denial rate.
- **Module 2:** Chronic concentration is the budget: Diabetes, Heart Failure and CKD are 59.1% of paid dollars on 41% of claims. PMPM of $235.39 is the baseline any cost initiative must move.
- **Module 3:** The inpatient readmission proxy (25.5%) is the quality team's target; the top 10% of patients driving 25.7% of cost is the care-management cohort — and the overlap of the two groups is where intervention pays first.
- **Module 4:** Scorecards separate signal from noise with volume context: PR073's 25.9% denial rate (27 claims) warrants review, while PR058 (Primary Care) runs 0.0% denials at comparable volume — a workflow worth copying.
- **Module 5:** The money funnel shows both leaks: $278,161 of billed money (11.6%) sat in denied claims, and even approved claims converted only 79.8% of their billed dollars into paid dollars — the rest is contractual adjustment, the silent second leak.
- **Module 5:** Denials depend on the combination, not just the disease: heart-failure claims for Medicaid members were denied 17.6% of the time while kidney-disease claims for the same payer were denied only 2.3% — so denial fixes should target specific condition-and-payer pairs. And because Commercial members drive 47.3% of paid dollars, a small change there moves total cost more than a big change in Medicaid (21.8%).
- **Module 6:** Denials cluster by specialty as well as by reason: Nephrology loses 15.1% of its claims while Cardiology loses 7.9%, so documentation and authorization coaching should be specialty-specific. Readmission risk is just as uneven by condition (Back Pain 6.6% vs COPD 2.5%), the concentration curve confirms the top 59 patients (10% of those with claims) drive 25.7% of paid dollars, and volume is not the denial driver — the busiest month (month 9, 237 claims) has an ordinary denial rate while February's smaller volume carries the highest (14.0%).

## Business questions this project answers
- **Revenue cycle:** What is our paid ratio, and which denial reasons — by count and by billed dollars at risk — should the denial-management team attack first?
- **Finance / actuarial support:** What is PMPM this month, is it trending up, and how much of it is chronic-condition cost versus everything else?
- **Utilization management:** Are members using the ER and inpatient settings at rates (per 1,000 members) that suggest access or care-management problems?
- **Quality / outcomes:** How large is the 30-day readmission problem, for which conditions, and which patients — the high-cost decile — should care management enrol first?
- **Network / provider relations:** Which providers are denial or cost outliers once volume is accounted for, and which high performers' workflows should be studied and replicated?

## Data design (why the synthetic data is shaped this way)
The generator (seed 42) weights conditions by realistic prevalence and cost: Heart Failure and Chronic Kidney Disease carry cost multipliers of 2.2× and 2.4× against a Hypertension baseline of 0.8×, which is what produces the 59.1% top-3 concentration the analysis then "discovers". Provider behaviour is also planted, not random: a small number of providers bill at 1.4–1.55× peer levels with elevated denial propensity, and one efficient provider bills at 0.62× with a 4% denial propensity — Module 4's scorecard has to find them from the data alone, the same way a real scorecard must. Readmission probability is encounter-type- and condition-dependent (22% base for inpatient stays, uplifted for Heart Failure, COPD and CKD), mirroring the clinical pattern that readmission risk concentrates in chronic, recently-discharged patients. Denial reasons follow a front-end-heavy distribution (prior authorization and coding errors first), consistent with published revenue-cycle benchmarks where most denials are administrative rather than clinical.

## Data files (all in `data/`)
- `patients.csv` — 600 members: age, gender, payer (insurance type), months enrolled, number of chronic conditions
- `providers.csv` — 80 providers (doctors/clinics): specialty and region
- `claims.csv` — 2,500 insurance claims: amount billed, amount paid (0 when denied), paid/denied status, denial reason
- `encounters.csv` — 1,200 hospital and clinic visits: visit type, cost, and a flag for "came back within 30 days"

How the headline numbers are calculated: Paid ratio = paid ÷ billed · Denial rate = denied claims ÷ all claims · PMPM = total paid ÷ member-months · Readmission rate = share of visits flagged as a return within 30 days.

## Data & credits

- **Data:** all data in `data/` was generated by my own Python script (seed 42) to behave like real claims data. No real patients, no real claims, no employer data, and no personal health information.
- **Why synthetic:** real Bank of America, CVS, or Best Buy data can never be published. The synthetic data is shaped the way real claims work — denial reasons, costs by condition, and patients returning within 30 days — so the analysis and dashboards are real, even though the rows are made up.
- **No outside dataset was used**, so no outside credit is owed. The KPI definitions (denial rate, cost per member per month, readmission rate) are stated under "Data files" above.
- **Tools:** SQL, Python, Power BI, Tableau.

## Repository structure
```
├── analysis.py             # runs Modules 0–6, writes all outputs
├── charts.py               # 14 matplotlib charts -> images/
├── KPI_DICTIONARY.md       # every KPI defined in plain words, with its exact formula
├── requirements.txt  LICENSE  .gitignore
├── data/                   # patients.csv, providers.csv, claims.csv, encounters.csv
├── sql/analysis_queries.sql  # 10+ queries across all modules
├── outputs/                # kpi_summary.csv, provider_scorecard.csv, cost_by_condition.csv,
│                           # denial_by_condition_payer.csv, paid_by_payer.csv, monthly_paid_billed.csv,
│                           # denial_by_specialty.csv, readmission_by_condition.csv,
│                           # patient_concentration.csv, monthly_claims_volume.csv, condition_cost_denial.csv
├── images/                 # cost_by_condition, monthly_pmpm_trend, denial_pareto, provider_scorecard_scatter,
│                           # claims_funnel, denial_heatmap, payer_mix_donut, encounter_cost_boxplot, monthly_paid_area,
│                           # denial_by_specialty, readmission_by_condition, patient_concentration,
│                           # monthly_claims_volume, condition_cost_denial_scatter
```

## How to run
```bash
pip install -r requirements.txt
python3 analysis.py        # Modules 0–6 -> outputs/
python3 charts.py          # -> images/
```

## SQL highlights (`sql/analysis_queries.sql`)
Denial Pareto with window-function cumulative share · PMPM overall and monthly · cost-by-condition with chronic concentration · encounters per 1,000 members · readmission by condition with `RANK()` · top-decile patient cost concentration (CTE + `ROW_NUMBER()`) · provider scorecard with `RANK()` over denial rate.

## Interview Q&A
1. **How is PMPM calculated, and what breaks it?** Total paid ÷ member-months. It breaks when enrollment churn is ignored — the denominator must be member-months, not headcount.
2. **Your first denial-reduction move?** Pareto first: prior-auth and coding errors are 57.5% of denials here, so workflow fixes beat provider-by-provider chasing.
3. **Is the readmission number real?** It's a *proxy* — a pre-flagged return within 30 days on synthetic data. In production I'd derive it by linking an index admission to the next inpatient encounter per patient and state the definition (planned vs unplanned) explicitly.
4. **Why a star schema for this?** Claims and encounters are facts at different grains; patients/providers/conditions are conformed dimensions, so every module slices the same trusted tables instead of rebuilding extracts.
5. **How do you avoid shaming a provider on a scorecard unfairly?** Volume and case-mix context on every metric, minimum-volume thresholds for rankings, and rates shown next to raw counts — exactly how `provider_scorecard.csv` is built.

## 60-second talk track
"This project replicates a healthcare data analyst's full job at a payer. I built one pipeline that ingests patients, providers, claims and encounters into a star schema with automated data-quality checks, then five modules on top: revenue cycle — $1.69 million paid on $2.40 million billed with an 11.5% denial rate driven mainly by prior-authorization failures; cost and utilization — PMPM of $235 with three chronic conditions driving 59% of spend; outcomes — a 25.5% inpatient readmission proxy and a top-decile of patients driving a quarter of cost; and provider scorecards that flag a 25.9% denial-rate outlier against a 0% best performer. Everything — SQL, Python, dashboard and tests — is in the repo and reproducible from one command sequence."

## Next steps
