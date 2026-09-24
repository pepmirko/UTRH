# UTRH Stage 0 — Synthetic Engineering Preflight Report v0.1

**Date:** 2026-09-24T18:36:09+02:00
**Status:** PRE-FREEZE ENGINEERING VALIDATION — not the formal post-freeze Stage 0 run.
**Biological outcome data accessed:** none.
**Random seed:** 20260924.

## Executive result

S0.1–S0.5 passed the engineering checks used in this preflight. S0.6 exposed one internal plan conflict: with a fixed common observation grid, the rate modifier and relative-granularity covariate are structurally near-collinear, so the §8.2 VIF gate correctly returns NOT IDENTIFIABLE. The original S0.6 wording incorrectly demanded an adjusted beta1 estimate in the same setting. A pre-freeze amendment (PF-01) therefore splits S0.6 into a fixed-grid identifiability stress test and a heterogeneous-grid adjustment-validation test.

## Results

| Test | Scenario | Main result | Engineering status |
|---|---|---|---|
| S0.1 | weibull | bias=(0.006,-0.018); RMSE=0.052; coverage=1.000; false shape reject=0.083 | **PASS** |
| S0.1 | lognormal | bias=(0.007,0.017); RMSE=0.038; coverage=0.958; false shape reject=0.000 | **PASS** |
| S0.1 | loglogistic | bias=(-0.021,0.004); RMSE=0.048; coverage=0.958; false shape reject=0.083 | **PASS** |
| S0.1 | gamma | bias=(0.015,0.003); RMSE=0.052; coverage=1.000; false shape reject=0.000 | **PASS** |
| S0.2 | weibull shape 1.05 vs 2.20 | detection=1.000; held-out gain=0.0742 nats/obs | **PASS** |
| S0.3 | early factor 0.60, late factor 1.40 | interaction detection=1.000; phase-specific held-out win=1.000 | **PASS** |
| S0.4 | mixture weights 0.80/0.20 vs 0.30/0.70 | KS rejection after scalar alignment=1.000; |log CV ratio| median=0.288 | **PASS** |
| S0.5 | equal Weibull modules | mean log-scale=-0.0011; false nonzero 95% CI=0.042 | **PASS** |
| S0.6 | fixed common grid | unadjusted reject=0.787; median VIF=663.3; VIF≤5=0.000; adjusted reject identifiable=— | **PLAN_CONFLICT** |
| S0.6 | varying grid | unadjusted reject=0.562; median VIF=1.8; VIF≤5=1.000; adjusted reject identifiable=0.000 | **PASS** |

## Interpretation by test

### S0.1 — Exact scalar scaling
Across Weibull, log-normal, log-logistic and gamma baselines, relative log-scales were recovered with small bias and RMSE around 0.04–0.05. The shared-shape model did not show systematic false shape heterogeneity. Coverage estimates are only coarse in this preflight because 12 Monte Carlo replicates per distribution were used.

### S0.2 — Shape violation
With Weibull shape 1.05 versus 2.20, the separate-shape model was selected in every preflight replicate and improved held-out log likelihood in every replicate. The simulated violation is therefore detectable rather than being absorbed into a scalar clock.

### S0.3 — Phase-specific scaling
When the early phase was accelerated by 0.60 and the late phase slowed by 1.40, the phase × module interaction was detected in every replicate and the phase-specific model won held-out prediction in every replicate.

### S0.4 — Mixture/frailty
Changing mixture weights remained detectable after estimating and removing a scalar log-time shift: the two-sample KS test rejected equality in every replicate. Median absolute log-CV ratio was about 0.29, showing that the shape change was not absorbed by the clock.

### S0.5 — Null pipeline
Equal modules produced mean estimated log-scale essentially zero (-0.0011) and a 95%-CI false-nonzero rate of 0.0417 in the preflight, consistent with nominal behavior.

### S0.6 — Observation granularity
Fixed common grid: the unadjusted regression generated a spurious modifier association in 78.8% of simulations, but median VIF was ~663 and no simulation satisfied VIF≤5. This is structural non-identifiability, not a failure of the VIF rule. The original S0.6 wording was therefore internally inconsistent.

With heterogeneous observation schedules, all simulations satisfied VIF≤5 (median VIF ~1.83). The unadjusted false-positive rate was 56.3%, whereas after including the granularity covariate it fell to 0% in this preflight. The median adjusted standardized beta1 was -0.196: below the preregistered 0.30 design-resolution target but not exactly unbiased, so the formal post-freeze run should use more Monte Carlo replicates and report this residual bias explicitly.

## Limitations of this preflight

- Monte Carlo replication was deliberately reduced to fit the engineering run within the execution budget: S0.1 used 12 replicates per baseline, S0.2 20, S0.3/S0.4 40, S0.5 24 and S0.6 80 per grid scenario. These are adequate for bug discovery but not for final Monte Carlo precision.
- Engineering pass tolerances in the script are software-validation thresholds, not biological decision thresholds and do not modify P1–P3.
- No biological dataset, event time, prion summary statistic, polyQ age-at-onset value or P1 benchmark outcome was analyzed in this run.

## Required action before formal freeze

1. Adopt or reject PF-01. If adopted, v1.2.1 becomes the freeze candidate.
2. Freeze the plan and exact Stage 0 code with third-party timestamp/hash.
3. Rerun the unchanged Stage 0 code with a larger Monte Carlo budget as the formal verification.
4. Only after formal Stage 0 passes may P1 biological benchmark analysis begin.
