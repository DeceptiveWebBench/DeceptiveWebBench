# Reproducibility

## Frozen Protocol v2 environment

The formal study used Python 3.12.13, BrowserUse 0.12.6, Playwright 1.61.0, and Google Chrome 151.0.7922.138 in headless mode with a 1280 x 720 viewport, device scale factor 1, and `en-US` locale. The frozen vision-capable agent was `qwen.qwen3-vl-235b-a22b`, accessed through AWS Bedrock in `us-east-1`.

The active configuration is `configs/v2/runtime.yaml`. It records the model and request schema, sampling behavior, clean-context policy, step and timeout limits, retry policy, and dated cost configuration. The experiment crossed 12 tasks, 3 safeguard conditions, and 3 repeats for 108 scheduled cells.

## Inspect the synthetic websites

No credentials are needed to inspect or interact with the benchmark websites.

```bash
python3 -m http.server 8000 --bind 127.0.0.1
# Open http://127.0.0.1:8000/env/index.html
```

## Install and run the verification suite

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

python -m unittest discover -s tests/v2 -v
python -m scripts.v2.audit_structural_metrics
```

The public package contains 102 tests. These cover the task registry and randomized matrix, real-browser safe and unsafe paths, matched safeguard delivery, deterministic endpoint and boundary scoring, retry and timeout rules, formal-only analysis admission, and cost accounting. Three provenance-only checks skip automatically because the raw pilot/formal interaction trees are intentionally not released.

## Frozen design and scoring

- Matrix: `docs/experiment_matrix_v2.csv` (108 unique scheduled cells).
- Task registry: `configs/v2/task_registry.json`.
- Safeguard payload: `configs/v2/warnings_v0.2.yaml`.
- Run-level scoring: independent deterministic `C` and `S` checks in `src/v2/scorer.py`; no LLM judge.
- Statistical plan: 10,000 task-cluster bootstrap resamples with seed 20260807; task identity is the cluster and all conditions and repeats travel together.
- Validity: non-formal, fixture, stale-version, duplicate, missing, and invalid-retry records are rejected from formal analysis.

## Released results

The authoritative aggregate release is under `artifacts/v2/formal_v02_108/author_insight_review/`. Important entry points are:

| Artifact | Purpose |
|---|---|
| `analysis_dataset.csv` | Scored 108-cell analysis dataset |
| `condition_summary.csv` | Four-quadrant counts and C/S/TC rates |
| `contrast_bootstrap.csv` | Preregistered condition contrasts and cluster-bootstrap intervals |
| `task_condition_summary.csv` | Task-by-condition outcomes |
| `repeat_summary.csv` | Repeat-level consistency |
| `cost_summary.csv` | Cost and latency accounting |
| `data_integrity_audit.json` | Machine-readable completeness, validity, and provenance checks |
| `statistical_analysis_report.md` | Human-readable statistical report |

One malformed model action was classified as a valid behavioral safe non-completion through an append-only, hash-linked adjudication under the frozen validity rule. The original attempt artifacts were not modified and no API rerun occurred. See `artifacts/v2/formal_v02_108/ADJUDICATION_NOTICE.md`.

Raw model/browser traces are intentionally omitted from the anonymous review package. The released aggregate tables, audit hashes, deterministic scorer, registry, and statistical code support inspection of the reported results without exposing credentials or large interaction logs.

## Regenerate publication assets

```bash
python scripts/v2/generate_publication_figures_v02.py
```

## Build the paper

From `paper/`, use a compatible LaTeX installation:

```bash
pdflatex venue_ai4good.tex
bibtex venue_ai4good
pdflatex venue_ai4good.tex
pdflatex venue_ai4good.tex

pdflatex supplement_v2_formal.tex
bibtex supplement_v2_formal
pdflatex supplement_v2_formal.tex
pdflatex supplement_v2_formal.tex
```

The shared anonymous manuscript source is `paper/neurips_2026.tex`. Thin wrappers for the three considered workshops are retained alongside it; `venue_ai4good.tex` is the current primary wrapper.
