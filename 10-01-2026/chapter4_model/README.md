# Chapter 4 reproducible model

This directory is the computational companion to Chapter 4. The dataset is
stylized and is intended to demonstrate the model mechanics; it is not an
estimate of the U.S. EV-battery-recycling industry.

Run from `latex_code_active/chapter4_model/`:

```powershell
python solve_chapter4.py --data case_data.json --output generated --solver SCIP
```

The command solves all 64 coalitions for the baseline and each sensitivity
scenario, computes exact Shapley allocations, checks every proper-coalition
core constraint, solves a least-core/L1 projection, and writes CSV, JSON, and
LaTeX fragments. `SCIP` is the primary solver; the script falls back to `CBC`
if SCIP is unavailable.

Phase I uses three direct coalition inputs: a formal-service target, binary
processor-access indicators, and a fixed governance cost. It then optimizes
retailer-to-center flow, center-to-processor flow, and facility activation.
The model intentionally contains no latent capability index or leakage choice.

Costs in the optimization are reported in thousands of U.S. dollars. Variable
cost inputs are dollars per ton and are divided by 1,000 when they enter the
objective. Generated files should not be edited by hand.
