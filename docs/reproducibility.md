# Reproducibility

## Protocol v2 pre-API environment

The verified local candidate uses Python **3.12.13**, BrowserUse **0.12.6**, Playwright
**1.61.0**, Google Chrome **151.0.7922.138**, a 1280×720 viewport, and `en-US` locale.
Exact package and source hashes are recorded in
`artifacts/v2/review/non_model_freeze_candidate.json`. `requirements.txt` is a dependency
specification rather than a complete lock, so the installed-environment hash must be frozen again
after the final clean install and repository commit.

The unique active v2 runtime is `configs/v2/runtime.yaml`. It freezes AWS Bedrock Claude Sonnet
4.6, the documented model identifier, region/request version, sampling, headless browser settings,
four distinct timeout levels, and retry policy. `configs/v2/pricing.yaml` freezes the dated standard
price used for reconstruction. Access/inference-profile resolution and actual provider event/usage
fields remain first-smoke checks. The static pre-API workflow neither needs nor reads credentials.

## Local sandbox entry (Protocol v2)

The current author-review entry covers all 12 Protocol v2 tasks:

```bash
cd DeceptiveWebBench
python3 -m http.server 8000 --bind 127.0.0.1
# open http://127.0.0.1:8000/env/index.html
```

`env/dashboard/index.html` is the historical Version 1 BenchScope dashboard for the 9-task / 81-run suite. New work should not treat it as the default entry. Path notes: `archive/v1_benchmark/README.md`.

## Canonical commands

| Step | Command |
|------|---------|
| Preview all 12 v2 tasks | `python3 -m http.server 8000 --bind 127.0.0.1` → `http://127.0.0.1:8000/env/index.html` |
| Full v2 contracts and real-browser paths | `./.venv/bin/python -m unittest discover -s tests/v2 -v` |
| Structural comparability audit | `./.venv/bin/python -m scripts.v2.audit_structural_metrics` |
| Complete model-free 108-cell dry run | `./.venv/bin/python -m scripts.v2.run_pre_api_dry_run` |
| Design-only repeat precision audit | `./.venv/bin/python -m scripts.v2.run_precision_audit` |
| Capture non-model freeze candidate | `./.venv/bin/python -m scripts.v2.build_freeze_candidate` |
| Confirm formal guard | `./.venv/bin/python -m scripts.v2.run_schedule --formal` (must exit blocked) |
| Static smoke preflight (no credential read) | `PYTHONPATH=. ./.venv/bin/python scripts/v2/preflight_api_smoke.py` |

The separately authorized real-smoke sequence is documented in `docs/smoke_api_handoff.md`. It is
not part of model-free verification and has not been run.

## Paper build

From `paper/`, using Tectonic 0.16.9 or a compatible LaTeX installation:

```bash
tectonic --keep-logs neurips_2026.tex
tectonic --keep-logs supplement_v1_2026-08-09.tex
```

The released files are `paper/paper_v1_AC_2026-08-09.pdf` and `paper/supplement_v1_2026-08-09.pdf`. The main PDF has seven pages total; the main text ends on page 5 and References begins on page 6, satisfying the 2--8 page main-text limit.

## Protocol v2 seeds, scoring, and analysis admission

- Planned aggregation: **10,000 task-cluster resamples**, seed **20260807**; task identity
  is the cluster and all conditions/repeats travel together.
- Outcomes: independent deterministic C/S checks in `src/v2/scorer.py`; no LLM judge.
- Formal analysis rejects `formal_run=false`, `synthetic_fixture=true`, stale task versions, stale
  matrix hashes, duplicate/missing cells, and invalid retry sequences.
- Historical Version 1 reproduction remains governed by `docs/archive/v1/experiment_protocol.md`
  and its frozen commands. It is not a fallback input for Protocol v2.

The pre-API dry run writes only to `artifacts/v2/pre_api_dry_run/`, declares
`formal_run=false`, `synthetic_fixture=true`, and `agent_model_call=false`, and prohibits treatment
analysis. It does not write `logs/v2/formal/` or produce paper-facing results.

## Artifacts

| Artifact | Location |
|----------|----------|
| Protocol v2 registry/matrix | `configs/v2/`, `docs/experiment_matrix_v2.csv` |
| Pre-API machine audits | `artifacts/v2/review/` |
| Model-free dry run | `artifacts/v2/pre_api_dry_run/` (local validation only) |
| Future formal v2 attempts | `logs/v2/formal/` (currently empty and authorization-guarded) |
| Historical Version 1 summaries | `analysis/outputs/` (frozen) |
