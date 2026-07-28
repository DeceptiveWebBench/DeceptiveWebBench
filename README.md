# Execution-Time Warnings for Web Agents Under Deceptive Interfaces

A controlled local benchmark for evaluating whether **execution-time warnings** reduce **unsafe completion** when a multimodal web agent navigates deceptive UIs, and whether the **delivery channel** (system-prompt vs in-page) matters.

> **Paper:** NeurIPS 2026 Evaluations & Datasets track. Build the PDF with `cd paper && pdflatex neurips_2026 && bibtex neurips_2026 && pdflatex neurips_2026 && pdflatex neurips_2026`.

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
| `configs/` | Frozen agent config, warnings, task index, run manifests (`configs/manifests/`) |
| `env/site/`, `env/tasks/` | ShopLane & WorkHub HTML shells + per-task `task.yaml` |
| `src/env/static/` | CSS/JS served by the sandbox pages |
| `src/` | Runner, scorer, prompt builder, agent wrapper |
| `scripts/` | Smoke tests and contract checks |
| `analysis/` | Aggregation + frozen `outputs/` summaries |
| `dataset/` | Hugging Face export/upload + Croissant metadata |
| `docs/` | Protocol, release split (GitHub vs HF), decision log |
| `paper/` | NeurIPS LaTeX source |

See [`docs/release.md`](docs/release.md) for what belongs on GitHub vs Hugging Face.

## Quickstart

```bash
# 0. Python 3.12 recommended (see .venv setup on macOS/Linux)
python3.12 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# 1. Credentials (env vars only — no keys in the repo)
export AWS_ACCESS_KEY_ID="..."
export AWS_API_KEY="..."        # Bedrock secret key
export AWS_REGION="us-east-1"   # optional

# 2. Verify API access
python scripts/smoke_test_api.py

# 3. Preview the sandbox
python -m http.server
# open http://localhost:8000/env/dashboard/index.html

# 4. Smoke test (single task)
python -m scripts.smoke_browseruse.run

# 5. Formal batch run
python -m src.runner.run_experiment --manifest configs/manifests/formal.yaml

# 6. Aggregate results
python -m analysis
```

## Analysis

```bash
python -m analysis
python -m analysis.aggregate_results --input-csv logs/experiment_runs/results_run_level.csv
```

Bootstrap 95% CIs (1,000 resamples, seed 42) over scorable runs. See `analysis/stats_plan.md`. Frozen paper-facing tables live in `analysis/outputs/`.

## Data release (Hugging Face)

```bash
python dataset/export_staging.py
python dataset/upload_to_hf.py
```

Staging files land in `dataset/hf_staging/` (gitignored). Dataset card: `dataset/README.md`. Croissant: `dataset/metadata/croissant.json`. Raw `logs/` stay local / optional Hub revision.

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
