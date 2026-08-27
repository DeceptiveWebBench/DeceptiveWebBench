# Trustworthy Completion for Web Agents

A controlled benchmark for evaluating web agents when nominal task completion can conflict with user interests, consent, autonomy, privacy, or policy constraints.

The benchmark separates endpoint completion (`C`) from avoidance of a machine-verifiable unsafe commitment (`S`). **Trustworthy Completion** is their conjunction: `TC = C AND S`.

## Study snapshot

| Item | Frozen Protocol v2 design |
|---|---|
| Tasks | 12 synthetic consumer tasks |
| Pattern families | Forced action, sneaking, interface interference |
| Conditions | No safeguard, system-delivered safeguard, interface-delivered safeguard |
| Repeats | 3 per task-condition cell |
| Scheduled cells | 108 |
| Agent | `qwen.qwen3-vl-235b-a22b` via AWS Bedrock, BrowserUse 0.12.6 |
| Scoring | Deterministic endpoint and trajectory-state checks; no LLM judge |

All 108 scheduled cells have valid outcomes. One malformed action was resolved by append-only adjudication under the frozen validity rule. Without a safeguard, nominal completion was 34/36 (94.4%), while trustworthy completion was 7/36 (19.4%) and unsafe completion was 27/36 (75.0%). Both safeguard strategies increased safety, with smaller and uncertain changes in trustworthy completion; the direct system-versus-interface contrast was unresolved.

## Repository layout

| Path | Role |
|---|---|
| `env/index.html`, `env/v2/` | Protocol v2 review portal and five synthetic consumer sites |
| `configs/v2/` | Frozen task registry, safeguard, runtime, pricing, and authorization records |
| `src/v2/` | Runner, adapter, state machine, deterministic scorer, cost accounting, and artifact contracts |
| `scripts/v2/` | Verification, analysis, adjudication, and publication-asset commands |
| `tests/v2/` | Protocol, browser, runner, cost, and formal-analysis tests |
| `analysis/` | Statistical plan and formal analysis pipeline |
| `artifacts/v2/formal_v02_108/` | Frozen aggregate results, audits, and analysis outputs |
| `paper/` | Anonymous manuscript source, supplement, figures, and tables |
| `archive/v1_benchmark/` | Pointer to the historical Version 1 benchmark paths |

## Preview the benchmark

No API credentials are needed to inspect the websites.

```bash
python3 -m http.server 8000 --bind 127.0.0.1
# Open http://127.0.0.1:8000/env/index.html
```

## Install and verify

Python 3.12 is recommended.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

python -m unittest discover -s tests/v2 -v
python -m scripts.v2.audit_structural_metrics
```

The complete test suite contains 102 checks, including real-browser safe/unsafe paths, monotonic unsafe-boundary evidence, matched safeguard delivery, retry policy, formal-only analysis admission, and cost accounting.

## Reproduce the frozen analysis and manuscript

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

The release-safe analysis command rebuilds all manuscript aggregates from the tracked 108-row dataset, verifies the canonical matrix and released append-only adjudication evidence, and makes no model/API call. Full provider traces and raw screenshots are intentionally omitted from the anonymous package and are not reconstructable from the tabular release. An optional tabular export package is prepared locally with:

```bash
python dataset/build_hf_package_v2.py
```

## Paper

`paper/neurips_2026.tex` is the shared anonymous master. Its PDF contains the eight-page main text, references, formal appendix, and official checklist in one file. The three `paper/venue_*.tex` files are thin header-only wrappers over the same scientific source. `paper/supplement_v2_formal.tex` remains independently compilable from the same appendix content.

## Scope and limitations

The benchmark uses curated synthetic deceptive interfaces, one frozen vision-capable agent, and no neutral-interface twins. It evaluates safeguard delivery within this controlled setting; it does not estimate a population-level effect of deceptive design, detector quality, live-site behavior, or cross-agent generality.

## Licenses

| Scope | License |
|---|---|
| Source code | MIT (`LICENSE`) |
| Non-code assets, tasks, data, and figures | CC BY-NC 4.0 (`LICENSE_DATA`) |
