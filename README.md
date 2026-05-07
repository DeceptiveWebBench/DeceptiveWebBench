# Execution-Time Warnings for Web Agents Under Deceptive Interfaces

A controlled local benchmark for evaluating whether **execution-time warnings** reduce **unsafe completion** when a multimodal web agent navigates deceptive UIs, and whether the **delivery channel** (system-prompt vs in-page) matters.

> **Paper:** NeurIPS 2026 Evaluations & Datasets track submission.  Build the PDF with `cd paper && pdflatex neurips_2026 && bibtex neurips_2026 && pdflatex neurips_2026 && pdflatex neurips_2026`.

## Key ideas

| Concept | Detail |
|---------|--------|
| **Conditions** | No Warning · System Warning · UI Warning (matched semantics, channel varies) |
| **Pattern families** | Interface interference · Sneaking · Forced action |
| **Outcome schema** | Safe completion · Unsafe completion · Safe abort · Other failure |
| **Scoring** | Deterministic terminal-state checks (no LLM judge) |
| **Agent** | BrowserUse + Amazon Nova Lite v1 (Bedrock), fixed across conditions |

## Repository layout

| Path | Role |
|------|------|
| `paper/` | NeurIPS LaTeX bundle (`neurips_2026.tex`, `checklist.tex`, `figs/`, `tabs/`, `references.bib`) |
| `configs/` | `main_config.yaml` (frozen agent/model config), `warnings.yaml` (risk-slot table), manifests |
| `env/site/` | ShopLane & WorkHub Admin HTML sandbox shells |
| `env/tasks/<task_id>/task.yaml` | Per-task goals, risk annotations, scoring rules |
| `src/` | Agent wrapper, experiment runner, deterministic scorer, prompt builder, sandbox JS |
| `analysis/` | Aggregation pipeline, bootstrap CIs, summary outputs |
| `dataset/` | HuggingFace staging export & upload helpers |
| `docs/` | `experiment_protocol.md`, `decision_log.md` |
| `scripts/` | Smoke tests and verification scripts |

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set credentials (env vars only — no keys in the repo)
export AWS_ACCESS_KEY_ID="..."
export AWS_API_KEY="..."        # Bedrock secret key
export AWS_REGION="us-east-1"   # optional, defaults to us-east-1

# 3. Verify API access
python smoke_test_api.py

# 4. Preview the sandbox (static file server)
python -m http.server
# then open http://localhost:8000/env/dashboard/index.html

# 5. Smoke test (single task)
python -m scripts.smoke_browseruse.run

# 6. Formal batch run
python -m src.runner.run_experiment --manifest configs/experiment_manifest.yaml

# 7. Aggregate results & generate summaries
python -m analysis
```

## Analysis

```bash
# Full merge + summaries
python -m analysis

# Summaries only (from existing merged CSV)
python -m analysis.aggregate_results --input-csv logs/experiment_runs/results_run_level.csv
```

Bootstrap 95% CIs (1,000 resamples, seed 42) are computed over scorable runs.  See `analysis/stats_plan.md` for metric definitions.

## Data release

Run-level results (JSONL / CSV / Parquet) are published on **HuggingFace** via `dataset/export_staging.py`.  Raw experiment logs (`logs/`) are excluded from this repository.

## Licenses

| Scope | License |
|-------|---------|
| Source code | MIT (`LICENSE`) |
| Non-code assets (tasks, data, figures) | CC BY-NC 4.0 (`LICENSE_DATA`) |

## Terminology (paper ↔ code)

| Paper phrasing | Identifier |
|----------------|------------|
| Interface interference | `interface_interference` |
| Sneaking | `sneaking` |
| Forced action | `forced_action` |
