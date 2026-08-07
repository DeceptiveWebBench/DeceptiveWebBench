# Results confirmation report — analysis freeze

## Scope and freeze status

This report confirms the frozen pilot results used in the Version 1 A--C package. No agent was run, no formal result was replaced, and no D/E experiment was performed.

Research question (Revision Guide, verbatim):

> How should web agents be evaluated when nominal task completion may compromise the user’s financial interests, privacy, informed consent, autonomy, or policy constraints - and how can execution-time safeguards be tested without conflating warning design, risk detection, and agent capability?

The canonical table contains 81 complete, unique `(task_id, condition, repeat_id)` cells: 9 tasks × 3 conditions × 3 repeats. `interface_perm_001` is included. The raw canonical CSV SHA-256 is `c7095c1189b03cb672b888209d41d18853e3236360587455368cca440c851b07`.

The current task and UI warning use the concrete **non-essential cookie acceptance** wording. Repository history shows that the formal pilot's System-warning runs used the more abstract phrase **an unnecessary permission grant**. The primary analysis retains all nine affected cells. A requested sensitivity view excludes the task's nine cells; it is diagnostic rather than a general leave-one-task-out analysis. No historical artifact was edited or relabeled.

## Numbers eligible for the main text

All rates below identify their denominator. `safe_completion`, `unsafe_completion`, and `safe_abort` are among scorable runs; `other_failure` is among all runs.

| Condition | All runs | Scorable | Safe completion | Unsafe completion | Safe abort | Other failure |
|---|---:|---:|---:|---:|---:|---:|
| No Warning | 27 | 21 | 10/21 (47.6%) | 11/21 (52.4%) | 0/21 (0.0%) | 6/27 (22.2%) |
| System Warning | 27 | 20 | 8/20 (40.0%) | 12/20 (60.0%) | 0/20 (0.0%) | 7/27 (25.9%) |
| UI Warning | 27 | 24 | 9/24 (37.5%) | 14/24 (58.3%) | 1/24 (4.2%) | 3/27 (11.1%) |

Unsafe-completion task-cluster-bootstrap 95% intervals are 19.0–86.4% (No Warning), 25.0–90.9% (System), and 26.1–87.0% (UI). The System-minus-UI unsafe-completion difference is +1.7 percentage points (task-cluster-bootstrap 95% interval −33.6 to +36.6 points). These wide intervals do not support a warning-channel ranking.

Eligible scoped wording: the four-way deterministic schema exposes unsafe completion that endpoint-only success would conceal; for the fixed BrowserUse/Amazon Nova Lite v1 pilot on these nine tasks, the data do not provide a reliable System-versus-UI channel difference.

## Results for supplement / diagnostics only

- The descriptive 27-row task × condition table is `analysis/outputs/task_by_condition.csv`; it documents heterogeneity and is not confirmatory.
- The failure decomposition is `analysis/outputs/failure_decomposition.csv`: 37 deterministic unsafe decisions, 1 deterministic safe abstention, 27 safe completions, and 16 `other_failure` runs. The logs do not permit a reliable exhaustive navigation/grounding-versus-infrastructure split for the 16 failures, so no such split is claimed.
- Task-cluster bootstrap details, seed, and matrix audit are analysis/reproducibility records rather than stand-alone channel-effect results.
- The wording-deviation sensitivity view contains 72 runs (8 tasks × 3 conditions × 3 repeats). Unsafe completion is 11/19 (57.9%) for No Warning, 9/17 (52.9%) for System Warning, and 14/21 (66.7%) for UI Warning. The System-minus-UI difference is −13.7 percentage points (task-cluster-bootstrap 95% interval −43.3 to +12.3 points). This does not change the conclusion that the pilot does not establish a channel ranking.

## What the data support—and do not support

Supported:

- Deterministic terminal-state scoring operationalizes the four outcomes.
- The pilot contains unsafe completions in every warning condition under the stated scorable denominator.
- The pilot has substantial task-level heterogeneity and non-negligible `other_failure` rates that must remain visible.

Not supported:

- A general conclusion that either System or UI warnings are superior, or that execution-time warnings are ineffective generally.
- A causal statement about deployed risk detectors: the pilot is an oracle-trigger response evaluation.
- A comprehensive deceptive-pattern taxonomy claim, cross-agent claim, human comparison, or population-level claim.

## Author decisions still needed

- Confirm that the main text will use only the scoped pilot wording above and retain the task/pattern view as exploratory.
- Decide whether task × condition heterogeneity belongs in the main paper or supplement within the page limit.
- Decide whether a future D cross-agent validation should proceed; it has not begun here.

## Reproduction and verification

```bash
./.venv/bin/python -m analysis --input-csv logs/experiment_runs/results_run_level.csv --output-dir analysis/outputs --bootstrap-samples 10000 --seed 42
./.venv/bin/python analysis/generate_figures.py
./.venv/bin/python scripts/verify_analysis_freeze.py
./.venv/bin/python scripts/verify_paper_numbers.py
./.venv/bin/python scripts/verify_warning_task_contract.py
```

The first command validates and aggregates the existing CSV only. The second checks the fixed CSV hash/matrix and the protected paper front matter. The third checks the current cookie-warning task contract. No command runs an agent or mutates raw run data.

## Files changed for this freeze

- `analysis/aggregate_results.py`
- `analysis/report.py`, `analysis/__init__.py`, `analysis/stats_plan.md`
- `analysis/outputs/README.md`, `analysis/outputs/run_matrix_audit.csv`, `analysis/outputs/summary_by_condition.csv`, `analysis/outputs/task_by_condition.csv`, `analysis/outputs/summary_system_vs_ui.csv`, `analysis/outputs/sensitivity_without_interface_perm_001.csv`, `analysis/outputs/sensitivity_system_vs_ui_without_interface_perm_001.csv`, `analysis/outputs/failure_decomposition.csv`, `analysis/outputs/run_manifest_v1.csv`, `analysis/outputs/summary.md`
- `scripts/verify_analysis_freeze.py`
- `docs/archive/v1/results_confirmation_report.md`

The Version 1 paper and supplement consume these frozen outputs; they do not alter them.
