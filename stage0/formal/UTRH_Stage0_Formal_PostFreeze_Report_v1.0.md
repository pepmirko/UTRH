# UTRH Stage 0 — Formal Post-Freeze Verification Report v1.0

**Generated (UTC):** 2026-09-24T18:23:33.872617+00:00  
**Frozen preregistration commit:** `3930408b67faa49195e628f33bc0b4a017355adf`  
**Frozen plan SHA-256:** `4b25bc877b72341409e4ff15b246d7b4ff8310c34241c54e0af1adffcaacfd90`  
**Frozen Stage 0 code SHA-256:** `3cf08f96f5b763dfe4725fb23743ee1fa781010fcf138f94a98c082b1bb916ee`  
**Frozen high-power driver SHA-256:** `5e343eaa61f121edb817daf8ce8ab1a8017364b5f1b5cf6b238adf6ba8d9f5d8`  
**Biological outcome data accessed:** none.  

## Executive result

All formal synthetic gates S0.1–S0.6 **PASS** under the frozen v1.2.2/PF-01 specification. Because the code uses fixed preregistered seeds, the formal post-freeze run reproduced the pre-freeze high-power engineering output **exactly**: `True`.

This satisfies the Stage 0 gate for proceeding to P1. It is not biological evidence for UTRH.

## Results

| Test | Formal result | Status |
|---|---|---|
| S0.1 Weibull | bias=(0.0115, 0.0046); RMSE=0.0607; coverage=0.965; false shape reject=0.070 | PASS |
| S0.1 log-normal | bias=(0.0037, -0.0035); RMSE=0.0475; coverage=0.960; false shape reject=0.050 | PASS |
| S0.1 log-logistic | bias=(0.0018, -0.0086); RMSE=0.0469; coverage=0.940; false shape reject=0.060 | PASS |
| S0.1 gamma | bias=(0.0039, -0.0054); RMSE=0.0532; coverage=0.945; false shape reject=0.060 | PASS |
| S0.2 shape violation | joint detection=0.980; LRT=1.000; alt held-out win=0.980 | PASS |
| S0.3 phase-specific | interaction detection=1.000; held-out win=1.000 | PASS |
| S0.4 mixture/frailty | KS rejection after scale alignment=1.000; median |log CV ratio|=0.282 | PASS |
| S0.5 null | mean log-scale=0.00111; false nonzero 95% CI=0.066 | PASS |
| S0.6a fixed grid | median VIF=715.1; VIF≤5 fraction=0.000; correctly non-separable | PASS |
| S0.6b varying grid | VIF≤5 fraction=1.000; adjusted false-positive=0.010 | PASS |

## Reproducibility check

The formal results were compared programmatically against `UTRH_Stage0_HighPower_results.csv` from the pre-freeze engineering validation. Exact byte-for-byte equality of the results CSV: **True**.

Differences: none. The SHA-256 of both results CSV files is `38705b2f57176fffd5cff2bad061e292b743a7d9245f039bc88c2862426864f1`.

## Gate decision

**Stage 0 formal gate: PASS.** P1 may now begin under the frozen plan. No amendment was triggered by the post-freeze synthetic rerun.
