"""Create (if needed) a Hugging Face dataset repo and upload `dataset/hf_staging/`.

Requires authentication: set `HF_TOKEN` / `HUGGING_FACE_HUB_TOKEN`, or run `hf auth login`.
Org members need a token with write access to the organization.

Usage (from repo root):
  python dataset/build_hf_package.py
  python dataset/upload_to_hf.py
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from huggingface_hub import HfApi

DEFAULT_REPO_ID = "deceptive-web-benchmark/execution-time-warnings-web-agents"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--repo-id",
        default=DEFAULT_REPO_ID,
        help=f"Dataset repo id (default: {DEFAULT_REPO_ID})",
    )
    p.add_argument(
        "--folder",
        default=None,
        help="Staging folder (default: dataset/hf_staging under repo root)",
    )
    p.add_argument("--private", action="store_true", help="Create private dataset repo")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = (
        Path(args.folder).resolve()
        if args.folder
        else (root / "dataset" / "hf_staging").resolve()
    )
    if not folder.is_dir():
        print(f"Missing {folder}; run: python dataset/build_hf_package.py")
        return 1

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    api = HfApi(token=token) if token else HfApi()

    api.create_repo(
        repo_id=args.repo_id,
        repo_type="dataset",
        exist_ok=True,
        private=args.private,
    )
    api.upload_folder(
        folder_path=str(folder),
        repo_id=args.repo_id,
        repo_type="dataset",
        commit_message="Upload formal run-level results, summaries, and scrubbed raw JSON",
        allow_patterns=[
            "README.md",
            "croissant.json",
            "export_meta.json",
            "run_level.*",
            "run_manifest_v1.csv",
            "summaries/summary.md",
            "summaries/summary_by_condition.csv",
            "summaries/summary_system_vs_ui.csv",
            "summaries/task_by_condition.csv",
            "summaries/failure_decomposition.csv",
            "summaries/sensitivity_*.csv",
            "summaries/run_matrix_audit.csv",
            "raw_runs/**",
        ],
    )
    print(f"Uploaded -> https://huggingface.co/datasets/{args.repo_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
