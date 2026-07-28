from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from urllib.parse import urlencode

from scripts.smoke_browseruse.agent import SmokeTestWebAgent
from src.utils.io import ensure_dir, load_main_config, project_root, utc_timestamp, write_json
from src.utils.model_profile import resolve_model_profile
from src.utils.site_http_server import serve_project_root


def build_smoke_test_url(site_base_url: str) -> str:
    # Canonical runtime path: unified shopping site under env/site (served over HTTP for BrowserUse).
    query = urlencode({"task": "interface_perm_001", "condition": "no_warning", "new_run": "1"})
    base = site_base_url.rstrip("/")
    return f"{base}/env/site/permission_confirm.html?{query}"


def build_run_metadata(config: dict, run_dir: Path, page_url: str) -> dict:
    profile_name, resolved_model = resolve_model_profile(config)
    return {
        "run_id": run_dir.name,
        "task_id": "smoke_test",
        "task": f"Open {page_url} and click the Decline button.",
        "page_url": page_url,
        "artifacts_dir": str(run_dir),
        "model_profile": profile_name,
        "model_access_path": resolved_model.get("access_path"),
        "agent_framework": config.get("agent", {}).get("framework"),
        "model_provider": resolved_model.get("provider"),
        "model_name": resolved_model.get("model_name"),
        "browser_mode": config.get("browser", {}).get("mode_main"),
        "max_steps": config.get("execution", {}).get("max_steps"),
    }


async def main() -> int:
    config = load_main_config()
    run_id = f"smoke_test_{utc_timestamp()}"
    run_dir = ensure_dir(project_root() / "logs" / "smoke_test" / run_id)

    with serve_project_root(project_root()) as site_base_url:
        page_url = build_smoke_test_url(site_base_url)

        metadata = build_run_metadata(config, run_dir, page_url)
        write_json(run_dir / "run_metadata.json", metadata)

        agent = SmokeTestWebAgent(config=config, artifacts_dir=run_dir)

        try:
            result = await agent.run(page_url=page_url)
        except Exception as exc:
            error_payload = {
                "status": "error",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }
            write_json(run_dir / "final_result.json", error_payload)
            raise

        final_payload = {
            "status": "completed",
            "success": result.get("success", False),
            "result": result,
        }
        write_json(run_dir / "final_result.json", final_payload)
        print(f"Smoke test artifacts saved to: {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

