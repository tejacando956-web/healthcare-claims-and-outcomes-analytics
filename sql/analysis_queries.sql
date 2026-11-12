-- End-to-End Healthcare Analytics — SQL (SQLite/Postgres-compatible standard SQL)
-- Schema: patients(patient_id, age, gender, payer, enrollment_months, chronic_condition_count)
--         providers(provider_id, specialty, region)
--         claims(claim_id, patient_id, provider_id, claim_month, condition, billed_amount, paid_amount, status, denial_reason)
--         encounters(encounter_id, patient_id, provider_id, encounter_month, encounter_type, condition, encounter_cost, readmission_30d_flag)

-- MODULE 0 — Data quality: row counts, duplicates, orphans
SELECT 'claims' AS tbl, COUNT(*) AS rows_loaded, COUNT(*) - COUNT(DISTINCT claim_id) AS duplicate_keys FROM claims
UNION ALL SELECT 'encounters', COUNT(*), COUNT(*) - COUNT(DISTINCT encounter_id) FROM encounters;
SELECT COUNT(*) AS orphan_claims FROM claims c LEFT JOIN patients p ON p.patient_id = c.patient_id WHERE p.patient_id IS NULL;

-- MODULE 1 — Denial Pareto: count, billed at risk, share and cumulative share
WITH d AS (SELECT denial_reason, COUNT(*) AS denied_claims, SUM(billed_amount) AS billed_at_risk
           FROM claims WHERE status = 'Denied' GROUP BY denial_reason)
SELECT denial_reason, denied_claims, billed_at_risk,
       ROUND(100.0 * denied_claims / SUM(denied_claims) OVER (), 2) AS share_pct,
       ROUND(100.0 * SUM(denied_claims) OVER (ORDER BY denied_claims DESC) / SUM(denied_claims) OVER (), 2) AS cumulative_pct
FROM d ORDER BY denied_claims DESC;

-- MODULE 1 — Paid ratio by payer segment (join through patients)
SELECT p.payer, COUNT(*) AS claims, SUM(c.billed_amount) AS billed, SUM(c.paid_amount) AS paid,
       ROUND(100.0 * SUM(c.paid_amount) / SUM(c.billed_amount), 2) AS paid_ratio_pct
FROM claims c JOIN patients p ON p.patient_id = c.patient_id GROUP BY p.payer ORDER BY paid DESC;

-- MODULE 2 — PMPM overall and by month (paid / member-months)
SELECT ROUND(SUM(paid_amount) / (SELECT SUM(enrollment_months) FROM patients), 2) AS pmpm FROM claims;
SELECT claim_month, ROUND(SUM(paid_amount) / (SELECT COUNT(*) FROM patients), 2) AS monthly_pmpm
FROM claims GROUP BY claim_month ORDER BY claim_month;

-- MODULE 2 — Cost by condition + chronic concentration (top-3 share via window total)
SELECT condition, COUNT(*) AS claims, SUM(paid_amount) AS paid,
       ROUND(100.0 * SUM(paid_amount) / SUM(SUM(paid_amount)) OVER (), 2) AS share_pct
FROM claims GROUP BY condition ORDER BY paid DESC;

-- MODULE 2 — Utilization: encounters per 1,000 members by type
SELECT encounter_type, COUNT(*) AS encounters,
       ROUND(1000.0 * COUNT(*) / (SELECT COUNT(*) FROM patients), 1) AS per_1000_members
FROM encounters GROUP BY encounter_type ORDER BY encounters DESC;

-- MODULE 3 — Readmission proxy: overall, inpatient-only, and by condition (ranked)
SELECT ROUND(100.0 * AVG(readmission_30d_flag), 2) AS readmission_pct_all,
       ROUND(100.0 * AVG(CASE WHEN encounter_type = 'Inpatient' THEN readmission_30d_flag END), 2) AS readmission_pct_inpatient
FROM encounters;
SELECT condition, COUNT(*) AS encounters, ROUND(100.0 * AVG(readmission_30d_flag), 2) AS readmission_pct,
       RANK() OVER (ORDER BY AVG(readmission_30d_flag) DESC) AS rnk
FROM encounters GROUP BY condition ORDER BY readmission_pct DESC;

-- MODULE 3 — High-cost patient concentration: top 10% of patients, share of paid
WITH pc AS (SELECT patient_id, SUM(paid_amount) AS paid FROM claims GROUP BY patient_id),
     ranked AS (SELECT paid, ROW_NUMBER() OVER (ORDER BY paid DESC) AS rn, COUNT(*) OVER () AS n FROM pc)
SELECT ROUND(100.0 * SUM(CASE WHEN rn <= 0.10 * n THEN paid ELSE 0 END) / SUM(paid), 2) AS top10pct_share_pct FROM ranked;

-- MODULE 4 — Provider scorecard with window-function ranking by denial rate
SELECT pr.provider_id, pr.specialty, pr.region, COUNT(*) AS claims, SUM(c.paid_amount) AS paid,
       ROUND(100.0 * AVG(CASE WHEN c.status = 'Denied' THEN 1.0 ELSE 0 END), 2) AS denial_rate_pct,
       COUNT(DISTINCT c.patient_id) AS patients,
       RANK() OVER (ORDER BY AVG(CASE WHEN c.status = 'Denied' THEN 1.0 ELSE 0 END) DESC) AS denial_rank
FROM claims c JOIN providers pr ON pr.provider_id = c.provider_id
GROUP BY pr.provider_id, pr.specialty, pr.region ORDER BY denial_rate_pct DESC;

-- MODULE 4 — Cost per encounter by provider (fact_encounters), top/bottom 5 by volume-weighted cost
SELECT provider_id, COUNT(*) AS encounters, ROUND(AVG(encounter_cost), 2) AS avg_cost_per_encounter
FROM encounters GROUP BY provider_id HAVING COUNT(*) >= 10 ORDER BY avg_cost_per_encounter DESC LIMIT 5;
