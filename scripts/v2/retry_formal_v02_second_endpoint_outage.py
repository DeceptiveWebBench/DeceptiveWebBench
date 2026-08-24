from __future__ import annotations

import os
import yaml

from src.utils.site_http_server import serve_project_root
from src.v2.formal_amendment_v02_second_outage import SecondEndpointRetryRunner, create_adjudication, target_cell
from src.v2.formal_executor_v02 import make_formal_executor
from src.v2.formal_repeat1_v02 import AUTHORIZATION_PATH, FORMAL_ROOT, sync_ledger, write_reports


def main():
    if not os.environ.get("AWS_BEARER_TOKEN_BEDROCK"): raise SystemExit("Missing scoped Bedrock credential")
    create_adjudication()
    with serve_project_root() as base_url:
        result=SecondEndpointRetryRunner(executor=make_formal_executor(base_url=base_url),output_root=FORMAL_ROOT/"runs",external_retry_reason="model_service_unavailable").run([target_cell()])[0]
    sync_ledger(); summary=write_reports(); attempts=result.get("attempts") or []
    if not attempts or attempts[-1].get("run_validity") != "valid": raise SystemExit("Second endpoint retry invalid")
    auth=yaml.safe_load(AUTHORIZATION_PATH.read_text()) or {}; auth["status"]="in_progress"; AUTHORIZATION_PATH.write_text(yaml.safe_dump(auth,sort_keys=False))
    print(summary); return 0


if __name__ == "__main__": raise SystemExit(main())
