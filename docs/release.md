# What goes where (GitHub vs Hugging Face)

This repo is the **benchmark code + protocol** release. Tabular run-level data is intended for **Hugging Face**.

## GitHub (this repository)

**Include**

| Path | Why |
|------|-----|
| `env/index.html`, `env/v2/shared/`, `env/v2/sites/` | **Current** 12-task Protocol v2 review portal and five consumer sites |
| `src/v2/`, `configs/v2/`, `scripts/v2/`, `tests/v2/` | Protocol v2 implementation, active runtime, dated pricing, smoke guard, and tests |
| `src/`, `scripts/`, `analysis/*.py` | Version 1 runnable benchmark + scoring + aggregation |
| `env/site/`, `env/dashboard/`, `env/tasks/`, `src/env/static/` | Historical Version 1 sandbox (kept for 81-run paper repro) |
| `configs/` | Frozen Version 1 agent config, warnings, manifests |
| `docs/archive/v1/experiment_protocol.md` | Historical 81-run protocol |
| `docs/protocol_v2_consumer.md` | Canonical Protocol v2 |
| `analysis/outputs/` | Frozen summary tables for the paper |
| `analysis/v2_pipeline.py`, `analysis/v2_precision.py`, `analysis/v2_costs.py`, `analysis/stats_plan.md` | Protocol v2 formal-only intake, preregistered analysis, and supplement cost reporting |
| `artifacts/v2/review/pre_api_readiness_report.md`, selected machine audits | Pre-API readiness evidence after author review |
| `dataset/*.py`, `dataset/README.md`, `dataset/metadata/` | HF export helpers + Croissant card |
| `paper/` (LaTeX source, figs, tabs) | Paper source (optional in anonymous supplement) |
| `LICENSE`, `LICENSE_DATA`, `README.md`, `requirements.txt` | Legal + entrypoint |
| `archive/v1_benchmark/README.md` | Pointer: Version 1 paths remain in place until freeze |

**Exclude (already gitignored)**

| Path | Why |
|------|-----|
| `logs/` | Large raw traces / screenshots; not for Git |
| `dataset/hf_staging/` | Local export before Hub upload |
| `.venv/`, `.history/`, `__pycache__/` | Local environment / editor noise |
| `paper/*.pdf`, LaTeX aux, `paper/*.txt` | Build / export junk |
| `artifacts/v2/pre_api_dry_run/` | Synthetic 108-cell pipeline validation; never release as empirical results |

## Hugging Face (dataset repo)

Target: `deceptive-web-benchmark/execution-time-warnings-web-agents` (see `dataset/upload_to_hf.py`).

**Upload**

1. `python dataset/build_hf_package.py` → `dataset/hf_staging/`
2. `python dataset/upload_to_hf.py`
3. Dataset card is copied from `dataset/README.md`; Croissant from `dataset/metadata/croissant.json`

**Do not** put API keys or raw `logs/` trees on a public Hub repo unless you intentionally release traces under `LICENSE_DATA`.

## Local-only (never commit)

- AWS / Bedrock credentials (env vars only)
- `.venv/`
- Full `logs/formal_runs/**` unless you decide on a separate restricted release
- `logs/v2/formal/**` until the author approves a trace/data release plan
- model-free pre-API dry-run attempt trees; retain locally for audit, not as a dataset
- API-backed smoke logs until the author reviews both privacy and release scope
