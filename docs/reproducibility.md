# Reproducibility

## Released Protocol v2 evidence

The anonymous release contains the 108-row selected-cell dataset, the 112-row attempt audit, all aggregate CSVs used by the manuscript, frozen configurations and hashes, and a byte-identical evidence bundle for the one append-only adjudicated cell. Full provider traces and raw screenshots are intentionally omitted; the release does not claim that omitted traces can be reconstructed.

The formal environment used Python 3.12.13, BrowserUse 0.12.6, Playwright 1.61.0, Google Chrome 151.0.7922.138, a 1280×720 headless viewport, and `en-US` locale. The evaluated endpoint was `qwen.qwen3-vl-235b-a22b` through AWS Bedrock in `us-east-1`. Exact non-model and protocol hashes are recorded in the v2 manifests and formal audit.

## Clean installation

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Tectonic is used for the documented PDF build. A compatible LaTeX installation may also be used if it preserves the official style and page geometry.

## One empirical reproduction pipeline

```bash
PYTHONPATH=. .venv/bin/python -m scripts.v2.reproduce_release_v02
PYTHONPATH=. .venv/bin/python -m scripts.v2.generate_manuscript_v02_assets
PYTHONPATH=. .venv/bin/python scripts/v2/generate_publication_figures_v02.py

cd paper
tectonic --keep-logs --keep-intermediates neurips_2026.tex
tectonic --keep-logs --keep-intermediates supplement_v2_formal.tex
tectonic --keep-logs --keep-intermediates venue_iaeval.tex
tectonic --keep-logs --keep-intermediates venue_ai4good.tex
tectonic --keep-logs --keep-intermediates venue_verify_agents.tex
cd ..

PYTHONPATH=. .venv/bin/python -m scripts.v2.verify_manuscript_v02
```

`reproduce_release_v02` recomputes condition, task, repeat, family, transition, termination, leave-one-task-out, bootstrap, and cost aggregates from the released 108 rows and compares every CSV byte-for-byte with the audited source. It verifies the 108 unique canonical matrix cells and re-scores the released adjudication evidence. It never reads ignored formal logs or calls a model/API.

The shared master PDF is ordered as eight pages of main text, references, formal appendix, and the official checklist. The standalone supplement inputs the same appendix source; it is not a manually maintained second data narrative.

## Full internal audit versus anonymous reproduction

The internal raw-attempt audit additionally rebuilds selected outcomes from 451 JSON artifacts in the local ignored `logs/v2/formal/` tree. Those full traces are deliberately outside the anonymous release. The tracked `data_integrity_audit.json` records the frozen raw-tree hash and deterministic-rescoring result, while the release-safe pipeline independently checks everything that can be verified from the released package.

Historical Version 1 reproduction remains governed by `docs/archive/v1/` and is not an input to Protocol v2 results.
