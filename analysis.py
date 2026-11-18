"""End-to-End Healthcare Analytics — runs Modules 0-6 over one pipeline.
Module 0 Pipeline & data quality | 1 Claims & Revenue Cycle | 2 Cost &
Utilization | 3 Patient Outcomes | 4 Provider Performance | 5 Money
Funnel, Payer Mix & Denial Heatmap | 6 Second Depth Pass (specialty
denials, readmission by condition, patient concentration, monthly
volume, condition cost-vs-denial).
Outputs land in outputs/ (kpi_summary.csv, insights.md,
data_quality_report.md, provider_scorecard.csv, cost_by_condition.csv,
denial_by_condition_payer.csv, paid_by_payer.csv, monthly_paid_billed.csv,
denial_by_specialty.csv, readmission_by_condition.csv,
patient_concentration.csv, monthly_claims_volume.csv,
condition_cost_denial.csv).
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

# ---------- Module 5: money funnel, payer mix & denial heatmap ----------
claims_payer = claims.merge(patients[["patient_id", "payer"]], on="patient_id", how="left")
approved_billed = claims_payer.loc[claims_payer.status != "Denied", "billed_amount"].sum()
denied_billed = claims_payer.loc[claims_payer.status == "Denied", "billed_amount"].sum()
kpi("Claims & Revenue Cycle", "approved_claims_billed_usd", approved_billed)
kpi("Claims & Revenue Cycle", "denied_claims_billed_usd", denied_billed)
kpi("Claims & Revenue Cycle", "paid_share_of_approved_billed_pct", 100 * total_paid / approved_billed)

heat = (claims_payer.groupby(["condition", "payer"])
        .agg(claims=("claim_id", "count"), denied=("status", lambda s: (s == "Denied").sum()))
        .reset_index())
heat["denial_rate_pct"] = 100 * heat.denied / heat.claims
heat = heat.sort_values(["condition", "payer"])
heat.to_csv("outputs/denial_by_condition_payer.csv", index=False)
hi_cell = heat.loc[heat.denial_rate_pct.idxmax()]; lo_cell = heat.loc[heat.denial_rate_pct.idxmin()]
kpi("Claims & Revenue Cycle", "highest_denial_condition_payer_pct", hi_cell.denial_rate_pct)
kpi("Claims & Revenue Cycle", "lowest_denial_condition_payer_pct", lo_cell.denial_rate_pct)

payer_mix = (claims_payer.groupby("payer")
             .agg(patients_with_claims=("patient_id", "nunique"), claims=("claim_id", "count"),
                  billed=("billed_amount", "sum"), paid=("paid_amount", "sum"))
             .sort_values("paid", ascending=False))
payer_mix["share_pct"] = 100 * payer_mix.paid / total_paid
payer_mix.to_csv("outputs/paid_by_payer.csv")
kpi("Cost & Utilization", "top_payer_paid_share_pct", payer_mix.share_pct.iloc[0])

med_by_type = encounters.groupby("encounter_type").encounter_cost.median()
kpi("Cost & Utilization", "median_encounter_cost_inpatient_usd", med_by_type["Inpatient"])
kpi("Cost & Utilization", "median_encounter_cost_office_visit_usd", med_by_type["Office Visit"])

monthly_pb = (claims.groupby("claim_month")
              .agg(billed=("billed_amount", "sum"), paid=("paid_amount", "sum")).reset_index())
monthly_pb["paid_ratio_pct"] = 100 * monthly_pb.paid / monthly_pb.billed
monthly_pb.to_csv("outputs/monthly_paid_billed.csv", index=False)

# ---------- Module 6: second depth pass ----------
# Denial rate by provider specialty (claims joined to the provider's specialty)
claims_spec = claims.merge(providers[["provider_id", "specialty"]], on="provider_id", how="left")
spec = (claims_spec.groupby("specialty")
        .agg(claims=("claim_id", "count"), denied=("status", lambda s: (s == "Denied").sum()),
             paid=("paid_amount", "sum"))
        .reset_index())
spec["denial_rate_pct"] = 100 * spec.denied / spec.claims
spec = spec.sort_values("denial_rate_pct", ascending=False)
spec.to_csv("outputs/denial_by_specialty.csv", index=False)
kpi("Provider Performance", "highest_denial_rate_specialty_pct", spec.denial_rate_pct.iloc[0])
kpi("Provider Performance", "lowest_denial_rate_specialty_pct", spec.denial_rate_pct.iloc[-1])

# Readmission rate by condition (same 30-day flag definition as Module 3)
readm_cond = (encounters.groupby("condition")
              .agg(encounters=("encounter_id", "count"), readmissions=("readmission_30d_flag", "sum"))
              .reset_index())
readm_cond["readmission_rate_pct"] = 100 * readm_cond.readmissions / readm_cond.encounters
readm_cond = readm_cond.sort_values("readmission_rate_pct", ascending=False)
readm_cond.to_csv("outputs/readmission_by_condition.csv", index=False)
kpi("Patient Outcomes", "lowest_readmission_condition_rate_pct", readm_cond.readmission_rate_pct.iloc[-1])

# Patient cost concentration curve (patients with claims, ranked by total paid;
# same top-decile cut as Module 3 so the 10% point reproduces its KPI)
conc_rows = []
for k_ in range(1, 11):
    take = int(k_ / 10 * len(pat_cost))
    conc_rows.append((k_ * 10, take, 100 * take / len(pat_cost),
                      pat_cost.iloc[:take].sum(), 100 * pat_cost.iloc[:take].sum() / total_paid))
conc = pd.DataFrame(conc_rows, columns=["top_patient_pct", "patients", "cum_patients_pct",
                                        "paid_usd", "cum_paid_share_pct"])
conc.to_csv("outputs/patient_concentration.csv", index=False)

# Monthly claim volume with monthly denial rate
monthly_vol = (claims.groupby("claim_month")
               .agg(claims=("claim_id", "count"), denied=("status", lambda s: (s == "Denied").sum()))
               .reset_index())
monthly_vol["denial_rate_pct"] = 100 * monthly_vol.denied / monthly_vol.claims
monthly_vol.to_csv("outputs/monthly_claims_volume.csv", index=False)
peak_month = monthly_vol.loc[monthly_vol.claims.idxmax()]
kpi("Claims & Revenue Cycle", "peak_month_claim_volume", peak_month.claims)

# Condition cost-vs-denial summary (average paid per claim, denial rate, volume)
cond_cd = (claims.groupby("condition")
           .agg(claims=("claim_id", "count"), paid=("paid_amount", "sum"),
                denied=("status", lambda s: (s == "Denied").sum()))
           .reset_index())
cond_cd["avg_paid_per_claim_usd"] = cond_cd.paid / cond_cd.claims
cond_cd["denial_rate_pct"] = 100 * cond_cd.denied / cond_cd.claims
cond_cd = cond_cd.sort_values("paid", ascending=False)
cond_cd.to_csv("outputs/condition_cost_denial.csv", index=False)

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
    f.write(f"**Module 5 — Money Funnel, Payer Mix & Denial Heatmap.** Of ${total_billed:,.0f} billed, ${denied_billed:,.0f} sat in denied claims and ${total_paid:,.0f} was actually paid — "
            f"{100 * total_paid / approved_billed:.1f}% of approved billed dollars converted to paid. {payer_mix.index[0]} members are the largest payer group at {payer_mix.share_pct.iloc[0]:.1f}% of paid dollars. "
            f"Denials are not even across condition-and-payer combinations: the worst cell is {hi_cell['condition']} / {hi_cell['payer']} at {hi_cell.denial_rate_pct:.1f}% denied, versus {lo_cell['condition']} / {lo_cell['payer']} at {lo_cell.denial_rate_pct:.1f}% — "
            f"denial work should target specific combinations, not spread evenly. Median visit cost is ${med_by_type['Inpatient']:,.0f} for an inpatient stay versus ${med_by_type['Office Visit']:,.0f} for an office visit, "
            f"which is why a small number of hospital stays moves total cost so much.\n")
    f.write(f"**Module 6 — Second Depth Pass.** Denials also cluster by specialty: {spec.specialty.iloc[0]} has the highest denial rate at {spec.denial_rate_pct.iloc[0]:.1f}% on {int(spec.claims.iloc[0])} claims, "
            f"while {spec.specialty.iloc[-1]} is lowest at {spec.denial_rate_pct.iloc[-1]:.1f}% — specialty-level workflow reviews beat plan-wide averages. "
            f"Readmission by condition peaks at {readm_cond.condition.iloc[0]} ({readm_cond.readmission_rate_pct.iloc[0]:.1f}%) and is lowest for {readm_cond.condition.iloc[-1]} ({readm_cond.readmission_rate_pct.iloc[-1]:.1f}%). "
            f"The concentration curve confirms the care-management case: the top 10% of patients with claims ({int(conc.patients.iloc[0])} people) account for {conc.cum_paid_share_pct.iloc[0]:.1f}% of paid dollars, "
            f"and the top half accounts for {conc.cum_paid_share_pct.iloc[4]:.1f}%. "
            f"Claim volume peaks in month {int(peak_month.claim_month)} ({int(peak_month.claims)} claims), while the monthly denial rate swings between {monthly_vol.denial_rate_pct.min():.1f}% and {monthly_vol.denial_rate_pct.max():.1f}% — "
            f"volume and denial pressure do not peak together. "
            f"By condition, {cond_cd.loc[cond_cd.avg_paid_per_claim_usd.idxmax(), 'condition']} has the highest average paid per claim (${cond_cd.avg_paid_per_claim_usd.max():,.0f}), "
            f"while {cond_cd.loc[cond_cd.denial_rate_pct.idxmax(), 'condition']} has the highest denial rate ({cond_cd.denial_rate_pct.max():.1f}%) at only ${cond_cd.loc[cond_cd.denial_rate_pct.idxmax(), 'avg_paid_per_claim_usd']:,.0f} per claim — "
            f"the most expensive conditions are not the most-denied ones.\n")
for m, n, v in K: print(f"{m:26s} {n:48s} {v}")
print("outputs written")
