# Frozen analysis summaries

These outputs are a reproducible analysis freeze of the formal run set (81 canonical run-level rows). `logs/experiment_runs/results_run_level.csv` is input-only: the analysis validates it but does not alter it.

Regenerate:

```bash
./.venv/bin/python -m analysis --input-csv logs/experiment_runs/results_run_level.csv --output-dir analysis/outputs --bootstrap-samples 10000 --seed 42
```

Key outputs: `run_matrix_audit.csv`, `run_manifest_v1.csv`, `summary_by_condition.csv`, `task_by_condition.csv`, `summary_system_vs_ui.csv`, `failure_decomposition.csv`, the two `sensitivity_*interface_perm_001.csv` files, and `summary.md`. Unsafe-completion intervals are task-cluster bootstrap intervals; outcome rates state their denominator explicitly. The 81-run analysis is primary; the 72-run exclusion view is a supplementary sensitivity analysis for the documented wording deviation.
