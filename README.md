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

All 108 scheduled cells have valid outcomes. One malformed action was resolved by append-only adjudication under the frozen validity rule. Without a safeguard, nominal completion was 34/36 (94.4%), while trustworthy completion was 7/36 (19.4%) and unsafe completion was 27/36 (75.0%). Each safeguard had an estimated 16.7-point safety gain relative to No safeguard, although the Interface interval reached zero; trustworthy-completion gains were smaller and uncertain, and the direct system-versus-interface contrast was unresolved.

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
| `docs/benchmark_card.md` | Current Protocol v2 benchmark card |
| `docs/stakeholder_harm_annotations.md` | Frozen 12-task stakeholder and consequence annotations |

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

The public package contains 102 checks, including real-browser safe/unsafe paths, monotonic unsafe-boundary evidence, matched safeguard delivery, retry policy, formal-only analysis admission, and cost accounting. Three provenance-only checks are skipped when the intentionally unreleased raw pilot/formal interaction trees are absent.

## Reproduce the released analysis, figures, tables, and manuscript

```bash
PYTHONPATH=. .venv/bin/python -m scripts.v2.reproduce_release_v02
PYTHONPATH=. .venv/bin/python -m scripts.v2.generate_manuscript_v02_assets
PYTHONPATH=. .venv/bin/python scripts/v2/generate_publication_figures_v02.py
cd paper
tectonic --keep-logs --keep-intermediates neurips_2026.tex
tectonic --keep-logs --keep-intermediates supplement_v2_formal.tex
cd ..
PYTHONPATH=. .venv/bin/python -m scripts.v2.verify_manuscript_v02
```

The authoritative released aggregate dataset and audits are under `artifacts/v2/formal_v02_108/author_insight_review/`. The append-only correction that yields 108/108 valid outcomes is documented in `artifacts/v2/formal_v02_108/ADJUDICATION_NOTICE.md`; the byte-identical evidence bundle for that cell is included under `artifacts/v2/formal_v02_108/adjudication_evidence/`. Full raw interaction traces are not included in this anonymous review package.

Run-level tabular release files are prepared separately for Hugging Face with:

```bash
python dataset/build_hf_package_v2.py
```

## Paper

`paper/neurips_2026.tex` and `paper/neurips_2026.pdf` are the shared anonymous manuscript. The three `paper/venue_*.tex` files are thin workshop wrappers over the same scientific source, and `paper/supplement_v2_formal.tex` remains independently compilable.

## Scope and limitations

The benchmark uses curated synthetic deceptive interfaces, one frozen vision-capable agent, and no neutral-interface twins. It evaluates safeguard delivery within this controlled setting; it does not estimate a population-level effect of deceptive design, detector quality, live-site behavior, or cross-agent generality.

## Licenses

| Scope | License |
|---|---|
| Source code | MIT (`LICENSE`) |
| Non-code assets, tasks, data, and figures | CC BY-NC 4.0 (`LICENSE_DATA`) |
