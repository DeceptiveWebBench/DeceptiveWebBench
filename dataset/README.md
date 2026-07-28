---
license: cc-by-nc-4.0
language:
  - en
tags:
  - robotics
  - safety
  - agent
  - benchmark
  - human-computer-interaction
  - web-agents
  - dark-patterns
pretty_name: Deception Warning Study (ShopLane / WorkHub)
size_categories:
  - n<1K
---

# Deception Warning Study — benchmark runs (staging)

This repository will host **run-level** rows for the controlled benchmark described in the companion paper (NeurIPS-style release).

## Contents (when populated)

| Artifact | Description |
|----------|-------------|
| `run_level.jsonl` / `run_level.csv` | One row per merged run: task, condition, repeat, outcome, flags |
| `run_level.parquet` | Optional if `pyarrow` is installed (Hub-friendly) |
| `manifest.yaml` (optional) | `benchmark_version`, `repeats_per_task_condition`, model snapshot |

**Raw logs** (screenshots, `terminal_state.json`, traces) are large; they may ship as a separate revision or via restricted access—document here before upload.

## Build staging files (local)

From repo root, after `python -m analysis`:

```bash
python dataset/export_staging.py
```

Outputs go to `dataset/hf_staging/` (gitignored). Croissant metadata lives at `dataset/metadata/croissant.json` (copy onto the Hub with the tabular files if desired). Review then:

```bash
pip install huggingface_hub datasets pyarrow  # as needed
python dataset/upload_to_hf.py
```

## Upload to the Hub (outline)

1. Create a dataset repo on Hugging Face (default id in `upload_to_hf.py`: `deceptive-web/deception-warning-study-runs`).
2. Use this file as the dataset card; fill license, citation, and author fields before public release.
3. Upload staging folder (`run_level.*`) via `python dataset/upload_to_hf.py`; optionally add `metadata/croissant.json`.
4. Companion code lives on GitHub; see the code repo `docs/release.md`.

## Citation

```bibtex
@misc{deception_warning_study_2026,
  title        = {Warning Placement for Web Agents under Deceptive Interfaces},
  author       = {[Anonymous]},
  year         = {2026},
  howpublished = {Hugging Face Dataset},
  url          = {https://huggingface.co/datasets/deceptive-web/deception-warning-study-runs}
}
```
