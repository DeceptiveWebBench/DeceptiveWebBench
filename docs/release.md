# What goes where (GitHub vs Hugging Face)

This repo is the **benchmark code + protocol** release. Tabular run-level data is intended for **Hugging Face**.

## GitHub (this repository)

**Include**

| Path | Why |
|------|-----|
| `src/`, `scripts/`, `analysis/*.py` | Runnable benchmark + scoring + aggregation |
| `env/site/`, `env/tasks/`, `src/env/static/` | Sandbox pages, tasks, static assets |
| `configs/` | Frozen agent config, warnings, manifests |
| `docs/archive/v1/experiment_protocol.md` | Historical 81-run protocol |
| `docs/protocol_v2_consumer.md` | Canonical Protocol v2 |
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
