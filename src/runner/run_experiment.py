from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import yaml

from scripts.smoke_browseruse.agent import SmokeTestWebAgent
from src.utils.io import ensure_dir, load_main_config, project_root, utc_timestamp, write_json
from src.utils.model_profile import resolve_model_profile
from src.utils.config_contract import collect_contract_issues
from src.utils.site_http_server import serve_project_root


def load_manifest(manifest_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(manifest_path) if manifest_path else project_root() / "configs" / "experiment_manifest.yaml"
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def build_canonical_url(start_page: str, task_id: str, condition: str, *, site_base_url: str) -> str:
    """HTTP site URL under a local static server (project root); required for BrowserUse."""
    query = urlencode({"task": task_id, "condition": condition, "new_run": "1"})
    base = site_base_url.rstrip("/")
    return f"{base}/env/site/{start_page}.html?{query}"


def build_run_id(task_id: str, condition: str, repeat_idx: int) -> str:
    return f"{task_id}__{condition}__r{repeat_idx:02d}__{utc_timestamp()}"


def iter_run_plan(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = list(manifest.get("tasks") or [])
    conditions = list(manifest.get("conditions") or [])
    repeats = int(manifest.get("repeats_per_task_condition") or 1)
    explicit = manifest.get("repeat_indices")
    if explicit is not None:
        repeat_iter = [int(x) for x in list(explicit)]
    else:
        repeat_iter = list(range(1, repeats + 1))

    run_plan: list[dict[str, Any]] = []
    for task in tasks:
        task_id = str(task["task_id"])
        pattern_family = str(task["pattern_family"])
        start_page = str(task["start_page"])
        for condition in conditions:
            condition_label = str(condition)
            for repeat_idx in repeat_iter:
                if repeat_idx < 1 or repeat_idx > repeats:
                    raise ValueError(
                        f"repeat_indices must be within 1..repeats_per_task_condition ({repeats}); got {repeat_idx}"
                    )
                run_plan.append(
                    {
                        "task_id": task_id,
                        "pattern_family": pattern_family,
                        "start_page": start_page,
                        "condition": condition_label,
                        "repeat_idx": repeat_idx,
                    }
                )
    return run_plan


def build_run_metadata(
    main_config: dict[str, Any],
    manifest: dict[str, Any],
    run_id: str,
    run_dir: Path,
    run_item: dict[str, Any],
    page_url: str,
) -> dict[str, Any]:
    profile_name, resolved_model = resolve_model_profile(main_config)
    return {
        "run_id": run_id,
        "benchmark_version": manifest.get("benchmark_version"),
        "task_id": run_item["task_id"],
        "pattern_family": run_item["pattern_family"],
        "start_page": run_item["start_page"],
        "condition": run_item["condition"],
        "repeat_idx": run_item["repeat_idx"],
        "page_url": page_url,
        "artifacts_dir": str(run_dir),
        "task_goal_source": f"env/tasks/{run_item['task_id']}/task.yaml:user_goal",
        "system_warning_source": "configs/warnings.yaml:rendered_text",
        "model_profile": profile_name,
        "model_access_path": resolved_model.get("access_path"),
        "agent_framework": main_config.get("agent", {}).get("framework"),
        "model_provider": resolved_model.get("provider"),
        "model_name": resolved_model.get("model_name"),
        "browser_mode": main_config.get("browser", {}).get("mode_main"),
        "max_steps": main_config.get("execution", {}).get("max_steps"),
    }


async def run_once(
    agent: SmokeTestWebAgent,
    run_dir: Path,
    run_metadata: dict[str, Any],
    page_url: str,
) -> dict[str, Any]:
    write_json(run_dir / "run_metadata.json", run_metadata)
    try:
        result = await agent.run(page_url=page_url)
        payload = {
            "status": "completed",
            "success": result.get("success", False),
            "result": result,
        }
    except Exception as exc:
        payload = {
            "status": "error",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }
    write_json(run_dir / "final_result.json", payload)
    return payload


async def main(manifest_path: str | Path | None = None) -> int:
    main_config = load_main_config()
    issues = collect_contract_issues()
    if issues:
        for issue in issues:
            print(f"[CONFIG_CONTRACT_ERROR] [{issue.task_id}] {issue.message}")
        return 2

    manifest = load_manifest(manifest_path)
    run_plan = iter_run_plan(manifest)

    output_root_raw = str(manifest.get("output_root") or "logs/experiment_runs")
    output_root = ensure_dir(project_root() / output_root_raw)

    print(f"Loaded run plan items: {len(run_plan)}")
    print(f"Output root: {output_root}")

    with serve_project_root(project_root()) as site_base_url:
        print(f"Local site server: {site_base_url}")
        for run_item in run_plan:
            run_id = build_run_id(run_item["task_id"], run_item["condition"], int(run_item["repeat_idx"]))
            run_dir = ensure_dir(output_root / run_id)
            page_url = build_canonical_url(
                start_page=str(run_item["start_page"]),
                task_id=str(run_item["task_id"]),
                condition=str(run_item["condition"]),
                site_base_url=site_base_url,
            )

            run_metadata = build_run_metadata(
                main_config=main_config,
                manifest=manifest,
                run_id=run_id,
                run_dir=run_dir,
                run_item=run_item,
                page_url=page_url,
            )
            agent = SmokeTestWebAgent(config=main_config, artifacts_dir=run_dir)
            payload = await run_once(agent=agent, run_dir=run_dir, run_metadata=run_metadata, page_url=page_url)
            print(f"[{run_id}] {payload['status']}")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run minimal formal experiment task x condition x repeat.")
    parser.add_argument(
        "--manifest",
        default=None,
        help="Optional path to experiment manifest YAML (default: configs/experiment_manifest.yaml).",
    )
    args = parser.parse_args()
    sys.exit(asyncio.run(main(manifest_path=args.manifest)))

