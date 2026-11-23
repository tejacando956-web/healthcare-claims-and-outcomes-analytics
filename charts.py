"""Generate the 10 curated charts from outputs/ + data/ (matplotlib, dpi=150).

Palette — "calm clinical": rich, professional mid-deep tones.
  Diabetes #0E7C86 (teal) · Heart Failure #2E7FA8 (steel blue) ·
  CKD #5B84AE (denim) · COPD #2E9E77 (sea green) · Hypertension #57A773 (leaf) ·
  Asthma #E76F51 (coral, also the denial/alert accent) ·
  Back Pain #7D6BA8 (plum) · Depression #C95D7B (rose).
Ordered data uses the teal -> steel -> denim family ramp; the heatmap is a
single-hue teal ramp (white -> deep teal); grey appears only on context lines.
"""
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter

TEAL = "#0E7C86"; STEEL = "#2E7FA8"; DENIM = "#5B84AE"; SEA = "#2E9E77"
LEAF = "#57A773"; CORAL = "#E76F51"; PLUM = "#7D6BA8"; ROSE = "#C95D7B"
TEAL_DEEP = "#084F57"; GREY = "#9AA5AB"
COND_COLS = {"Diabetes": TEAL, "Heart Failure": STEEL, "Chronic Kidney Disease": DENIM,
             "COPD": SEA, "Hypertension": LEAF, "Asthma": CORAL, "Back Pain": PLUM,
             "Depression": ROSE}
FAMILY = LinearSegmentedColormap.from_list("family", [TEAL, STEEL, DENIM])

plt.rcParams.update({
    "font.size": 10, "axes.titlesize": 10.8, "axes.titleweight": "bold",
    "axes.labelsize": 10, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": "#B9C6CC", "text.color": "#1C2733",
    "axes.labelcolor": "#1C2733", "xtick.color": "#3D4A54", "ytick.color": "#3D4A54",
})
FIG = (8, 4.4)
DOLLAR = FuncFormatter(lambda v, _: f"${v:,.0f}")

claims = pd.read_csv("data/claims.csv"); enc = pd.read_csv("data/encounters.csv")
patients = pd.read_csv("data/patients.csv")

def grid_x(ax):
    ax.grid(axis="x", color="#E4ECEE", linewidth=0.7); ax.set_axisbelow(True)

def grid_y(ax):
    ax.grid(axis="y", color="#E4ECEE", linewidth=0.7); ax.set_axisbelow(True)

# 1. Paid cost by condition (ranked bars, family ramp — darkest = most money)
c = pd.read_csv("outputs/cost_by_condition.csv")  # sorted: most paid first
fig, ax = plt.subplots(figsize=FIG)
cols = [FAMILY(t) for t in np.linspace(0, 1, len(c))]
ax.barh(c.condition[::-1], c.paid[::-1], color=cols[::-1])
for i, (v, s) in enumerate(zip(c.paid[::-1], c.share_pct[::-1])):
    ax.text(v, i, f"  ${v:,.0f}  ({s:.1f}%)", va="center", fontsize=9)
ax.set_xlim(0, c.paid.max() * 1.30); ax.set_xlabel("Paid $ (one year of claims)")
ax.xaxis.set_major_formatter(DOLLAR); grid_x(ax)
ax.set_title("Three conditions drive 59.1% of paid cost — Diabetes is #1 at \\$400,249")
plt.tight_layout(); plt.savefig("images/cost_by_condition.png", dpi=150); plt.close()

# 2. Claims money funnel: billed -> approved billed -> paid (denim -> steel -> teal)
funnel_vals = [claims.billed_amount.sum(),
               claims.loc[claims.status != "Denied", "billed_amount"].sum(),
               claims.paid_amount.sum()]
funnel_labels = ["Total billed", "Billed on approved claims", "Paid"]
funnel_cols = [DENIM, STEEL, TEAL]
fig, ax = plt.subplots(figsize=(8, 3.8)); top = funnel_vals[0]
for i, (lab, v) in enumerate(zip(funnel_labels, funnel_vals)):
    y = len(funnel_vals) - 1 - i
    ax.barh(y, v, height=0.6, left=(top - v) / 2, color=funnel_cols[i])
    ax.text(top / 2, y, f"{lab}: \\${v:,.0f}  ({100 * v / top:.1f}% of billed)", ha="center",
            va="center", color="white", fontsize=9.5, fontweight="bold")
ax.set_xlim(0, top); ax.set_yticks([]); ax.set_xlabel("USD")
ax.xaxis.set_major_formatter(DOLLAR)
ax.set_title("Of \\$2.40M billed, \\$1.69M was paid — \\$278K sits in denied claims")
for sp in ["top", "right", "left"]: ax.spines[sp].set_visible(False)
plt.tight_layout(); plt.savefig("images/claims_funnel.png", dpi=150); plt.close()

# 3. Denial-rate heatmap: condition (rows) x payer (columns), single-hue teal ramp
heat = pd.read_csv("outputs/denial_by_condition_payer.csv")
piv = heat.pivot(index="condition", columns="payer", values="denial_rate_pct")[["Commercial", "Medicare", "Medicaid"]]
row_order = heat.groupby("condition").denial_rate_pct.mean().sort_values(ascending=False).index
piv = piv.loc[row_order]
cmap = LinearSegmentedColormap.from_list("tealramp", ["#FFFFFF", "#D9ECEC", "#8FBFC4", "#3E8E96", TEAL, TEAL_DEEP])
fig, ax = plt.subplots(figsize=FIG)
im = ax.imshow(piv.values, cmap=cmap, vmin=0, vmax=20, aspect="auto")
ax.set_xticks(range(len(piv.columns)), piv.columns); ax.set_yticks(range(len(piv)), piv.index)
for i in range(piv.shape[0]):
    for j in range(piv.shape[1]):
        v = piv.values[i, j]
        ax.text(j, i, f"{v:.1f}%", ha="center", va="center", fontsize=9, fontweight="bold",
                color="white" if v >= 10 else TEAL_DEEP)
ax.set_title("Denials hit hardest for Heart Failure + Medicaid (17.6%)")
fig.colorbar(im, ax=ax, label="Denial rate %")
plt.tight_layout(); plt.savefig("images/denial_heatmap.png", dpi=150); plt.close()

# 4. Paid $ share by payer (donut, teal family)
pm = pd.read_csv("outputs/paid_by_payer.csv")
donut_cols = {"Commercial": TEAL, "Medicare": STEEL, "Medicaid": DENIM}
fig, ax = plt.subplots(figsize=FIG)
wedges, _ = ax.pie(pm.paid, colors=[donut_cols[p] for p in pm.payer], startangle=90, counterclock=False,
                   wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2))
ax.legend(wedges, [f"{p}: \\${v:,.0f} ({s:.1f}%)" for p, v, s in zip(pm.payer, pm.paid, pm.share_pct)],
          loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=9.5, frameon=False)
ax.text(0, 0, f"Total paid\n\\${pm.paid.sum():,.0f}", ha="center", va="center",
        fontsize=10.5, fontweight="bold", color=TEAL_DEEP)
ax.set_title("Commercial pays 47.3% of all paid dollars")
plt.tight_layout(); plt.savefig("images/payer_mix_donut.png", dpi=150, bbox_inches="tight"); plt.close()

# 5. Cost per encounter by visit type (box plot, teal family deepening with cost)
types = ["Outpatient", "Office Visit", "Emergency", "Inpatient"]
box_data = [enc.loc[enc.encounter_type == t, "encounter_cost"] for t in types]
fig, ax = plt.subplots(figsize=FIG)
bp = ax.boxplot(box_data, patch_artist=True, medianprops=dict(color=CORAL, linewidth=2.2),
                boxprops=dict(edgecolor=STEEL), whiskerprops=dict(color=STEEL), capprops=dict(color=STEEL),
                flierprops=dict(marker="o", markersize=3.5, markerfacecolor=PLUM, markeredgecolor="none", alpha=0.75))
for patch, col in zip(bp["boxes"], [STEEL, DENIM, TEAL, TEAL_DEEP]): patch.set_facecolor(col)
for i, d in enumerate(box_data):
    ax.text(i + 1 + 0.32, d.median(), f"median \\${d.median():,.0f}", ha="left", va="center",
            fontsize=9, fontweight="bold", color=TEAL_DEEP,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=1.2))
ax.set_xticklabels(types); ax.set_ylabel("Encounter cost $")
ax.yaxis.set_major_formatter(DOLLAR); grid_y(ax)
ax.set_title("A hospital stay's middle cost (\\$1,442) is 4.5x an office visit's (\\$320)")
plt.tight_layout(); plt.savefig("images/encounter_cost_boxplot.png", dpi=150); plt.close()

# 6. Monthly billed vs paid (overlapping areas, teal family)
mpb = pd.read_csv("outputs/monthly_paid_billed.csv")
fig, ax = plt.subplots(figsize=FIG)
ax.fill_between(mpb.claim_month, mpb.billed, color=DENIM, alpha=0.40, label="Billed $")
ax.fill_between(mpb.claim_month, mpb.paid, color=TEAL, alpha=0.45, label="Paid $")
ax.plot(mpb.claim_month, mpb.billed, color=STEEL, lw=2); ax.plot(mpb.claim_month, mpb.paid, color=TEAL, lw=2)
ax.set_xticks(range(1, 13)); ax.set_xlabel("Month"); ax.set_ylabel("USD")
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v / 1000:,.0f}K")); grid_y(ax)
ax.set_title("Paid money stays near 70% of billed in every month")
ax.legend(); plt.tight_layout(); plt.savefig("images/monthly_paid_area.png", dpi=150); plt.close()

# 7. Denial rate by provider specialty (coral = worst, sea green = best, family ramp between)
ds = pd.read_csv("outputs/denial_by_specialty.csv").iloc[::-1]  # ascending -> highest on top
ramp = [FAMILY(t) for t in np.linspace(0, 1, len(ds))]
bar_cols = ramp[::-1]                       # lowest rate gets the lightest (denim) end
bar_cols[0] = SEA                           # first row = lowest rate (Cardiology) = good = green
bar_cols[-1] = CORAL                        # last row = highest rate (Nephrology) = alert = coral
fig, ax = plt.subplots(figsize=FIG)
ax.barh(ds.specialty, ds.denial_rate_pct, color=bar_cols)
for i, (r, n) in enumerate(zip(ds.denial_rate_pct, ds.claims)):
    ax.text(r + 0.3, i, f"{r:.1f}%  ({int(n)} claims)", va="center", fontsize=8.5)
ax.set_xlim(0, ds.denial_rate_pct.max() * 1.34)
ax.set_xlabel("Denial rate %"); grid_x(ax)
ax.set_title("Denials by specialty: Nephrology worst (15.1%), Cardiology best (7.9%)")
plt.tight_layout(); plt.savefig("images/denial_by_specialty.png", dpi=150); plt.close()

# 8. Readmission rate by condition (ranked bars, family ramp — darkest = highest)
rc = pd.read_csv("outputs/readmission_by_condition.csv")  # sorted: highest first
fig, ax = plt.subplots(figsize=FIG)
ax.bar(rc.condition, rc.readmission_rate_pct,
       color=[FAMILY(t) for t in np.linspace(0, 1, len(rc))])
for i, v in enumerate(rc.readmission_rate_pct):
    ax.text(i, v + 0.15, f"{v:.1f}%", ha="center", fontsize=9, fontweight="bold")
ax.set_ylabel("Readmission rate %"); ax.set_ylim(0, rc.readmission_rate_pct.max() * 1.20); grid_y(ax)
ax.set_title("Back Pain patients return within 30 days most often (6.6%)")
plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=8.5)
plt.tight_layout(); plt.savefig("images/readmission_by_condition.png", dpi=150); plt.close()

# 9. Patient cost concentration curve (teal line, grey = even-spread context line)
conc = pd.read_csv("outputs/patient_concentration.csv")
fig, ax = plt.subplots(figsize=FIG)
cx = np.concatenate([[0], conc.cum_patients_pct.values]); cy = np.concatenate([[0], conc.cum_paid_share_pct.values])
ax.plot(cx, cy, marker="o", color=TEAL, lw=2.2, label="Actual cost concentration")
ax.plot([0, 100], [0, 100], color=GREY, ls="--", lw=1.5, label="If cost were spread evenly")
top = conc.iloc[0]
ax.scatter([top.cum_patients_pct], [top.cum_paid_share_pct], s=120, color=CORAL, zorder=5)
ax.annotate(f"Top 10% of patients = {top.cum_paid_share_pct:.1f}% of paid \\$",
            xy=(top.cum_patients_pct, top.cum_paid_share_pct), xytext=(34, 16),
            fontsize=9.5, fontweight="bold", color=CORAL,
            arrowprops=dict(arrowstyle="->", color=CORAL))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); grid_y(ax)
ax.set_xlabel("Cumulative % of patients (highest-cost first)"); ax.set_ylabel("Cumulative % of paid $")
ax.set_title("The top 10% of patients drive 25.7% of all paid cost")
ax.legend(loc="lower right"); plt.tight_layout()
plt.savefig("images/patient_concentration.png", dpi=150); plt.close()

# 10. Condition scatter: average paid per claim vs denial rate (bubble = claims)
cd = pd.read_csv("outputs/condition_cost_denial.csv")
OFFSETS = {"Diabetes": (7, 6), "Heart Failure": (7, 6), "Chronic Kidney Disease": (7, -13),
           "COPD": (7, -13), "Hypertension": (-88, 3), "Asthma": (8, 4),
           "Back Pain": (8, -14), "Depression": (7, 5)}
fig, ax = plt.subplots(figsize=(8, 4.6))
for _, r in cd.iterrows():
    ax.scatter(r.avg_paid_per_claim_usd, r.denial_rate_pct, s=r.claims * 1.7,
               color=COND_COLS[r.condition], alpha=0.88, edgecolor="white", linewidth=0.7)
    ax.annotate(r.condition, (r.avg_paid_per_claim_usd, r.denial_rate_pct), fontsize=8.5,
                xytext=OFFSETS[r.condition], textcoords="offset points")
ax.set_xlabel("Average paid $ per claim"); ax.set_ylabel("Denial rate %")
ax.xaxis.set_major_formatter(DOLLAR); grid_y(ax)
ax.set_title("The priciest condition is not the most denied\nCKD costs \\$1,233 per claim; Asthma is denied most (14.2%)")
plt.tight_layout(); plt.savefig("images/condition_cost_denial_scatter.png", dpi=150); plt.close()
print("10 charts written")
