# Reproducibility

## Software

- Python **3.12** (recommended; 3.14 not validated)
- Dependencies: `requirements.txt` (UTF-8). After install: `playwright install chromium`
- Agent stack: BrowserUse + Amazon Nova Lite v1 via AWS Bedrock (`configs/main_config.yaml`)

## Credentials

Set only via environment variables (never commit):

- `AWS_ACCESS_KEY_ID`
- `AWS_API_KEY` (Bedrock secret; see `scripts/smoke_test_api.py`)
- `AWS_REGION` (default `us-east-1`)

## Canonical commands

| Step | Command |
|------|---------|
| API smoke | `python scripts/smoke_test_api.py` |
| Contract check | `python scripts/verify_warning_task_contract.py` |
| Formal run | `python -m src.runner.run_experiment --manifest configs/manifests/formal.yaml` |
| ShopLane only | `... --manifest configs/manifests/shoplane.yaml` |
| Enterprise only | `... --manifest configs/manifests/enterprise.yaml` |
| Aggregate | `python -m analysis` |
| HF staging | `python dataset/export_staging.py` |

## Seeds and scoring

- Aggregation bootstrap: **1,000** resamples, seed **42** (`analysis/stats_plan.md`)
- Outcomes: deterministic terminal-state checks (`src/scorer/`), no LLM judge
- Protocol source of truth: `docs/experiment_protocol.md` (overridden by configs / `task.yaml` / sandbox JS if prose drifts)

## Artifacts

| Artifact | Location |
|----------|----------|
| Frozen summaries | `analysis/outputs/` (in git) |
| Raw run logs | `logs/` (local; not on GitHub) |
| Hub tabular export | `dataset/hf_staging/` → Hugging Face |
| Croissant card | `dataset/metadata/croissant.json` |
