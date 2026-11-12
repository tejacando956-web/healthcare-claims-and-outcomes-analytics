"""End-to-End Healthcare Analytics — runs Modules 0-4 over one pipeline.
Module 0 Pipeline & data quality | 1 Claims & Revenue Cycle | 2 Cost &
Utilization | 3 Patient Outcomes | 4 Provider Performance.
Outputs land in outputs/ (kpi_summary.csv, insights.md,
data_quality_report.md, provider_scorecard.csv, cost_by_condition.csv).
"""
import pandas as pd, numpy as np, os
os.makedirs("outputs", exist_ok=True)

patients = pd.read_csv("data/patients.csv"); providers = pd.read_csv("data/providers.csv")
claims = pd.read_csv("data/claims.csv"); encounters = pd.read_csv("data/encounters.csv")
K = []  # (module, kpi, value)
def kpi(module, name, value): K.append((module, name, round(float(value), 2)))

# ---------- Module 0: pipeline & data quality ----------
dq = []
for name, df, key in [("patients", patients, "patient_id"), ("providers", providers, "provider_id"),
                      ("claims", claims, "claim_id"), ("encounters", encounters, "encounter_id")]:
    dq.append((name, len(df), int(df.isna().sum().sum()), int(df.duplicated(subset=[key]).sum()),
               int((~df["patient_id"].isin(patients.patient_id)).sum()) if "patient_id" in df and name != "patients" else 0))
kpi("Pipeline", "total_rows_loaded", sum(d[1] for d in dq))
kpi("Pipeline", "duplicate_claim_ids", claims.claim_id.duplicated().sum())
kpi("Pipeline", "claims_with_missing_amounts", claims[["billed_amount","paid_amount"]].isna().sum().sum())
with open("outputs/data_quality_report.md", "w") as f:
    f.write("# Data Quality Report — Module 0 (Pipeline)\n\nSynthetic CMS-style data. Star schema: dim_patient, dim_provider, fact_claims, fact_encounters.\n\n")
    f.write("| Table | Rows | Null cells | Duplicate keys | Orphan patient FKs |\n|---|---:|---:|---:|---:|\n")
    for r in dq: f.write(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |\n")
    f.write(f"\nChecks: claim_id unique = {not claims.claim_id.duplicated().any()}; "
            f"denied claims have paid_amount 0 = {bool((claims.loc[claims.status=='Denied','paid_amount']==0).all())}; "
            f"paid <= billed on paid claims = {bool((claims.loc[claims.status=='Paid','paid_amount'] <= claims.loc[claims.status=='Paid','billed_amount']).all())}; "
            f"all claim providers resolve = {bool(claims.provider_id.isin(providers.provider_id).all())}.\n")

# ---------- Module 1: claims & revenue cycle ----------
total_billed, total_paid = claims.billed_amount.sum(), claims.paid_amount.sum()
denied = claims[claims.status == "Denied"]
denial_rate = 100 * len(denied) / len(claims)
pareto = (denied.groupby("denial_reason").agg(claims=("claim_id","count"), billed=("billed_amount","sum"))
          .sort_values("claims", ascending=False)); pareto["share_pct"] = 100 * pareto.claims / pareto.claims.sum()
kpi("Claims & Revenue Cycle", "total_billed_usd", total_billed); kpi("Claims & Revenue Cycle", "total_paid_usd", total_paid)
kpi("Claims & Revenue Cycle", "paid_ratio_pct", 100 * total_paid / total_billed)
kpi("Claims & Revenue Cycle", "denial_rate_pct", denial_rate)
kpi("Claims & Revenue Cycle", "top_denial_reason_share_pct", pareto.share_pct.iloc[0])

# ---------- Module 2: cost & utilization ----------
member_months = patients.enrollment_months.sum()
pmpm = total_paid / member_months
cost_by_cond = (claims.groupby("condition").agg(claims=("claim_id","count"), paid=("paid_amount","sum"))
                .sort_values("paid", ascending=False)); cost_by_cond["share_pct"] = 100 * cost_by_cond.paid / total_paid
cost_by_cond.to_csv("outputs/cost_by_condition.csv")
top3_share = cost_by_cond.share_pct.iloc[:3].sum()
kpi("Cost & Utilization", "pmpm_usd", pmpm)
kpi("Cost & Utilization", "avg_cost_per_encounter_usd", encounters.encounter_cost.mean())
kpi("Cost & Utilization", "encounters_per_1000_members", 1000 * len(encounters) / len(patients))
kpi("Cost & Utilization", "top3_conditions_share_of_paid_pct", top3_share)

# ---------- Module 3: patient outcomes ----------
inp = encounters[encounters.encounter_type == "Inpatient"]
readm_rate = 100 * encounters.readmission_30d_flag.mean()
inp_readm = 100 * inp.readmission_30d_flag.mean()
by_cond = encounters.groupby("condition").readmission_30d_flag.mean().sort_values(ascending=False)
pat_cost = claims.groupby("patient_id").paid_amount.sum().sort_values(ascending=False)
top10_share = 100 * pat_cost.iloc[: int(0.10 * len(pat_cost))].sum() / total_paid
kpi("Patient Outcomes", "readmission_proxy_rate_pct", readm_rate)
kpi("Patient Outcomes", "inpatient_readmission_rate_pct", inp_readm)
kpi("Patient Outcomes", "top10pct_patients_share_of_cost_pct", top10_share)
kpi("Patient Outcomes", "highest_readmission_condition_rate_pct", 100 * by_cond.iloc[0])

# ---------- Module 4: provider performance ----------
enc_cost = encounters.groupby("provider_id").agg(encounters=("encounter_id","count"), enc_cost=("encounter_cost","sum"))
sc = (claims.groupby("provider_id").agg(claims=("claim_id","count"), paid=("paid_amount","sum"),
        denied=("status", lambda s: (s == "Denied").sum()), patients=("patient_id","nunique"))
      .join(enc_cost, how="left").fillna(0).reset_index()
      .merge(providers, on="provider_id", how="left"))
sc["denial_rate_pct"] = 100 * sc.denied / sc.claims
sc["cost_per_encounter_usd"] = sc.enc_cost / sc.encounters.replace(0, np.nan)
sc = sc.sort_values("paid", ascending=False)
sc.to_csv("outputs/provider_scorecard.csv", index=False)
worst = sc.sort_values("denial_rate_pct", ascending=False).iloc[0]; best = sc[sc.claims >= 20].sort_values("denial_rate_pct").iloc[0]
kpi("Provider Performance", "providers_scored", len(sc))
kpi("Provider Performance", "highest_denial_rate_provider_pct", worst.denial_rate_pct)
kpi("Provider Performance", "lowest_denial_rate_provider_min20claims_pct", best.denial_rate_pct)
kpi("Provider Performance", "top_provider_paid_usd", sc.paid.iloc[0])

pd.DataFrame(K, columns=["module","kpi","value"]).to_csv("outputs/kpi_summary.csv", index=False)
with open("outputs/insights.md", "w") as f:
    f.write("# Insights — End-to-End Healthcare Analytics (portfolio project, synthetic data)\n\n")
    f.write(f"**Module 1 — Claims & Revenue Cycle.** Paid ${total_paid:,.0f} of ${total_billed:,.0f} billed ({100*total_paid/total_billed:.1f}% paid ratio). "
            f"Denial rate {denial_rate:.1f}%; top denial reason '{pareto.index[0]}' = {pareto.share_pct.iloc[0]:.1f}% of denials — the first fix target.\n\n")
    f.write(f"**Module 2 — Cost & Utilization.** PMPM ${pmpm:,.2f}. Top-3 conditions ({', '.join(cost_by_cond.index[:3])}) = {top3_share:.1f}% of paid — chronic concentration drives the budget. "
            f"Encounters per 1,000 members: {1000*len(encounters)/len(patients):,.0f}.\n\n")
    f.write(f"**Module 3 — Patient Outcomes.** Readmission proxy {readm_rate:.1f}% overall, {inp_readm:.1f}% for inpatients; highest by condition: {by_cond.index[0]} ({100*by_cond.iloc[0]:.1f}%). "
            f"Top 10% of patients account for {top10_share:.1f}% of paid cost — the care-management cohort.\n\n")
    f.write(f"**Module 4 — Provider Performance.** Highest denial rate: {worst.provider_id} ({worst.specialty}, {worst.denial_rate_pct:.1f}% on {int(worst.claims)} claims). "
            f"Lowest (min 20 claims): {best.provider_id} ({best.specialty}, {best.denial_rate_pct:.1f}%). Full ranking in provider_scorecard.csv.\n")
for m, n, v in K: print(f"{m:26s} {n:48s} {v}")
print("outputs written")
