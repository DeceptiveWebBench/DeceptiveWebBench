"""Run one newly author-authorized formal v0.2 repeat (2 or 3), serially."""

from __future__ import annotations

import argparse
import os

from src.utils.site_http_server import serve_project_root
from src.v2.formal_executor_v02 import make_formal_executor
from src.v2.formal_later_repeats_v02 import (
    EndpointRetryRunner, FormalLaterRepeatRunner, authorization_path,
    formal_root, load_authorization, prepare_formal_root, repeat_cells,
    selected_rows, set_authorization_status, sync_ledger, write_authorization,
    write_reports, _endpoint_outage,
)


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--repeat",type=int,choices=(2,3),required=True); parser.add_argument("--author-confirmed",action="store_true",required=True); args=parser.parse_args()
    if not args.author_confirmed: raise SystemExit("Explicit author confirmation is required")
    if not os.environ.get("AWS_BEARER_TOKEN_BEDROCK"): raise SystemExit("Missing scoped Bedrock credential")
    repeat_id=args.repeat; write_authorization(repeat_id); load_authorization(repeat_id); prepare_formal_root(repeat_id); set_authorization_status(repeat_id,"in_progress")
    # A non-retryable invalid cell is still a consumed scheduled cell.  Never
    # select it again merely because it has no valid outcome.
    existing={c.scheduled_run_id for c in repeat_cells(repeat_id) if (formal_root(repeat_id)/"runs"/c.scheduled_run_id).exists()}
    targets=[c for c in repeat_cells(repeat_id) if c.scheduled_run_id not in existing]
    try:
        with serve_project_root() as base_url:
            base_executor=make_formal_executor(base_url=base_url)
            def executor(cell,attempt_id,clean_context_id):
                raw=base_executor(cell,attempt_id,clean_context_id)
                raw["adapter_status"]="QWEN_BEDROCK_CONVERSE_FORMAL_V02_108_MATRIX; v0.2 delivery verified before action 1"
                return raw
            for index,cell in enumerate(targets,start=1):
                print(f"[{index}/{len(targets)}] {cell.scheduled_run_id} ({cell.safeguard_condition})",flush=True)
                runner=FormalLaterRepeatRunner(repeat_id=repeat_id,executor=executor,output_root=formal_root(repeat_id)/"runs")
                result=runner.run([cell])[0]; sync_ledger(repeat_id); write_reports(repeat_id)
                if result.get("operational_stop"):
                    set_authorization_status(repeat_id,"stopped_by_budget_guard"); raise SystemExit(f"Repeat {repeat_id} stopped before a call by the USD 8 budget guard")
                attempts=result.get("attempts") or []
                if attempts and attempts[-1].get("run_validity")=="valid": continue
                attempt1=formal_root(repeat_id)/"runs"/cell.scheduled_run_id/"attempt_1"
                if _endpoint_outage(attempt1):
                    retry=EndpointRetryRunner(target=cell,executor=executor,output_root=formal_root(repeat_id)/"runs")
                    retry_result=retry.run([cell])[0]; sync_ledger(repeat_id); write_reports(repeat_id)
                    retry_attempts=retry_result.get("attempts") or []
                    if retry_result.get("operational_stop"):
                        set_authorization_status(repeat_id,"stopped_by_budget_guard"); raise SystemExit(f"Repeat {repeat_id} endpoint retry stopped by budget guard")
                    if not retry_attempts or retry_attempts[-1].get("run_validity")!="valid":
                        set_authorization_status(repeat_id,"technical_review_required"); raise SystemExit(f"Technical gate failed for {cell.scheduled_run_id}")
                else:
                    print(f"Non-retryable invalid preserved for {cell.scheduled_run_id}; continuing schedule",flush=True)
        summary=write_reports(repeat_id)
        if summary["valid_cells"]<35:
            set_authorization_status(repeat_id,"technical_review_required"); raise SystemExit(f"Repeat {repeat_id} incomplete")
        set_authorization_status(repeat_id,"consumed"); print(summary); return 0
    except BaseException:
        write_reports(repeat_id); raise


if __name__=="__main__": raise SystemExit(main())
