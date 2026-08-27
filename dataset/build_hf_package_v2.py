"""Build the public Protocol v2 Hugging Face dataset package.

The package is assembled only from audited formal-v0.2 outputs. It excludes raw
prompts, screenshots, model responses, credentials, and local debug artifacts.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "artifacts" / "v2" / "formal_v02_108"
REVIEW = FORMAL / "author_insight_review"
MANUSCRIPT = FORMAL / "manuscript_update"
OUT = ROOT / "dataset" / "hf_staging_v2"


SUMMARY_FILES = [
    "condition_summary.csv",
    "contrast_bootstrap.csv",
    "task_condition_summary.csv",
    "paired_transitions.csv",
    "termination_summary.csv",
    "repeat_summary.csv",
    "family_summary_exploratory.csv",
    "leave_one_task_out_posthoc.csv",
    "cost_summary.csv",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def write_readme() -> None:
    text = """---
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

This release contains audited run-level results from a controlled study of execution-time safeguards for web agents under deceptive consumer interfaces.

The benchmark independently scores nominal completion (`C`) and trajectory safety (`S`): trustworthy completion (`C=1,S=1`), unsafe completion (`C=1,S=0`), safe non-completion (`C=0,S=1`), and unsafe failure (`C=0,S=0`).

## Study design

- One frozen vision-capable web-agent configuration
- 12 synthetic consumer tasks: four forced-action, four sneaking, and four interface-interference tasks
- Three conditions: `no_warning`, `system_warning`, and `ui_warning` (the latter two correspond to System-delivered and Interface-delivered safeguards)
- Three scheduled repeats per task-condition cell
- 108 scheduled cells and 108 valid outcomes after one append-only protocol-consistency adjudication (see `audit/ADJUDICATION_NOTICE.md`)

System-delivered and Interface-delivered safeguards use byte-identical, task-independent content available before the first agent action. The comparison concerns complete delivery strategies, not a universal channel effect. All interfaces are deceptive variants, so the data do not estimate the causal effect of deception relative to a neutral interface.

## Files

- `run_level.csv`, `run_level.jsonl`, `run_level.parquet`: one row per scheduled cell
- `attempt_audit.csv`: all recorded attempts, including invalid attempts and retries
- `formal_run_manifest.csv`: compact scheduled-cell manifest
- `summaries/`: prespecified summaries and clearly labeled exploratory/post-hoc analyses
- `audit/`: integrity audit, adjudication notice, and manuscript-number provenance
- `metadata/`: data dictionary, hash manifest, and Croissant metadata

No raw prompts, model responses, screenshots, credentials, or personal data are included.

## Scope

Results describe one frozen agent configuration on this curated synthetic task suite. They should not be generalized to all agents, live websites, humans, or population-level harms. Family summaries are exploratory, and `leave_one_task_out_posthoc.csv` is explicitly post hoc.

## License

Non-code data assets are released under CC BY-NC 4.0. See `LICENSE_DATA`.

## Citation

```bibtex
@misc{trustworthy_completion_web_agents_2026,
  title        = {Beyond Endpoint Success: Trustworthy Completion for Web Agents},
  author       = {[Anonymous]},
  year         = {2026},
  howpublished = {Anonymous artifact},
  url          = {https://anonymous.4open.science/r/DeceptiveWebBench-960E/}
}
```
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def write_dictionary(frame: pd.DataFrame) -> None:
    descriptions = {
        "planned_order": "Deterministic randomized position in the formal schedule.",
        "scheduled_run_id": "Unique identifier for a scheduled task-condition-repeat cell.",
        "task_id": "Benchmark task identifier.",
        "task_version": "Frozen task version used for collection.",
        "pattern_family": "Deceptive-interface family.",
        "condition": "Safeguard condition.",
        "repeat_id": "Scheduled repeat index (1-3).",
        "n_attempts": "Number of preserved attempts for the scheduled cell.",
        "selected_attempt": "Attempt selected under the validity/retry protocol.",
        "valid": "Whether the scheduled cell has a valid selected attempt.",
        "unavailable": "Whether the cell remained unavailable after allowed retry.",
        "C": "Nominal completion indicator.",
        "S": "Trajectory safety indicator; 1 iff no unsafe boundary was crossed.",
        "TC": "Trustworthy-completion indicator, equal to C multiplied by S.",
        "outcome": "One of the four C/S outcomes, or unavailable.",
        "termination_class": "Structured non-completion class when applicable.",
        "termination_reason": "Recorded termination reason when available.",
        "unsafe_boundary_first_step": "First logged step crossing the unsafe boundary.",
        "termination_step": "Step at which the run terminated.",
        "model_calls": "Number of model calls with recorded usage for the selected attempt.",
        "input_tokens": "Recorded provider input tokens.",
        "output_tokens": "Recorded provider output tokens.",
        "total_tokens": "Recorded input plus output tokens.",
        "wall_clock_seconds": "Selected-attempt wall-clock duration.",
        "model_latency_seconds": "Accumulated model-service latency.",
        "known_cost_usd": "Known provider cost in USD.",
        "cost_known": "Whether provider cost is known for the selected attempt.",
        "clean_context_id": "Random identifier documenting browser-context isolation.",
        "selected_attempt_path": "Repository-relative provenance path for the selected attempt.",
    }
    rows = [
        "# Data dictionary",
        "",
        "`run_level.*` contains one row for each of the 108 scheduled cells. All 108 rows have valid selected outcomes after the documented append-only adjudication; no cell was rerun or imputed.",
        "",
        "| Column | Storage type | Description |",
        "|---|---|---|",
    ]
    for column in frame.columns:
        rows.append(f"| `{column}` | `{frame[column].dtype}` | {descriptions.get(column, 'Audited run-level field.')} |")
    rows.extend([
        "",
        "## Outcome vocabulary",
        "",
        "- `trustworthy_completion`: `C=1,S=1`",
        "- `unsafe_completion`: `C=1,S=0`",
        "- `safe_non_completion`: `C=0,S=1`",
        "- `unsafe_failure`: `C=0,S=0`",
        "- `unavailable`: no valid selected attempt after the allowed infrastructure retry",
        "",
        "Infrastructure validity is separate from the C/S outcome variables. See `audit/ADJUDICATION_NOTICE.md` and `audit/data_integrity_audit.json`.",
    ])
    (OUT / "metadata" / "data_dictionary.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_croissant(frame: pd.DataFrame) -> None:
    fields = []
    for column in frame.columns:
        fields.append({
            "@type": "cr:Field",
            "@id": f"run_level/{column}",
            "name": column,
            "dataType": "sc:Text",
            "source": {"fileObject": {"@id": "run_level.csv"}, "extract": {"column": column}},
        })
    data = {
        "@context": {"@language": "en", "@vocab": "https://schema.org/", "cr": "http://mlcommons.org/croissant/"},
        "@type": "sc:Dataset",
        "name": "Trustworthy Completion for Web Agents",
        "description": "Audited run-level results for execution-time safeguards under deceptive consumer interfaces.",
        "license": "https://creativecommons.org/licenses/by-nc/4.0/",
        "url": "https://anonymous.4open.science/r/DeceptiveWebBench-960E/",
        "distribution": [{
            "@type": "cr:FileObject",
            "@id": "run_level.csv",
            "name": "run_level.csv",
            "contentUrl": "run_level.csv",
            "encodingFormat": "text/csv",
            "sha256": sha256(OUT / "run_level.csv"),
        }],
        "recordSet": [{"@type": "cr:RecordSet", "@id": "run_level", "name": "run_level", "field": fields}],
    }
    (OUT / "metadata" / "croissant.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_manifest(frame: pd.DataFrame) -> None:
    files = []
    for path in sorted(p for p in OUT.rglob("*") if p.is_file() and p.name != "export_manifest.json"):
        files.append({
            "path": path.relative_to(OUT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    manifest = {
        "release": "protocol-v2-formal-v0.2",
        "scheduled_cells": int(len(frame)),
        "valid_cells": int(frame["valid"].sum()),
        "unavailable_cells": int(frame["unavailable"].sum()),
        "source": "artifacts/v2/formal_v02_108",
        "files": files,
    }
    (OUT / "metadata" / "export_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "summaries").mkdir(parents=True)
    (OUT / "audit").mkdir(parents=True)
    (OUT / "metadata").mkdir(parents=True)

    frame = pd.read_csv(REVIEW / "analysis_dataset.csv")
    if len(frame) != 108 or int(frame["valid"].sum()) != 108 or int(frame["unavailable"].sum()) != 0:
        raise ValueError("Unexpected audited run-level accounting")
    frame.to_csv(OUT / "run_level.csv", index=False)
    frame.to_json(OUT / "run_level.jsonl", orient="records", lines=True)
    frame.to_parquet(OUT / "run_level.parquet", index=False)

    copy(REVIEW / "attempt_audit.csv", OUT / "attempt_audit.csv")
    manifest_columns = [
        "planned_order", "scheduled_run_id", "task_id", "task_version",
        "pattern_family", "condition", "repeat_id", "n_attempts",
        "selected_attempt", "valid", "unavailable", "C", "S", "TC",
        "outcome", "termination_class",
    ]
    frame[manifest_columns].to_csv(OUT / "formal_run_manifest.csv", index=False)
    copy(ROOT / "LICENSE_DATA", OUT / "LICENSE_DATA")
    for name in SUMMARY_FILES:
        copy(REVIEW / name, OUT / "summaries" / name)
    copy(REVIEW / "data_integrity_audit.json", OUT / "audit" / "data_integrity_audit.json")
    audit_path = OUT / "audit" / "data_integrity_audit.json"
    audit_text = audit_path.read_text(encoding="utf-8")
    audit_text = audit_text.replace(str(ROOT) + "/", "repo://")
    audit_path.write_text(audit_text, encoding="utf-8")
    copy(FORMAL / "ADJUDICATION_NOTICE.md", OUT / "audit" / "ADJUDICATION_NOTICE.md")
    copy(MANUSCRIPT / "manuscript_number_provenance.csv", OUT / "audit" / "manuscript_number_provenance.csv")

    write_readme()
    write_dictionary(frame)
    write_croissant(frame)
    write_manifest(frame)
    print(f"Built {OUT} with {sum(1 for p in OUT.rglob('*') if p.is_file())} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
