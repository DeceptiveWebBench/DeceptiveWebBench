"""Capture verifiable non-model environment fields for the pre-API freeze candidate."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

from src.utils.io import project_root, write_json
from src.v2.artifacts import ARTIFACT_SCHEMA_VERSION
from src.v2.matrix import schedule_sha256
from src.v2.runtime_config import load_runtime_config


RELEVANT_ROOTS = (
    "src/v2",
    "scripts/v2",
    "tests/v2",
    "env/v2",
    "configs/v2",
    "analysis/v2_pipeline.py",
    "analysis/v2_precision.py",
    "analysis/v2_costs.py",
    "analysis/stats_plan.md",
    "docs/protocol_v2_consumer.md",
    "docs/consumer_task_redesign_spec_v2.md",
    "docs/outcome_cs_spec_v2.md",
    "docs/task_construction_protocol.md",
    "docs/experiment_matrix_v2.csv",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(project_root()).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def relevant_files() -> list[Path]:
    files: list[Path] = []
    for value in RELEVANT_ROOTS:
        path = project_root() / value
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(
                item
                for item in path.rglob("*")
                if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"
            )
    return sorted(set(files))


def package_snapshot() -> tuple[list[str], str]:
    packages = sorted(
        f"{dist.metadata['Name']}=={dist.version}"
        for dist in importlib.metadata.distributions()
        if dist.metadata.get("Name")
    )
    payload = "\n".join(packages).encode("utf-8")
    return packages, hashlib.sha256(payload).hexdigest()


def chrome_version() -> str:
    result = subprocess.run(
        ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def build() -> dict[str, object]:
    runtime = load_runtime_config()
    packages, packages_hash = package_snapshot()
    files = relevant_files()
    hashes = {
        "task_registry_sha256": sha256_file(project_root() / "configs/v2/task_registry.json"),
        "warning_config_sha256": sha256_file(project_root() / "configs/v2/warnings.yaml"),
        "scorer_sha256": sha256_file(project_root() / "src/v2/scorer.py"),
        "runner_sha256": sha256_file(project_root() / "src/v2/runner.py"),
        "runtime_config_sha256": sha256_file(project_root() / "configs/v2/runtime.yaml"),
        "pricing_config_sha256": sha256_file(project_root() / "configs/v2/pricing.yaml"),
        "artifact_contract_sha256": sha256_file(project_root() / "src/v2/artifacts.py"),
        "provider_adapter_sha256": sha256_file(project_root() / "src/v2/smoke_executor.py"),
        "matrix_sha256": schedule_sha256(),
        "static_websites_sha256": tree_hash(
            [path for path in (project_root() / "env/v2").rglob("*") if path.is_file()]
        ),
        "tool_definitions_sha256": tree_hash(
            [
                project_root() / "src/v2/execution_adapter.py",
                project_root() / "src/v2/termination_adapter.py",
            ]
        ),
        "requirements_sha256": sha256_file(project_root() / "requirements.txt"),
        "installed_environment_sha256": packages_hash,
        "working_tree_v2_snapshot_sha256": tree_hash(files),
    }
    report: dict[str, object] = {
        "status": "pre_api_freeze_candidate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "formal_authorization": False,
        "repository_commit": "UNRESOLVED_DIRTY_WORKTREE",
        "python": platform.python_version(),
        "browser_use": importlib.metadata.version("browser-use"),
        "playwright": importlib.metadata.version("playwright"),
        "chrome": chrome_version(),
        "viewport": {"width": 1280, "height": 720, "status": "verified_candidate"},
        "locale": "en-US",
        "browser_mode": "headless",
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "limits": {
            "max_steps": 30,
            "page_or_browser_action_timeout_seconds": 45,
            "llm_request_timeout_seconds": 120,
            "agent_step_timeout_seconds": 180,
            "wall_clock_timeout_seconds": 900,
        },
        "hashes": hashes,
        "installed_packages": packages,
        "frozen_model_fields": {
            "provider": runtime.model["provider"],
            "family": runtime.model["intended_model_family"],
            "documented_model_identifier": runtime.model["documented_model_identifier"],
            "region": runtime.model["endpoint_region"],
            "temperature": runtime.sampling["temperature"],
            "top_p": runtime.sampling["top_p"],
            "max_output_tokens": runtime.sampling["max_output_tokens"],
            "thinking_mode": runtime.sampling["thinking_mode"],
            "effort": runtime.sampling["effort"],
        },
        "requires_first_api_smoke_confirmation": [
            "Bedrock model access and any required inference-profile resolution",
            "provider usage fields returned for the selected endpoint",
            "BrowserUse structured done/ask_user event mapping",
            "actual latency and task-level cost distribution",
        ],
        "requires_author_before_formal": [
            "formal budget derived from smoke evidence",
            "explicit formal authorization",
            "repository commit identifier for final freeze",
        ],
    }
    write_json(project_root() / "artifacts/v2/review/non_model_freeze_candidate.json", report)
    return report


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
