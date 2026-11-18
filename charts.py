"""Generate the 14 dashboard charts from outputs/ + data/ (matplotlib, dpi=150)."""
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
claims = pd.read_csv("data/claims.csv"); enc = pd.read_csv("data/encounters.csv")
patients = pd.read_csv("data/patients.csv"); sc = pd.read_csv("outputs/provider_scorecard.csv")
TEAL="#0e7c7b"; NAVY="#1f3a5f"

c = pd.read_csv("outputs/cost_by_condition.csv")
plt.figure(figsize=(8,4.4)); plt.barh(c.condition[::-1], c.paid[::-1], color=TEAL)
for i,v in enumerate(c.paid[::-1]): plt.text(v, i, f" ${v:,.0f}", va="center", fontsize=8)
plt.title("Paid Cost by Condition (claims)"); plt.xlabel("Paid $"); plt.tight_layout()
plt.savefig("images/cost_by_condition.png", dpi=150); plt.close()

monthly = claims.groupby("claim_month").paid_amount.sum() / len(patients)
plt.figure(figsize=(8,4.2)); plt.plot(monthly.index, monthly.values, marker="o", color=NAVY, lw=2)
plt.axhline(monthly.mean(), color=TEAL, ls="--", label=f"Avg PMPM ${monthly.mean():,.0f}")
plt.title("Monthly PMPM Trend (paid per member per month)"); plt.xlabel("Month"); plt.ylabel("PMPM $")
plt.xticks(range(1,13)); plt.legend(); plt.tight_layout()
plt.savefig("images/monthly_pmpm_trend.png", dpi=150); plt.close()

den = claims[claims.status=="Denied"].groupby("denial_reason").size().sort_values(ascending=False)
share = 100*den/den.sum(); cum = share.cumsum()
fig, ax = plt.subplots(figsize=(8,4.4)); ax.bar(share.index, share.values, color=TEAL)
ax.set_ylabel("Share of denials %"); ax.set_title("Denial Reasons Pareto")
plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=8)
ax2 = ax.twinx(); ax2.plot(share.index, cum.values, color=NAVY, marker="o"); ax2.set_ylabel("Cumulative %"); ax2.set_ylim(0,105)
plt.tight_layout(); plt.savefig("images/denial_pareto.png", dpi=150); plt.close()

s = sc.dropna(subset=["cost_per_encounter_usd"])
plt.figure(figsize=(8,4.6))
plt.scatter(s.cost_per_encounter_usd, s.denial_rate_pct, s=s.paid/40, alpha=0.65, color=TEAL, edgecolor=NAVY)
plt.title("Provider Scorecard: Cost per Encounter vs Denial Rate (bubble = paid $)")
plt.xlabel("Avg cost per encounter $"); plt.ylabel("Denial rate %"); plt.tight_layout()
plt.savefig("images/provider_scorecard_scatter.png", dpi=150); plt.close()

# ---------- Signature charts (Ocean & Coral palette) ----------
from matplotlib.colors import LinearSegmentedColormap
TEAL2="#0E7C86"; SKY="#3AAED8"; STEEL="#2B7A9E"; MINT="#34B596"; PEACH="#FF8A66"; CORAL="#FF7A59"; PERI="#6D7FD6"; PINK="#E56399"

# 5. Claims money funnel: billed -> approved billed -> paid
funnel_vals = [claims.billed_amount.sum(),
               claims.loc[claims.status != "Denied", "billed_amount"].sum(),
               claims.paid_amount.sum()]
funnel_labels = ["Total billed", "Billed on approved claims", "Paid"]
funnel_cols = [STEEL, SKY, TEAL2]
fig, ax = plt.subplots(figsize=(8, 3.8)); top = funnel_vals[0]
for i, (lab, v) in enumerate(zip(funnel_labels, funnel_vals)):
    y = len(funnel_vals) - 1 - i
    ax.barh(y, v, height=0.6, left=(top - v) / 2, color=funnel_cols[i])
    ax.text(top / 2, y, f"{lab}: ${v:,.0f}  ({100 * v / top:.1f}% of billed)", ha="center", va="center",
            color="white", fontsize=9.5, fontweight="bold")
ax.set_xlim(0, top); ax.set_yticks([]); ax.set_xlabel("USD")
ax.set_title("Claims Money Funnel: Billed → Approved → Paid")
for sp in ["top", "right", "left"]: ax.spines[sp].set_visible(False)
plt.tight_layout(); plt.savefig("images/claims_funnel.png", dpi=150); plt.close()

# 6. Denial-rate heatmap: condition (rows) x payer (columns)
heat = pd.read_csv("outputs/denial_by_condition_payer.csv")
piv = heat.pivot(index="condition", columns="payer", values="denial_rate_pct")[["Commercial", "Medicare", "Medicaid"]]
row_order = (heat.groupby("condition").denial_rate_pct.mean()
             .sort_values(ascending=False).index)
piv = piv.loc[row_order]
cmap = LinearSegmentedColormap.from_list("ocean", ["#E8F6F7", SKY, TEAL2, STEEL])
fig, ax = plt.subplots(figsize=(8, 4.6))
im = ax.imshow(piv.values, cmap=cmap, vmin=0, vmax=20, aspect="auto")
ax.set_xticks(range(len(piv.columns)), piv.columns); ax.set_yticks(range(len(piv)), piv.index)
for i in range(piv.shape[0]):
    for j in range(piv.shape[1]):
        v = piv.values[i, j]
        ax.text(j, i, f"{v:.1f}%", ha="center", va="center", fontsize=9, fontweight="bold",
                color="white" if v >= 11 else "#0B4F57")
ax.set_title("Denial Rate % by Condition and Payer (darker = more denials)")
fig.colorbar(im, ax=ax, label="Denial rate %")
plt.tight_layout(); plt.savefig("images/denial_heatmap.png", dpi=150); plt.close()

# 7. Paid $ share by payer (donut)
pm = pd.read_csv("outputs/paid_by_payer.csv")
donut_cols = {"Commercial": TEAL2, "Medicare": SKY, "Medicaid": PEACH}
fig, ax = plt.subplots(figsize=(7.6, 4.4))
wedges, _ = ax.pie(pm.paid, colors=[donut_cols[p] for p in pm.payer], startangle=90, counterclock=False,
                   wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2))
ax.legend(wedges, [f"{p}: ${v:,.0f} ({s:.1f}%)" for p, v, s in zip(pm.payer, pm.paid, pm.share_pct)],
          loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=9.5, frameon=False)
ax.set_title("Paid $ Share by Payer")
plt.tight_layout(); plt.savefig("images/payer_mix_donut.png", dpi=150, bbox_inches="tight"); plt.close()

# 8. Cost per encounter by visit type (box plot)
types = ["Outpatient", "Office Visit", "Emergency", "Inpatient"]
box_data = [enc.loc[enc.encounter_type == t, "encounter_cost"] for t in types]
fig, ax = plt.subplots(figsize=(8, 4.4))
bp = ax.boxplot(box_data, patch_artist=True, medianprops=dict(color=CORAL, linewidth=2.2),
                boxprops=dict(edgecolor=STEEL), whiskerprops=dict(color=STEEL), capprops=dict(color=STEEL),
                flierprops=dict(marker="o", markersize=3, markerfacecolor=PERI, markeredgecolor="none", alpha=0.45))
for patch, col in zip(bp["boxes"], [TEAL2, SKY, PEACH, CORAL]): patch.set_facecolor(col)
ax.set_xticklabels(types); ax.set_ylabel("Encounter cost $")
ax.set_title("Cost per Encounter by Visit Type (box = middle 50% of visits, line = median)")
plt.tight_layout(); plt.savefig("images/encounter_cost_boxplot.png", dpi=150); plt.close()

# 9. Monthly billed vs paid (overlapping areas)
mpb = pd.read_csv("outputs/monthly_paid_billed.csv")
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.fill_between(mpb.claim_month, mpb.billed, color=SKY, alpha=0.35, label="Billed $")
ax.fill_between(mpb.claim_month, mpb.paid, color=TEAL2, alpha=0.45, label="Paid $")
ax.plot(mpb.claim_month, mpb.billed, color=STEEL, lw=2); ax.plot(mpb.claim_month, mpb.paid, color=TEAL2, lw=2)
ax.set_xticks(range(1, 13)); ax.set_xlabel("Month"); ax.set_ylabel("USD")
ax.set_title("Monthly Billed vs Paid $ (the gap is denied or unpaid money)")
ax.legend(); plt.tight_layout(); plt.savefig("images/monthly_paid_area.png", dpi=150); plt.close()

# ---------- Second depth pass (Ocean & Coral palette) ----------
COND_COLS = {"Diabetes": TEAL2, "Heart Failure": SKY, "Chronic Kidney Disease": STEEL, "COPD": MINT,
             "Hypertension": PEACH, "Asthma": CORAL, "Back Pain": PERI, "Depression": PINK}

# 10. Denial rate by provider specialty (bars, claim counts annotated)
ds = pd.read_csv("outputs/denial_by_specialty.csv").iloc[::-1]  # ascending -> highest on top
bar_cols = [STEEL] * len(ds); bar_cols[0] = MINT; bar_cols[-1] = CORAL
fig, ax = plt.subplots(figsize=(8, 4.4))
ax.barh(ds.specialty, ds.denial_rate_pct, color=bar_cols)
for i, (r, n) in enumerate(zip(ds.denial_rate_pct, ds.claims)):
    ax.text(r + 0.3, i, f"{r:.1f}%  ({int(n)} claims)", va="center", fontsize=8.5)
ax.set_xlim(0, ds.denial_rate_pct.max() * 1.32)
ax.set_xlabel("Denial rate %")
ax.set_title("Denial Rate by Provider Specialty (coral = highest, mint = lowest)")
plt.tight_layout(); plt.savefig("images/denial_by_specialty.png", dpi=150); plt.close()

# 11. Readmission rate by condition (bars)
rc = pd.read_csv("outputs/readmission_by_condition.csv")
fig, ax = plt.subplots(figsize=(8, 4.4))
ax.bar(rc.condition, rc.readmission_rate_pct, color=[COND_COLS[c] for c in rc.condition])
for i, v in enumerate(rc.readmission_rate_pct):
    ax.text(i, v + 0.15, f"{v:.1f}%", ha="center", fontsize=9, fontweight="bold")
ax.set_ylabel("Readmission rate %"); ax.set_ylim(0, rc.readmission_rate_pct.max() * 1.18)
ax.set_title("Readmission Rate by Condition (visits that are a return within 30 days)")
plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=8.5)
plt.tight_layout(); plt.savefig("images/readmission_by_condition.png", dpi=150); plt.close()

# 12. Patient cost concentration curve (cumulative % of patients vs cumulative % of paid $)
conc = pd.read_csv("outputs/patient_concentration.csv")
fig, ax = plt.subplots(figsize=(8, 4.4))
cx = np.concatenate([[0], conc.cum_patients_pct.values]); cy = np.concatenate([[0], conc.cum_paid_share_pct.values])
ax.plot(cx, cy, marker="o", color=TEAL2, lw=2, label="Actual cost concentration")
ax.plot([0, 100], [0, 100], color=PERI, ls="--", lw=1.5, label="If cost were spread evenly")
top = conc.iloc[0]
ax.scatter([top.cum_patients_pct], [top.cum_paid_share_pct], s=120, color=CORAL, zorder=5)
ax.annotate(f"Top 10% of patients = {top.cum_paid_share_pct:.1f}% of paid $",
            xy=(top.cum_patients_pct, top.cum_paid_share_pct), xytext=(34, 16),
            fontsize=9.5, fontweight="bold", color=CORAL,
            arrowprops=dict(arrowstyle="->", color=CORAL))
ax.set_xlabel("Cumulative % of patients (highest-cost first)"); ax.set_ylabel("Cumulative % of paid $")
ax.set_title("Patient Cost Concentration: a Small Share of Patients Drives Cost")
ax.legend(loc="lower right"); plt.tight_layout()
plt.savefig("images/patient_concentration.png", dpi=150); plt.close()

# 13. Monthly claim volume (bars) + monthly denial rate (line, secondary axis)
mv = pd.read_csv("outputs/monthly_claims_volume.csv")
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.bar(mv.claim_month, mv.claims, color=SKY, label="Claims submitted")
ax.set_xlabel("Month"); ax.set_ylabel("Claims submitted"); ax.set_xticks(range(1, 13))
ax2 = ax.twinx()
ax2.plot(mv.claim_month, mv.denial_rate_pct, color=CORAL, marker="o", lw=2, label="Denial rate %")
ax2.set_ylabel("Denial rate %"); ax2.set_ylim(0, mv.denial_rate_pct.max() * 1.5)
ax.set_title("Monthly Claim Volume (bars) and Denial Rate % (line)")
plt.tight_layout(); plt.savefig("images/monthly_claims_volume.png", dpi=150); plt.close()

# 14. Condition scatter: average paid per claim vs denial rate (bubble = claims)
cd = pd.read_csv("outputs/condition_cost_denial.csv")
OFFSETS = {"Diabetes": (7, 6), "Heart Failure": (7, 6), "Chronic Kidney Disease": (7, -13),
           "COPD": (7, -13), "Hypertension": (-88, 3), "Asthma": (8, 4),
           "Back Pain": (8, -14), "Depression": (7, 5)}
fig, ax = plt.subplots(figsize=(8, 4.6))
for _, r in cd.iterrows():
    ax.scatter(r.avg_paid_per_claim_usd, r.denial_rate_pct, s=r.claims * 1.7,
               color=COND_COLS[r.condition], alpha=0.8, edgecolor=STEEL)
    ax.annotate(r.condition, (r.avg_paid_per_claim_usd, r.denial_rate_pct), fontsize=8.5,
                xytext=OFFSETS[r.condition], textcoords="offset points")
ax.set_xlabel("Average paid $ per claim"); ax.set_ylabel("Denial rate %")
ax.set_title("Conditions: Cost per Claim vs Denial Rate (bubble size = number of claims)")
plt.tight_layout(); plt.savefig("images/condition_cost_denial_scatter.png", dpi=150); plt.close()
print("14 charts written")
