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
| Verify frozen inputs | `./.venv/bin/python scripts/verify_analysis_freeze.py` |
| Aggregate existing runs | `./.venv/bin/python -m analysis --input-csv logs/experiment_runs/results_run_level.csv --output-dir analysis/outputs --bootstrap-samples 10000 --seed 42` |
| Generate figure | `./.venv/bin/python analysis/generate_figures.py` |
| Verify paper-facing numbers | `./.venv/bin/python scripts/verify_paper_numbers.py` |
| HF staging | `python dataset/build_hf_package.py` then `python dataset/upload_to_hf.py` |

## Paper build

From `paper/`, using Tectonic 0.16.9 or a compatible LaTeX installation:

```bash
tectonic --keep-logs neurips_2026.tex
tectonic --keep-logs supplement_v1_2026-08-09.tex
```

The released files are `paper/paper_v1_AC_2026-08-09.pdf` and `paper/supplement_v1_2026-08-09.pdf`. The main PDF has seven pages total; the main text ends on page 5 and References begins on page 6, satisfying the 2--8 page main-text limit.

## Seeds and scoring

- Aggregation bootstrap: **10,000 task-cluster resamples**, seed **42** (`analysis/stats_plan.md`)
- Outcomes: deterministic terminal-state checks (`src/scorer/`), no LLM judge
- Historical 81-run protocol: `docs/archive/v1/experiment_protocol.md` (the new study is governed by `docs/protocol_v2_consumer.md`)

The paper-facing workflow reads the existing canonical CSV only. It does not invoke the formal-run command, rerun an agent, merge substitute rows, or mutate raw artifacts. The requested `interface_perm_001` sensitivity view excludes exactly nine existing cells and is generated in the same aggregation command.

## Artifacts

| Artifact | Location |
|----------|----------|
| Frozen summaries | `analysis/outputs/` (in git) |
| Raw run logs | `logs/` (local; not on GitHub) |
| Run-to-artifact manifest | `analysis/outputs/run_manifest_v1.csv` |
| Hub tabular export | `dataset/hf_staging/` → Hugging Face |
| Croissant card | `dataset/metadata/croissant.json` |
