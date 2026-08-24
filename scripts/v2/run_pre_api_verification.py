"""Run the complete model-free Protocol v2 verification and write a compact report."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from src.utils.io import project_root, write_json


def _tree_hash(roots: tuple[Path, ...]) -> tuple[str, int]:
    files = sorted(path for root in roots for path in root.rglob("*") if path.is_file())
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(project_root())).encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest(), len(files)


def main() -> int:
    root = project_root()
    started = time.monotonic()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root)
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests/v2", "-p", "test_*.py"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    combined = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"Ran (\d+) tests? in ([0-9.]+)s", combined)
    baseline = json.loads(
        (root / "artifacts/v2/review/protected_scope_baseline.json").read_text(encoding="utf-8")
    )
    protected_hash, protected_count = _tree_hash((root / "paper", root / "archive"))
    paper_hash = hashlib.sha256((root / "paper/neurips_2026.tex").read_bytes()).hexdigest()
    formal_root = root / "logs/v2/formal"
    formal_files = list(formal_root.rglob("*")) if formal_root.exists() else []
    dry_manifest = json.loads(
        (root / "artifacts/v2/pre_api_dry_run/manifest.json").read_text(encoding="utf-8")
    )
    report = {
        "status": "pass" if result.returncode == 0 else "fail",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "command": "PYTHONPATH=. python -m unittest discover -s tests/v2 -p test_*.py",
        "tests_run": int(match.group(1)) if match else None,
        "reported_test_seconds": float(match.group(2)) if match else None,
        "wall_seconds": round(time.monotonic() - started, 3),
        "exit_code": result.returncode,
        "browser_path_contract": {
            "tasks": 12,
            "paths_per_task": ["safe_completion", "unsafe_completion", "benchmark_stop"],
            "real_browser_paths": 36,
        },
        "protected_scope": {
            "paper_tex_unchanged": paper_hash == baseline["paper_neurips_2026_tex_sha256"],
            "paper_archive_tree_unchanged": (
                protected_hash == baseline["paper_and_archive_tree_sha256"]
                and protected_count == baseline["paper_and_archive_file_count"]
            ),
            "paper_tex_sha256": paper_hash,
            "paper_archive_tree_sha256": protected_hash,
            "paper_archive_file_count": protected_count,
        },
        "formal_run_files": sum(path.is_file() for path in formal_files),
        "model_or_paid_api_calls": int(dry_manifest["model_or_api_calls"]),
        "dry_run_cells": int(dry_manifest["valid_dry_run_records"]),
        "dry_run_attempts": int(dry_manifest["attempts"]),
        "output_tail": "\n".join(combined.strip().splitlines()[-12:]),
    }
    write_json(root / "artifacts/v2/review/pre_api_test_report.json", report)
    print(json.dumps(report, indent=2))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
