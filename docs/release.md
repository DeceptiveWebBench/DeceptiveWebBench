# What goes where (GitHub vs Hugging Face)

This repo is the **benchmark code + protocol** release. Tabular run-level data is intended for **Hugging Face**.

## GitHub (this repository)

**Include**

| Path | Why |
|------|-----|
| `src/`, `scripts/`, `analysis/*.py` | Runnable benchmark + scoring + aggregation |
| `env/site/`, `env/tasks/`, `src/env/static/` | Sandbox pages, tasks, static assets |
| `configs/` | Frozen agent config, warnings, manifests |
| `docs/experiment_protocol.md` | Canonical protocol |
| `analysis/outputs/` | Frozen summary tables for the paper |
| `dataset/*.py`, `dataset/README.md`, `dataset/metadata/` | HF export helpers + Croissant card |
| `paper/` (LaTeX source, figs, tabs) | Paper source (optional in anonymous supplement) |
| `LICENSE`, `LICENSE_DATA`, `README.md`, `requirements.txt` | Legal + entrypoint |

**Exclude (already gitignored)**

| Path | Why |
|------|-----|
| `logs/` | Large raw traces / screenshots; not for Git |
| `dataset/hf_staging/` | Local export before Hub upload |
| `.venv/`, `.history/`, `__pycache__/` | Local environment / editor noise |
| `paper/*.pdf`, LaTeX aux, `paper/*.txt` | Build / export junk |

## Hugging Face (dataset repo)

Target: `deceptive-web/deception-warning-study-runs` (see `dataset/upload_to_hf.py`).

**Upload**

1. `run_level.csv` / `run_level.jsonl` / `run_level.parquet` (from `dataset/export_staging.py`)
2. Copy `dataset/README.md` as the dataset card
3. Optionally include `dataset/metadata/croissant.json`

**Do not** put API keys or raw `logs/` trees on a public Hub repo unless you intentionally release traces under `LICENSE_DATA`.

## Local-only (never commit)

- AWS / Bedrock credentials (env vars only)
- `.venv/`
- Full `logs/formal_runs/**` unless you decide on a separate restricted release
