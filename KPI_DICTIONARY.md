# KPI Dictionary — End-to-End Healthcare Analytics

The project's **15 headline KPIs**, in plain words: what each one means, the exact
calculation behind it, and where it comes from. All values are the current outputs
of `analysis.py` on the synthetic dataset (seed 42) and are published in
`outputs/kpi_summary.csv`.

**Words used below:** a *claim* is one bill sent to the insurance plan. *Billed* is
the amount the provider asked for; *paid* is the amount the plan actually paid.
A claim is *denied* when the plan refuses to pay it. A *member* is a person covered
by the plan. An *encounter* is one visit (office visit, ER visit, hospital stay…).

## Claims & Revenue Cycle (Modules 1 + 5 + 6 — billed vs paid, and denials)

| KPI | Value | What it means | How it is calculated | Source |
|---|---:|---|---|---|
| total_billed_usd | $2,400,676.91 | All money providers asked for | SUM of `billed_amount` over all 2,500 claims | `data/claims.csv` |
| total_paid_usd | $1,694,783.30 | All money the plan actually paid | SUM of `paid_amount` over all 2,500 claims (denied claims pay $0) | `data/claims.csv` |
| paid_ratio_pct | 70.6% | Share of billed money that was paid | total paid ÷ total billed × 100 | `outputs/kpi_summary.csv` |
| denial_rate_pct | 11.48% | Share of claims the plan refused to pay | Denied claims (status = Denied, 287) ÷ all claims (2,500) × 100 | `data/claims.csv` |
| top_denial_reason_share_pct | 31.71% | How much of the denial problem is the single biggest reason (Prior authorization) | Denied claims with the most common `denial_reason` (91) ÷ all denied claims (287) × 100 | `data/claims.csv` |
| denied_claims_billed_usd | $278,161.23 | Billed money stuck in denied claims — the money at risk | SUM of `billed_amount` over denied claims | `data/claims.csv` |
| highest_denial_condition_payer_pct | 17.65% | The worst disease-and-insurance combination for denials (Heart Failure + Medicaid, 9 of 51 claims). The safest combination (Chronic Kidney Disease + Medicaid) is 2.27% — the same payer can be worst for one disease and best for another, so denials depend on the combination, not the payer alone | For every condition × payer group: denied claims ÷ claims in the group × 100; this is the highest group | `outputs/denial_by_condition_payer.csv` |

## Cost & Utilization (Modules 2 + 5 — what care costs)

| KPI | Value | What it means | How it is calculated | Source |
|---|---:|---|---|---|
| pmpm_usd | $235.39 | Cost per member per month — the standard "what does one covered person cost us each month" number | Total paid ÷ total member-months. Member-months = SUM of `enrollment_months` over all members (600 members × 12 months = 7,200). $1,694,783.30 ÷ 7,200 = $235.39 | `data/claims.csv` + `data/patients.csv` |
| top3_conditions_share_of_paid_pct | 59.1% | Share of all paid money spent on the three most expensive conditions (Diabetes, Heart Failure, Chronic Kidney Disease) | Paid $ of the top 3 conditions ÷ total paid × 100 | `outputs/cost_by_condition.csv` |
| top_payer_paid_share_pct | 47.26% | Share of paid money coming from the biggest insurance type (Commercial) | Paid $ for the largest payer group ÷ total paid × 100 (payer comes from the patient record) | `outputs/paid_by_payer.csv` |

## Patient Outcomes (Modules 3 + 6 — readmissions and high-cost patients)

**The 30-day rule used everywhere below:** a visit counts as a *readmission* when the
patient comes back for another visit within 30 days of an earlier one. In this
synthetic dataset that is pre-computed as `readmission_30d_flag` (1 = came back
within 30 days) in the generator — a *proxy* for the real thing. In production the
flag would be built by linking each patient's visits in date order and checking
whether the next visit starts within 30 days of the previous discharge.

| KPI | Value | What it means | How it is calculated | Source |
|---|---:|---|---|---|
| readmission_proxy_rate_pct | 3.75% | Share of all visits that are a return within 30 days | Mean of `readmission_30d_flag` over all 1,200 encounters × 100 (45 returns ÷ 1,200) | `data/encounters.csv` |
| inpatient_readmission_rate_pct | 25.51% | Share of hospital stays followed by a return within 30 days — the number quality teams watch most | Mean of `readmission_30d_flag` over the 98 encounters with type = Inpatient × 100 (25 ÷ 98) | `data/encounters.csv` |
| top10pct_patients_share_of_cost_pct | 25.68% | Share of all paid money spent on the most expensive 10% of patients — the care-management group | Add up each patient's total paid (patients with at least one claim: 593), rank highest first, take the top 10% (59 patients, $435,166), divide by total paid × 100 | `outputs/patient_concentration.csv` |
| highest_readmission_condition_rate_pct | 6.6% | The condition whose visits most often are a return within 30 days (Back Pain, 7 of 106 visits). The lowest is COPD at 2.48% (3 of 121 visits) — full table in the source file | For each condition: mean of `readmission_30d_flag` × 100; this is the highest | `outputs/readmission_by_condition.csv` |

## Provider Performance (Modules 4 + 6 — which doctors are outliers?)

| KPI | Value | What it means | How it is calculated | Source |
|---|---:|---|---|---|
| highest_denial_rate_specialty_pct | 15.13% | The doctor type (specialty) whose claims are denied most often (Nephrology, 46 of 304 claims). The lowest is Cardiology at 7.93% (23 of 290 claims) — full table in the source file | Join claims to each provider's specialty; per specialty: denied claims ÷ all claims × 100; this is the highest | `outputs/denial_by_specialty.csv` |

---

**Supporting detail beyond these 15 headline KPIs** lives in the breakdown files in
`outputs/`: `cost_by_condition.csv` (paid $ per condition), `denial_by_condition_payer.csv`
(every condition × payer denial rate), `paid_by_payer.csv` (paid $ per payer),
`monthly_paid_billed.csv` and `monthly_claims_volume.csv` (the year month by month),
`provider_scorecard.csv` (one row per provider — claims, paid $, denial rate),
`denial_by_specialty.csv`, `readmission_by_condition.csv`, `patient_concentration.csv`
and `condition_cost_denial.csv`. The Module 0 data-quality checks (rows loaded,
duplicate IDs, missing amounts — all clean) are in `outputs/data_quality_report.md`.
