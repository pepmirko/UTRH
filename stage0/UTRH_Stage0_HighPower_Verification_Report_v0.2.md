# UTRH Stage 0 — High-Power Synthetic Pre-Freeze Verification Report v0.2

**Generated:** 2026-09-24T16:54:53.495478+00:00  
**Status:** HIGH-POWER PRE-FREEZE ENGINEERING VALIDATION — not the formal post-freeze Stage 0 run.  
**Biological outcome data accessed:** none.  
**Purpose:** test whether the v1.2.1/PF-01 analysis code behaves as specified with materially higher Monte Carlo precision than the initial engineering preflight.

## Executive result

All synthetic engineering gates S0.1–S0.6 pass under the amended PF-01 specification. No new methodological contradiction was found. The fixed-grid S0.6a scenario is correctly classified as structurally non-identifiable rather than forced into an adjusted estimate; the heterogeneous-grid S0.6b scenario is identifiable and the granularity adjustment suppresses the induced false modifier association.

This run **does not authorize P1** because the plan still requires a third-party timestamp/hash freeze followed by a formal rerun of the unchanged Stage 0 code.

## High-power results

| Test | Monte Carlo budget | Main result | Status |
|---|---:|---|---|
| S0.1 Weibull | 100 | bias=(0.0115, 0.0046); RMSE=0.0607; coverage=0.965; false shape reject=0.070 | PASS |
| S0.1 log-normal | 100 | bias=(0.0037, -0.0035); RMSE=0.0475; coverage=0.960; false shape reject=0.050 | PASS |
| S0.1 log-logistic | 100 | bias=(0.0018, -0.0086); RMSE=0.0469; coverage=0.940; false shape reject=0.060 | PASS |
| S0.1 gamma | 100 | bias=(0.0039, -0.0054); RMSE=0.0532; coverage=0.945; false shape reject=0.060 | PASS |
| S0.2 shape violation | 500 | joint detection=0.980; LRT rejection=1.000; alternative held-out win=0.980; median held-out gain=0.07495 nats/obs | PASS |
| S0.3 phase-specific scaling | 5,000 | interaction detection=1.000; phase-specific held-out win=1.000 | PASS |
| S0.4 mixture/frailty | 5,000 | post-scalar-alignment KS rejection=1.000; median |log CV ratio|=0.282 | PASS |
| S0.5 null | 1,000 | mean estimated log-scale=0.00111; false nonzero 95% CI rate=0.066 | PASS |
| S0.6a fixed grid | 5,000 | spurious unadjusted association=0.733; median VIF=715.1; VIF≤5 fraction=0.000 | PASS: correctly NOT IDENTIFIABLE |
| S0.6b varying grids | 5,000 | VIF≤5 fraction=1.000; unadjusted false signal=0.526; adjusted false-positive rate=0.010; median adjusted beta1=-0.181 | PASS |

## Interpretation

### S0.1 — recovery of true scalar clocks

Across four distinct positive-time distribution families, all 400 fits converged. Bias remained small relative to the simulated clock contrasts and empirical 95% coverage stayed between 0.940 and 0.965. False rejection of the shared-shape model was 0.05–0.07. This supports numerical stability of the censoring/interval likelihood and relative-clock recovery under exact scalar scaling.

### S0.2 — shape change is not absorbed by a clock

At the prespecified Weibull shape contrast 1.05 versus 2.20, the LRT rejected shared shape in all 500 simulations. The stricter joint criterion requiring both rejection and improved held-out prediction passed in 98.0% of simulations. Thus the scalar degree of freedom does not systematically hide this shape violation.

### S0.3 — phase-specific speed is detectable

The early/late factor contrast (0.60 versus 1.40) was detected in all 5,000 simulations and the phase-specific model won held-out prediction in all 5,000. The pipeline therefore distinguishes a global clock from a state/phase-specific modifier at the simulated effect size.

### S0.4 — changing mixture/frailty remains visible after time alignment

After estimating and removing a scalar log-time shift, all 5,000 simulations retained a detectable distributional difference. The median absolute log-CV ratio was 0.282 and the median absolute log ratio of Q3/Q1 statistics was 0.412. A changing mixture is therefore not spuriously repaired by the scalar alignment used here.

### S0.5 — null calibration

With truly equal Weibull modules, the mean estimated log-clock contrast was 0.00111. The 95%-CI false-nonzero rate was 0.066 (66/1000), below the preregistered engineering ceiling of 0.09. This is mildly above the ideal 0.05 but compatible with the intended engineering criterion and does not indicate a major anti-conservative failure.

### S0.6a — fixed observation grid

Exact scalar scaling plus a common observation grid generated a false unadjusted modifier association in 73.3% of simulations. However, the median VIF was 715 and **zero of 5,000 simulations** satisfied VIF≤5. The correct output is therefore NOT SEPARABLE FROM OBSERVATION GRANULARITY, exactly as PF-01 now requires. No adjusted clock conclusion is permitted.

### S0.6b — heterogeneous observation grids

When observation schedules varied independently of the modifier, all 5,000 simulations satisfied the VIF≤5 identifiability gate (median VIF 1.824). The unadjusted regression generated a false modifier association in 52.64% of simulations; after including relative granularity, the false-positive rate fell to 1.0%. The median adjusted standardized slope was -0.181, below the 0.30 design-resolution target but showing a residual finite-sample/discretisation bias that should continue to be reported rather than hidden.

## What this establishes — and what it does not

This establishes only that the synthetic implementation can, at the tested simulation effect sizes:

1. recover relative scalar clocks under exact scaling;
2. avoid systematic false clock calls under the null;
3. detect shape, phase and mixture violations;
4. identify fixed-grid granularity as non-separable;
5. adjust heterogeneous-grid granularity without creating an anti-conservative false-positive problem.

It does **not** establish that any biological NDD dataset obeys UTRH, AFT scaling, shape invariance or the conditional-symmetry formulation.

## Freeze implication

No new scientific amendment is required after this high-power pre-freeze run. PF-02 in v1.2.2 is purely an encoding repair. The remaining gate is external and procedural:

1. deposit the exact freeze bundle in a third-party timestamped repository;
2. record repository identifier, timestamp and bundle hash in the freeze receipt;
3. rerun the exact frozen Stage 0 implementation as the formal Stage 0 verification;
4. only if that run passes, execute P1.
