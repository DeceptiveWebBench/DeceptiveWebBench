"""Build Hugging Face staging package under dataset/hf_staging/.

Includes:
  - run_level tabular export (csv/jsonl/parquet)
  - dataset card (README.md)
  - frozen analysis summaries
  - scrubbed per-run JSON for formal shoplane + enterprise runs
  - croissant metadata (URLs rewritten to the public dataset id)
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
STAGING = _REPO_ROOT / "dataset" / "hf_staging"
HF_REPO_ID = "deceptive-web-benchmark/execution-time-warnings-web-agents"
ABS_PATH_RE = re.compile(r"[A-Za-z]:\\[^\n\"']+|/(?:Users|home)/[^\n\"']+")


def _scrub_obj(obj: object) -> object:
    if isinstance(obj, dict):
        out: dict = {}
        for key, value in obj.items():
            if key in {"artifacts_dir", "artifacts_path", "log_dir", "run_dir"} and isinstance(value, str):
                # Keep only the run folder name, drop absolute host paths.
                out[key] = Path(value.replace("\\", "/")).name
            else:
                out[key] = _scrub_obj(value)
        return out
    if isinstance(obj, list):
        return [_scrub_obj(x) for x in obj]
    if isinstance(obj, str):
        if ABS_PATH_RE.search(obj):
            # Replace absolute path prefixes with a placeholder when they appear inline.
            return ABS_PATH_RE.sub("<REDACTED_LOCAL_PATH>", obj)
        return obj
    return obj


def _copy_summaries() -> None:
    src = _REPO_ROOT / "analysis" / "outputs"
    dst = STAGING / "summaries"
    dst.mkdir(parents=True, exist_ok=True)
    for name in (
        "summary.md",
        "summary_by_condition.csv",
        "summary_system_vs_ui.csv",
        "task_by_condition.csv",
        "failure_decomposition.csv",
        "sensitivity_without_interface_perm_001.csv",
        "sensitivity_system_vs_ui_without_interface_perm_001.csv",
        "run_matrix_audit.csv",
    ):
        path = src / name
        if path.exists():
            shutil.copy2(path, dst / name)
    manifest = src / "run_manifest_v1.csv"
    if manifest.exists():
        shutil.copy2(manifest, STAGING / manifest.name)


def _copy_raw_runs() -> None:
    root = _REPO_ROOT / "logs" / "formal_runs"
    keep_files = ("terminal_state.json", "final_result.json", "run_metadata.json")
    for split in ("shoplane", "enterprise"):
        split_dir = root / split
        if not split_dir.is_dir():
            continue
        for run_dir in sorted(p for p in split_dir.iterdir() if p.is_dir()):
            out = STAGING / "raw_runs" / split / run_dir.name
            out.mkdir(parents=True, exist_ok=True)
            for fname in keep_files:
                src = run_dir / fname
                if not src.exists():
                    continue
                if fname == "run_metadata.json":
                    data = json.loads(src.read_text(encoding="utf-8"))
                    scrubbed = _scrub_obj(data)
                    (out / fname).write_text(
                        json.dumps(scrubbed, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )
                else:
                    # Light scrub for any absolute paths embedded in JSON text.
                    text = src.read_text(encoding="utf-8")
                    try:
                        data = json.loads(text)
                        text = json.dumps(_scrub_obj(data), indent=2, ensure_ascii=False) + "\n"
                    except json.JSONDecodeError:
                        text = ABS_PATH_RE.sub("<REDACTED_LOCAL_PATH>", text)
                    (out / fname).write_text(text, encoding="utf-8")


def _copy_card_and_croissant() -> None:
    shutil.copy2(_REPO_ROOT / "dataset" / "README.md", STAGING / "README.md")
    src = _REPO_ROOT / "dataset" / "metadata" / "croissant.json"
    if not src.exists():
        return
    text = src.read_text(encoding="utf-8")
    text = text.replace(
        "deceptive-web/deception-warning-study-runs",
        HF_REPO_ID,
    )
    (STAGING / "croissant.json").write_text(text, encoding="utf-8")


def main() -> int:
    import sys

    sys.path.insert(0, str(_REPO_ROOT))
    from dataset.export_staging import main as export_tabular  # noqa: WPS433

    STAGING.mkdir(parents=True, exist_ok=True)
    # Refresh tabular artifacts into hf_staging.
    rc = export_tabular()
    if rc != 0:
        return rc
    _copy_summaries()
    _copy_raw_runs()
    _copy_card_and_croissant()
    n_runs = sum(1 for _ in (STAGING / "raw_runs").rglob("run_metadata.json")) if (STAGING / "raw_runs").exists() else 0
    print(f"Staging ready at {STAGING}")
    print(f"Scrubbed raw run folders with metadata: {n_runs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
