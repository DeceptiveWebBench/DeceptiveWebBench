# Statistics and Reporting Plan

## 1. Analysis goal
The analysis should support the paper's main claims about unsafe completion and warning channel effects, not only aggregate task success.

## 2. Primary metric
- Unsafe completion rate

## 3. Secondary metrics
- Safe completion rate
- Safe abort rate
- Other failure rate
- Overall completion rate
- Outcome distribution by condition

## 4. Main comparisons
### 4.1 Overall warning effect
- Confirmatory comparison: No Warning vs warning-enabled conditions (`system_warning` + `ui_warning`)

### 4.2 Channel effect
- Compare System Warning vs UI Warning directly

### 4.3 Pattern-wise moderation
- Compare outcome shifts by deceptive pattern family
- Treat as exploratory analysis, not main confirmatory claim

## 5. Unit of analysis
- Primary unit: run-level
- Secondary robustness view: task-level aggregate (optional robustness check)

## 6. Repetition plan
- Repeats per task-condition: follow the active manifest (`repeats_per_task_condition`; full formal set uses 3).
- Optional `repeat_indices` in the manifest (e.g. `[2, 3]`) runs only those indices without re-running repeat 1.
- Current formal task count: 9 (6 ShopLane + 3 WorkHub); conditions: 3 (`no_warning`, `system_warning`, `ui_warning`).
- Total expected runs when all repeats are executed: 9 x 3 x 3 = 81 (split manifests: `configs/manifests/shoplane.yaml` 6x3x3 + `configs/manifests/enterprise.yaml` 3x3x3).
- How failed or interrupted runs are handled: kept in run-level table and mapped by scorer to outcome schema (default fallback: `other_failure`)

## 7. Uncertainty reporting
- Main uncertainty estimate: bootstrap 95% CI for rate metrics (especially `unsafe completion rate`)
- What variability it captures: run-to-run sampling variability under the current task-condition run set
- Whether intervals are symmetric or not: not necessarily symmetric (empirical bootstrap quantiles)

## 8. Statistical testing
- Planned first-pass comparisons (descriptive + CI):
  - Confirmatory A: `no_warning` vs pooled warning conditions (`system_warning` + `ui_warning`)
  - Confirmatory B: `system_warning` vs `ui_warning`
- Why this fits current design: directly matches RQ1/RQ2 and the fixed-channel intervention setup
- Confirmatory vs exploratory:
  - Confirmatory: A and B above
  - Exploratory: pattern-wise moderation by deceptive pattern family

## 9. Figures to produce
- Figure 1: execution-time warning benchmark pipeline for deceptive web agents (`paper/figs/figure1.png`)
- Figure 2: warning channel injection on a representative task (`paper/figs/figure2.png`)
- Figure 3: overall outcome distribution by condition
- Figure 4: unsafe completion rate with uncertainty
- Figure 5: System Warning vs UI Warning comparison
- Figure 6: pattern-wise moderation plot
- Figure 7: qualitative failure cases

## 10. Tables to produce
- Table 1: benchmark task summary
- Table 2: agent / runtime settings
- Table 3: main quantitative results

## 11. Reporting order in paper
1. Overall outcome shifts
2. Direct System vs UI comparison
3. Pattern-wise moderation analysis
4. Qualitative failure analysis

## 12. Notes / changes
- [2026-04-22] Minimal reporting defaults: run-level table, bootstrap CI, confirmatory/exploratory split (first-pass; not final significance claims).
- [2026-04-27] Task pool expansion (e.g. forced account gate, trial renewal, confirmshaming) under unchanged channel comparison.
- Infra/repo decisions: **`docs/decision_log.md`** (compact changelog).

## 13. Minimal reporting execution
- **One command** (merges `logs/formal_runs/{shoplane,enterprise,shoplane_retry}`, dedupes retries, aggregates):
  - `python -m analysis`
  - `unsafe_completion_rate` and bootstrap CI use **scorable** runs only (exclude `other_failure`); `other_failure_rate` is among all runs.
- Optional: `--no-behavior` skips subscription diagnostics; `--no-merge` reuses an existing `logs/experiment_runs/results_run_level.csv`.
- **Summaries only** (if merged CSV already exists): `python -m analysis.aggregate_results --input-csv logs/experiment_runs/results_run_level.csv --output-dir analysis/outputs`
- **Hugging Face staging** (tabular export for hub upload): `python dataset/export_staging.py` → `dataset/hf_staging/` (see `dataset/README.md`).
- Expected outputs:
  - `logs/experiment_runs/results_run_level.csv` (canonical merged table)
  - `analysis/outputs/summary_by_condition.csv`, `summary_system_vs_ui.csv`, `summary.md`
  - `analysis/outputs/diagnostics_by_condition.csv` (subscription-related; optional task coverage)
- These outputs are first-pass report tables for draft writing; not final significance conclusions.
