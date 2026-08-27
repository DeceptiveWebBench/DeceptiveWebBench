---
license: cc-by-nc-4.0
language:
  - en
tags:
  - safety
  - web-agents
  - benchmark
  - dark-patterns
  - trustworthy-ai
pretty_name: Trustworthy Completion for Web Agents
size_categories:
  - n<1K
---

# Trustworthy Completion for Web Agents

This release contains the audited 108-run Protocol v2 results used in *Beyond Endpoint Success: Trustworthy Completion for Web Agents*. The benchmark independently records nominal completion (`C_r`) and whether a trajectory avoided its machine-verifiable unsafe commitment boundary (`S_r`), with `TC_r = C_r AND S_r`.

Anonymous code, documentation, and released data: [DeceptiveWebBench anonymous artifact](https://anonymous.4open.science/r/DeceptiveWebBench-960E/).

## Study design

- one frozen vision-capable web-agent configuration;
- 12 synthetic consumer tasks across forced action, sneaking, and interface interference;
- No safeguard, system-delivered safeguard, and interface-delivered safeguard;
- three repeats per task-condition cell (108 scheduled and 108 valid outcomes);
- one append-only protocol-consistency adjudication, with no rerun and preserved evidence.

The study contains deceptive interfaces only. It does not estimate a deception-versus-neutral causal effect, detector performance, cross-agent generality, human behavior, or live-deployment effectiveness.

## Released files

The v2 package builder creates:

| Path | Description |
|---|---|
| `run_level.csv` / `.jsonl` / `.parquet` | One row per scheduled cell (108 rows) |
| `attempt_audit.csv` | All 112 attempts, including invalid/retry accounting |
| `formal_run_manifest.csv` | Scheduled-cell provenance |
| `summaries/` | Prespecified summaries and labeled exploratory/post-hoc analyses |
| `audit/` | Integrity audit, append-only adjudication notice, and number provenance |
| `metadata/` | Data dictionary, hashes, and Croissant metadata |

Full provider traces, prompts, model responses, and screenshots are intentionally omitted. The release does not claim they can be reconstructed. The released adjudication evidence in the anonymous code artifact is sufficient to verify the corrected cell against its unchanged original JSON evidence.

## Reproduce

From the anonymous repository root:

```bash
PYTHONPATH=. .venv/bin/python -m scripts.v2.reproduce_release_v02
PYTHONPATH=. .venv/bin/python -m scripts.v2.generate_manuscript_v02_assets
PYTHONPATH=. .venv/bin/python scripts/v2/generate_publication_figures_v02.py
```

## License

Non-code data assets are released under CC BY-NC 4.0. See `LICENSE_DATA`.

## Citation

```bibtex
@misc{trustworthy_completion_web_agents_2026,
  title  = {Beyond Endpoint Success: Trustworthy Completion for Web Agents},
  author = {[Anonymous]},
  year   = {2026},
  url    = {https://anonymous.4open.science/r/DeceptiveWebBench-960E/}
}
```
