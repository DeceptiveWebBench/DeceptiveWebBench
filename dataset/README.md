---
license: cc-by-nc-4.0
language:
  - en
tags:
  - safety
  - agent
  - benchmark
  - human-computer-interaction
  - web-agents
  - dark-patterns
pretty_name: Trustworthy Completion for Web Agents (ShopLane / WorkHub)
size_categories:
  - n<1K
---

# Trustworthy Completion for Web Agents — frozen pilot results

Controlled benchmark runs distinguishing safe completion, unsafe completion, safe abort, and other failure under deceptive web interfaces. The pilot evaluates agent response under oracle task annotations; it does not establish a generally superior warning channel.

Companion code (anonymous review mirror): [anonymous.4open.science/r/DeceptiveWebBench-960E](https://anonymous.4open.science/r/DeceptiveWebBench-960E/)

## Contents

| Path | Description |
|------|-------------|
| `run_level.csv` / `run_level.jsonl` / `run_level.parquet` | One row per formal run (81 rows): task, condition, repeat, outcome |
| `export_meta.json` | Export provenance (schema version, columns, row count) |
| `summaries/` | Frozen aggregate tables matching the paper analysis |
| `run_manifest_v1.csv` | Machine-readable 81-cell provenance and artifact hashes |
| `raw_runs/{shoplane,enterprise}/<run_id>/` | Per-run `terminal_state.json`, `final_result.json`, scrubbed `run_metadata.json` |
| `croissant.json` | Croissant metadata card (optional consumers) |

**Not included:** smoke/debug/retry logs, screenshots (empty in this release), source code / task HTML (see code repo).

## Schema (`run_level`)

| Column | Meaning |
|--------|---------|
| `run_id` | Unique run folder id |
| `task_id` | Task identifier |
| `pattern_family` | `forced_action` / `sneaking` / `interface_interference` |
| `condition` | `no_warning` / `system_warning` / `ui_warning` |
| `repeat_id` | Repeat index (1–3) |
| `outcome_label` / `terminal_state` | Deterministic outcome label |
| `risk_taken` / `safe_path` / `completed` | Boolean flags from scorer |
| `task_goal_source` / `system_warning_source` | Provenance pointers into the code repo |

## Completed evidence and planned extensions

Completed: one fixed BrowserUse/Amazon Nova Lite v1 configuration, nine synthetic tasks, three warning conditions, three repeats, deterministic scoring, task-cluster uncertainty, and the documented `interface_perm_001` wording-deviation sensitivity view.

Planned only: cross-agent validation, warning-wording experiments, detector-coupled evaluation, broader task coverage, long-horizon tasks, and human calibration. The dataset contains no D/E results.

## License

Non-code data assets: **CC BY-NC 4.0**.

## Citation

```bibtex
@misc{execution_time_warnings_web_agents_2026,
  title        = {Trustworthy Completion for Web Agents: A Benchmark and Research Agenda for Execution-Time Safeguards},
  author       = {[Anonymous]},
  year         = {2026},
  howpublished = {Hugging Face Dataset},
  url          = {https://huggingface.co/datasets/deceptive-web-benchmark/execution-time-warnings-web-agents}
}
```
