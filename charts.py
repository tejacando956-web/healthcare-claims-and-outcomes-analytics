"""Generate the 4 dashboard charts from outputs/ + data/ (matplotlib, dpi=150)."""
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
print("4 charts written")
