# Trustworthy Completion for Web Agents

A controlled local benchmark for evaluating trustworthy completion when nominal web-agent success can conflict with user interests, consent, autonomy, privacy, or policy constraints.

> **Paper:** Trustworthy AI for Good Workshop, NeurIPS 2026. The Version 1 A--C package uses the frozen 81-run pilot; D/E experiments are Research Agenda items only.

## Key ideas

| Concept | Detail |
|---------|--------|
| **Conditions** | No Warning · System Warning · UI Warning (matched semantics, channel varies) |
| **Pattern families** | Interface interference · Sneaking · Forced action |
| **Outcome schema** | Safe completion · Unsafe completion · Safe abort · Other failure |
| **Scoring** | Deterministic terminal-state checks (no LLM judge) |
| **Agent** | BrowserUse + Amazon Nova Lite v1 (Bedrock), fixed across conditions |

## Repository layout

| Path | Role |
|------|------|
| `env/index.html` | **Current** local entry — Protocol v2 ShopLane (4 tasks × 3 conditions) |
| `env/v2/sites/shoplane/` | Current formal v2 ShopLane sandbox |
| `env/v2/site/` | Temporary prototypes for other v2 tasks (still in development) |
| `configs/v2/`, `src/v2/`, `scripts/v2/`, `tests/v2/` | Protocol v2 implementation |
| `env/dashboard/`, `env/site/`, `env/tasks/`, `src/env/static/` | Historical Version 1 benchmark (9 tasks / 81 runs; keep for paper repro) |
| `configs/` | Frozen Version 1 agent config, warnings, manifests (`configs/manifests/`) |
| `src/` | Version 1 runner, scorer, prompt builder, agent wrapper |
| `scripts/` | Smoke tests and contract checks |
| `analysis/` | Aggregation + frozen `outputs/` summaries |
| `dataset/` | Hugging Face export/upload + Croissant metadata |
| `docs/` | Protocol, release split (GitHub vs HF), decision log |
| `paper/` | NeurIPS LaTeX source |
| `archive/v1_benchmark/` | Pointer README only (physical archive deferred) |

See [`docs/release.md`](docs/release.md) for what belongs on GitHub vs Hugging Face.

## Quickstart

```bash
# 0. Python 3.12 recommended (see .venv setup on macOS/Linux)
python3.12 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# 1. Credentials (env vars only — no keys in the repo)
export AWS_ACCESS_KEY_ID="..."
export AWS_API_KEY="..."        # Bedrock secret key
export AWS_REGION="us-east-1"   # optional

# 2. Verify API access
python scripts/smoke_test_api.py

# 3. Preview the current v2 ShopLane entry
python3 -m http.server 8000 --bind 127.0.0.1
# open http://127.0.0.1:8000/env/index.html
# Historical Version 1 dashboard (not the current entry): env/dashboard/index.html

# 4. Smoke test (single task; Version 1 path)
python -m scripts.smoke_browseruse.run

# 5. Reproduce the frozen paper analysis (does not run an agent)
python -m analysis --input-csv logs/experiment_runs/results_run_level.csv \
  --output-dir analysis/outputs --bootstrap-samples 10000 --seed 42
python analysis/generate_figures.py
```

## Analysis

```bash
python -m analysis
python -m analysis.aggregate_results --input-csv logs/experiment_runs/results_run_level.csv
```

Task-cluster-bootstrap 95% intervals use 10,000 resamples and seed 42. Outcome rates use explicitly labeled scorable or all-run denominators. Frozen paper-facing tables, the 72-run wording-deviation sensitivity view, and the 81-row run manifest live in `analysis/outputs/`.

## Data release (Hugging Face)

```bash
python dataset/build_hf_package.py
python dataset/upload_to_hf.py
```

Staging files land in `dataset/hf_staging/` (gitignored). Public dataset: [deceptive-web-benchmark/execution-time-warnings-web-agents](https://huggingface.co/datasets/deceptive-web-benchmark/execution-time-warnings-web-agents).

## Licenses

| Scope | License |
|-------|---------|
| Source code | MIT (`LICENSE`) |
| Non-code assets (tasks, data, figures) | CC BY-NC 4.0 (`LICENSE_DATA`) |

## Terminology (paper ↔ code)

| Paper phrasing | Identifier |
|----------------|------------|
| Interface interference | `interface_interference` |
| Sneaking | `sneaking` |
| Forced action | `forced_action` |
