# KPI Dictionary — End-to-End Healthcare Analytics

Every headline number in this project, in plain words: what it means, the exact
calculation behind it, and where it comes from. All values are the current outputs
of `analysis.py` on the synthetic dataset (seed 42) and are published in
`outputs/kpi_summary.csv`.

**Words used below:** a *claim* is one bill sent to the insurance plan. *Billed* is
the amount the provider asked for; *paid* is the amount the plan actually paid.
A claim is *denied* when the plan refuses to pay it. A *member* is a person covered
by the plan. An *encounter* is one visit (office visit, ER visit, hospital stay…).

## Pipeline (Module 0 — can we trust the data?)

| KPI | Value | What it means | How it is calculated | Source |
|---|---:|---|---|---|
| total_rows_loaded | 4,380 | Total data rows loaded from all four files | Rows in patients (600) + providers (80) + claims (2,500) + encounters (1,200) | `data/*.csv`, detail in `outputs/data_quality_report.md` |
| duplicate_claim_ids | 0 | Claim IDs that appear more than once (should be zero) | Count of `claim_id` values in claims that are duplicated | `data/claims.csv` |
| claims_with_missing_amounts | 0 | Money cells left blank in the claims file (should be zero) | Count of empty cells in the `billed_amount` and `paid_amount` columns of claims | `data/claims.csv` |

## Claims & Revenue Cycle (Module 1 + 5 + 6 — billed vs paid, and denials)

| KPI | Value | What it means | How it is calculated | Source |
|---|---:|---|---|---|
| total_billed_usd | $2,400,676.91 | All money providers asked for | SUM of `billed_amount` over all 2,500 claims | `data/claims.csv` |
| total_paid_usd | $1,694,783.30 | All money the plan actually paid | SUM of `paid_amount` over all 2,500 claims (denied claims pay $0) | `data/claims.csv` |
| paid_ratio_pct | 70.6% | Share of billed money that was paid | total paid ÷ total billed × 100 | `outputs/kpi_summary.csv` |
| denial_rate_pct | 11.48% | Share of claims the plan refused to pay | Denied claims (status = Denied, 287) ÷ all claims (2,500) × 100 | `data/claims.csv` |
| top_denial_reason_share_pct | 31.71% | How much of the denial problem is the single biggest reason (Prior authorization) | Denied claims with the most common `denial_reason` (91) ÷ all denied claims (287) × 100 | `data/claims.csv` |
| approved_claims_billed_usd | $2,122,515.68 | Billed money on claims that were not denied | SUM of `billed_amount` over claims whose status is not Denied | `data/claims.csv` |
| denied_claims_billed_usd | $278,161.23 | Billed money stuck in denied claims — the money at risk | SUM of `billed_amount` over denied claims | `data/claims.csv` |
| paid_share_of_approved_billed_pct | 79.85% | Of the billed money on approved claims, the share that became paid money (the rest is contractual adjustment — the plan's agreed discount) | Total paid ÷ billed on approved claims × 100 | `outputs/kpi_summary.csv` |
| highest_denial_condition_payer_pct | 17.65% | The worst disease-and-insurance combination for denials (Heart Failure + Medicaid) | For every condition × payer group: denied claims ÷ claims in the group × 100; this is the highest group | `outputs/denial_by_condition_payer.csv` |
| lowest_denial_condition_payer_pct | 2.27% | The safest disease-and-insurance combination (Chronic Kidney Disease + Medicaid) | Same calculation as above; this is the lowest group | `outputs/denial_by_condition_payer.csv` |
| peak_month_claim_volume | 237 | Claims submitted in the busiest month (month 9) | Count claims per `claim_month`, take the largest month | `outputs/monthly_claims_volume.csv` |

## Cost & Utilization (Module 2 + 5 — what care costs)

| KPI | Value | What it means | How it is calculated | Source |
|---|---:|---|---|---|
| pmpm_usd | $235.39 | Cost per member per month — the standard "what does one covered person cost us each month" number | Total paid ÷ total member-months. Member-months = SUM of `enrollment_months` over all members (600 members × 12 months = 7,200). $1,694,783.30 ÷ 7,200 = $235.39 | `data/claims.csv` + `data/patients.csv` |
| avg_cost_per_encounter_usd | $686.15 | Average cost of one visit | Mean of `encounter_cost` over all 1,200 encounters | `data/encounters.csv` |
| encounters_per_1000_members | 2,000 | Visit volume scaled to a standard 1,000-member group, so plans of different sizes can be compared | Encounters (1,200) ÷ members (600) × 1,000 | `data/encounters.csv` + `data/patients.csv` |
| top3_conditions_share_of_paid_pct | 59.1% | Share of all paid money spent on the three most expensive conditions (Diabetes, Heart Failure, Chronic Kidney Disease) | Paid $ of the top 3 conditions ÷ total paid × 100 | `outputs/cost_by_condition.csv` |
| top_payer_paid_share_pct | 47.26% | Share of paid money coming from the biggest insurance type (Commercial) | Paid $ for the largest payer group ÷ total paid × 100 (payer comes from the patient record) | `outputs/paid_by_payer.csv` |
| median_encounter_cost_inpatient_usd | $1,441.97 | Middle cost of a hospital stay — half of stays cost less, half cost more (median, not average, so a few very expensive stays do not distort it) | Median of `encounter_cost` over encounters with type = Inpatient | `data/encounters.csv` |
| median_encounter_cost_office_visit_usd | $319.91 | Middle cost of an office visit | Median of `encounter_cost` over encounters with type = Office Visit | `data/encounters.csv` |

## Patient Outcomes (Module 3 + 6 — readmissions and high-cost patients)

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
| highest_readmission_condition_rate_pct | 6.6% | The condition whose visits most often are a return within 30 days (Back Pain) | For each condition: mean of `readmission_30d_flag` × 100; this is the highest | `outputs/readmission_by_condition.csv` |
| lowest_readmission_condition_rate_pct | 2.48% | The condition whose visits least often are a return within 30 days (COPD) | Same calculation as above; this is the lowest | `outputs/readmission_by_condition.csv` |

## Provider Performance (Module 4 + 6 — which doctors are outliers?)

| KPI | Value | What it means | How it is calculated | Source |
|---|---:|---|---|---|
| providers_scored | 80 | Providers in the scorecard | Count of providers in the scorecard (one row per provider) | `outputs/provider_scorecard.csv` |
| highest_denial_rate_provider_pct | 25.93% | The single provider with the highest share of denied claims (PR073, Orthopedics, 27 claims) | For each provider: denied claims ÷ their claims × 100; this is the highest | `outputs/provider_scorecard.csv` |
| lowest_denial_rate_provider_min20claims_pct | 0.0% | The lowest denial rate among providers with at least 20 claims — the minimum-volume rule stops a provider with 2 lucky claims from looking "best" (PR058, Primary Care) | Same per-provider denial rate, but only over providers with 20+ claims; this is the lowest | `outputs/provider_scorecard.csv` |
| top_provider_paid_usd | $45,467.28 | Paid money of the highest-paid provider (PR006, Family Medicine) | For each provider: SUM of `paid_amount` on their claims; this is the highest | `outputs/provider_scorecard.csv` |
| highest_denial_rate_specialty_pct | 15.13% | The doctor type (specialty) whose claims are denied most often (Nephrology, 304 claims) | Join claims to each provider's specialty; per specialty: denied claims ÷ all claims × 100; this is the highest | `outputs/denial_by_specialty.csv` |
| lowest_denial_rate_specialty_pct | 7.93% | The specialty whose claims are denied least often (Cardiology, 290 claims) | Same calculation as above; this is the lowest | `outputs/denial_by_specialty.csv` |
