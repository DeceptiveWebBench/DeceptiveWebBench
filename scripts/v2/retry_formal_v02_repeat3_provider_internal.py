"""Execute the one append-only retry for Repeat 3's provider internal error."""

from __future__ import annotations

import os

from src.utils.site_http_server import serve_project_root
from src.v2.formal_executor_v02 import make_formal_executor
from src.v2.formal_later_repeats_v02 import (
    ProviderInternalRetryRunner, formal_root, repeat_cells,
    set_authorization_status, sync_ledger, write_reports,
)

TARGET="v2__sneaking_trial_renewal_002__ui_warning__r3"


def main() -> int:
    if not os.environ.get("AWS_BEARER_TOKEN_BEDROCK"): raise SystemExit("Missing scoped Bedrock credential")
    cell=next(c for c in repeat_cells(3) if c.scheduled_run_id==TARGET)
    with serve_project_root() as base_url:
        base=make_formal_executor(base_url=base_url)
        def executor(c,attempt_id,clean_context_id):
            raw=base(c,attempt_id,clean_context_id); raw["adapter_status"]="QWEN_BEDROCK_CONVERSE_FORMAL_V02_108_MATRIX; append-only provider internal-error retry"; return raw
        result=ProviderInternalRetryRunner(target=cell,executor=executor,output_root=formal_root(3)/"runs").run([cell])[0]
    sync_ledger(3); summary=write_reports(3)
    attempts=result.get("attempts") or []
    if not attempts or attempts[-1].get("run_validity")!="valid":
        set_authorization_status(3,"technical_review_required"); raise SystemExit("Provider internal-error retry did not produce a valid result")
    set_authorization_status(3,"consumed")
    print(summary); return 0


if __name__=="__main__": raise SystemExit(main())
