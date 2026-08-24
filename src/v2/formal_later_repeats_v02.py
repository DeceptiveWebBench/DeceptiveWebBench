"""Scoped, append-only execution contract for formal v0.2 repeats 2 and 3.

This module was added after Repeat 1.  It does not alter any frozen experimental
component; it only applies new author-scoped tranche guards to the remaining
canonical schedule cells.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

import src.v2.runner as runner_module
from src.utils.io import project_root, write_json
from src.v2.artifacts import read_json, validate_attempt_directory
from src.v2.costs import reconstructed_or_authoritative_cost
from src.v2.formal_repeat1_v02 import frozen_hashes, render_payload_bytes
from src.v2.matrix import ScheduledCell, load_schedule, schedule_sha256
from src.v2.runner import FormalRunGuardError, ProtocolV2Runner
from src.v2.safeguards_v02 import WARNING_VERSION, warning_config_path, warning_version
from src.v2.scorer import score_attempt


HARD_BUDGET_USD = 8.0
CONDITIONS = ("no_warning", "system_warning", "ui_warning")
OUTCOMES = ("trustworthy_completion", "unsafe_completion", "safe_non_completion", "unsafe_failure")
FORMAL_BASE = project_root() / "logs/v2/formal/protocol-v2-generic-safeguard-v0.2"
AUTH_BASE = project_root() / "configs/v2"
ENDPOINT_ERROR = 'Could not connect to the endpoint URL: "https://bedrock-runtime.us-east-1.amazonaws.com/model/qwen.qwen3-vl-235b-a22b/converse"'
PROVIDER_INTERNAL_ERROR = "The system encountered an unexpected error during processing. Try your request again."


def formal_root(repeat_id: int) -> Path:
    _check_repeat(repeat_id)
    return FORMAL_BASE / f"repeat_{repeat_id}"


def authorization_path(repeat_id: int) -> Path:
    _check_repeat(repeat_id)
    return AUTH_BASE / f"formal_v02_repeat{repeat_id}_authorization.yaml"


def collection_id(repeat_id: int) -> str:
    return f"protocol-v2-generic-safeguard-v0.2-repeat-{repeat_id}"


def collection_scope(repeat_id: int) -> str:
    return f"formal_v02_repeat{repeat_id}"


def _check_repeat(repeat_id: int) -> None:
    if repeat_id not in (2, 3):
        raise FormalRunGuardError("Later-repeat contract accepts only repeat 2 or 3")


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def repeat_cells(repeat_id: int) -> tuple[ScheduledCell, ...]:
    _check_repeat(repeat_id)
    cells = tuple(sorted((c for c in load_schedule() if c.repeat_id == repeat_id), key=lambda c: c.planned_order))
    if len(cells) != 36 or len({(c.task_id, c.safeguard_condition) for c in cells}) != 36:
        raise FormalRunGuardError(f"Repeat {repeat_id} is not a complete unique 36-cell tranche")
    if Counter(c.safeguard_condition for c in cells) != Counter({c: 12 for c in CONDITIONS}):
        raise FormalRunGuardError(f"Repeat {repeat_id} condition balance mismatch")
    return cells


def tranche_hash(repeat_id: int) -> str:
    return _canonical_hash([asdict(c) for c in repeat_cells(repeat_id)])


def authorization_template(repeat_id: int) -> dict[str, Any]:
    return {
        "authorization_version": "formal-v02-later-repeat-authorization-1.0",
        "status": "authorized_pending_execution",
        "authorized": True,
        "author_confirmation": "Explicit user instruction in Codex task on 2026-08-22 to run Repeat 2 and Repeat 3",
        "safeguard_version": WARNING_VERSION,
        "collection_id": collection_id(repeat_id),
        "repeat_ids": [repeat_id],
        "authorized_scheduled_run_ids": [c.scheduled_run_id for c in repeat_cells(repeat_id)],
        "authorized_cell_count": 36,
        "canonical_matrix_sha256": schedule_sha256(),
        "tranche_sha256": tranche_hash(repeat_id),
        "provider": "aws_bedrock",
        "model": "qwen.qwen3-vl-235b-a22b",
        "region": "us-east-1",
        "concurrency": 1,
        "hard_new_cost_limit_usd": HARD_BUDGET_USD,
        "authorized_repeat": repeat_id,
        "other_repeats_authorized_by_this_record": False,
        "formal_authorization_base_manifest_unchanged": True,
    }


def write_authorization(repeat_id: int) -> None:
    path = authorization_path(repeat_id)
    expected = authorization_template(repeat_id)
    if path.exists():
        old = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if old.get("status") == "consumed":
            raise FormalRunGuardError(f"Repeat {repeat_id} authorization is already consumed")
        for key, value in expected.items():
            if key != "status" and old.get(key) != value:
                raise FormalRunGuardError(f"Existing Repeat {repeat_id} authorization mismatch: {key}")
        return
    path.write_text(yaml.safe_dump(expected, sort_keys=False), encoding="utf-8")


def set_authorization_status(repeat_id: int, status: str) -> None:
    path = authorization_path(repeat_id)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw["status"] = status
    if status == "consumed":
        raw["consumed_after_valid_cells"] = 36
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")


def load_authorization(repeat_id: int) -> dict[str, Any]:
    raw = yaml.safe_load(authorization_path(repeat_id).read_text(encoding="utf-8")) or {}
    expected = authorization_template(repeat_id)
    for key, value in expected.items():
        if key != "status" and raw.get(key) != value:
            raise FormalRunGuardError(f"Scoped authorization mismatch: {key}")
    if raw.get("status") not in {"authorized_pending_execution", "in_progress"}:
        raise FormalRunGuardError(f"Repeat {repeat_id} authorization is not active")
    return raw


def verify_repeat1_freeze() -> None:
    manifest = read_json(FORMAL_BASE / "repeat_1/formal_manifest.json")
    if frozen_hashes() != manifest.get("frozen_hashes"):
        raise FormalRunGuardError("Frozen v0.2 experimental component hash mismatch")


def prepare_formal_root(repeat_id: int) -> None:
    verify_repeat1_freeze()
    root = formal_root(repeat_id)
    root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "manifest_version": "formal-v02-later-repeat-manifest-1.0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "collection_id": collection_id(repeat_id),
        "formal_run": True,
        "repeat_id": repeat_id,
        "safeguard_version": WARNING_VERSION,
        "payload_sha256": hashlib.sha256(render_payload_bytes()).hexdigest(),
        "matrix_sha256": schedule_sha256(),
        "tranche_sha256": tranche_hash(repeat_id),
        "cells": [asdict(c) for c in repeat_cells(repeat_id)],
        "frozen_hashes": frozen_hashes(),
        "pre_registered_endpoint_outage_policy": {
            "structured_error": ENDPOINT_ERROR,
            "requires_zero_completed_model_calls": True,
            "maximum_additional_attempts": 1,
            "original_attempt_preserved": True,
        },
    }
    path = root / "formal_manifest.json"
    if path.exists():
        old = read_json(path)
        for key in ("collection_id", "repeat_id", "safeguard_version", "payload_sha256", "matrix_sha256", "tranche_sha256", "cells", "frozen_hashes"):
            if old.get(key) != manifest[key]:
                raise FormalRunGuardError(f"Formal manifest freeze mismatch: {key}")
    else:
        write_json(path, manifest)
    (root / "cost_ledger.jsonl").touch(exist_ok=True)


def _assert_cell_authorized(repeat_id: int, cell: ScheduledCell) -> None:
    auth = load_authorization(repeat_id)
    if cell.repeat_id != repeat_id or cell.scheduled_run_id not in auth["authorized_scheduled_run_ids"]:
        raise FormalRunGuardError("Cell is outside the scoped repeat authorization")
    if (formal_root(repeat_id) / "runs" / cell.scheduled_run_id).exists():
        raise FormalRunGuardError("A formal attempt already exists for this scheduled cell")


class FormalLaterRepeatRunner(ProtocolV2Runner):
    def __init__(self, *, repeat_id: int, **kwargs: Any):
        self.repeat_id = repeat_id
        super().__init__(formal_run=False, smoke_api_run=True, explicit_smoke_authorization=True,
                         collection_scope=collection_scope(repeat_id), collection_id=collection_id(repeat_id),
                         budget_limit_usd=HARD_BUDGET_USD, **kwargs)
        self.formal_run = True

    def _run_cell(self, cell: ScheduledCell) -> dict[str, Any]:
        _assert_cell_authorized(self.repeat_id, cell)
        return super()._run_cell(cell)

    def _write_attempt(self, *args: Any, **kwargs: Any) -> None:
        old_version, old_path = runner_module.warning_version, runner_module.warning_config_path
        try:
            runner_module.warning_version, runner_module.warning_config_path = warning_version, warning_config_path
            super()._write_attempt(*args, **kwargs)
        finally:
            runner_module.warning_version, runner_module.warning_config_path = old_version, old_path


def attempt_dirs(repeat_id: int) -> list[Path]:
    path = formal_root(repeat_id) / "runs"
    return sorted(path.glob("*/attempt_*")) if path.exists() else []


def _endpoint_outage(path: Path) -> bool:
    raw, usage = read_json(path / "raw_state.json"), read_json(path / "usage_cost.json")
    errors = [str(result.get("error") or "") for action in raw.get("actions") or [] for result in action.get("result") or [] if result.get("error")]
    return errors == [ENDPOINT_ERROR] and int(usage.get("trajectory_totals", {}).get("model_calls") or 0) == 0 and not raw.get("agent_model_call")


def create_endpoint_amendment(repeat_id: int, cell: ScheduledCell, attempt: Path) -> dict[str, Any]:
    if attempt.name != "attempt_1" or not _endpoint_outage(attempt):
        raise FormalRunGuardError("Attempt does not meet the pre-registered endpoint-outage retry contract")
    amendment = {
        "amendment_id": f"formal-v02-repeat{repeat_id}-endpoint-outage-{cell.scheduled_run_id}",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scheduled_run_id": cell.scheduled_run_id,
        "attempt_id": 1,
        "original_artifacts_unchanged": True,
        "original_hashes": {name: hashlib.sha256((attempt / name).read_bytes()).hexdigest() for name in ("run_metadata.json", "raw_state.json", "scored_outcome.json", "usage_cost.json")},
        "structured_error": ENDPOINT_ERROR,
        "adjudicated_infrastructure_class": "model_service_unavailable",
        "maximum_additional_attempts": 1,
        "semantic_or_scorer_change": False,
    }
    directory = formal_root(repeat_id) / "amendments"; directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{amendment['amendment_id']}.json"
    if target.exists():
        old = read_json(target)
        if old.get("original_hashes") != amendment["original_hashes"]:
            raise FormalRunGuardError("Existing endpoint amendment hash mismatch")
        return old
    write_json(target, amendment)
    return amendment


class EndpointRetryRunner(FormalLaterRepeatRunner):
    def __init__(self, *, target: ScheduledCell, **kwargs: Any):
        self.target = target
        super().__init__(repeat_id=target.repeat_id, external_retry_reason="model_service_unavailable", **kwargs)

    def _run_cell(self, cell: ScheduledCell) -> dict[str, Any]:
        if cell.scheduled_run_id != self.target.scheduled_run_id:
            raise FormalRunGuardError("Endpoint retry runner is scoped to one cell")
        create_endpoint_amendment(cell.repeat_id, cell, formal_root(cell.repeat_id) / "runs" / cell.scheduled_run_id / "attempt_1")
        self.formal_run = False
        try:
            return ProtocolV2Runner._run_cell(self, cell)
        finally:
            self.formal_run = True

    def _write_attempt(self, cell, attempt_id, raw, scored, usage_cost, screenshot_payloads):
        if attempt_id != 2:
            raise FormalRunGuardError("Endpoint amendment permits only attempt 2")
        raw["formal_run"] = True
        old = self.formal_run; self.formal_run = True
        try:
            return FormalLaterRepeatRunner._write_attempt(self, cell, attempt_id, raw, scored, usage_cost, screenshot_payloads)
        finally:
            self.formal_run = old


def _provider_internal_error(path: Path) -> bool:
    raw=read_json(path/"raw_state.json"); scored=read_json(path/"scored_outcome.json")
    errors=[str(result.get("error") or "") for action in raw.get("actions") or [] for result in action.get("result") or [] if result.get("error")]
    return (errors==[PROVIDER_INTERNAL_ERROR] and scored.get("run_validity")=="configuration_contract_failure"
            and not raw.get("unsafe_boundary_crossed") and not raw.get("nominal_endpoint_reached"))


def create_provider_internal_amendment(repeat_id: int, cell: ScheduledCell, attempt: Path) -> dict[str, Any]:
    if attempt.name!="attempt_1" or not _provider_internal_error(attempt):
        raise FormalRunGuardError("Attempt does not meet provider-internal-error retry contract")
    amendment={
        "amendment_id":f"formal-v02-repeat{repeat_id}-provider-internal-error-{cell.scheduled_run_id}",
        "created_at_utc":datetime.now(timezone.utc).isoformat(),"scheduled_run_id":cell.scheduled_run_id,"attempt_id":1,
        "original_artifacts_unchanged":True,
        "original_hashes":{name:hashlib.sha256((attempt/name).read_bytes()).hexdigest() for name in ("run_metadata.json","raw_state.json","scored_outcome.json","usage_cost.json")},
        "structured_error":PROVIDER_INTERNAL_ERROR,"adjudicated_infrastructure_class":"model_service_unavailable",
        "unsafe_boundary_crossed_before_error":False,"behavioral_outcome_available":False,
        "maximum_additional_attempts":1,"semantic_or_scorer_change":False,
    }
    directory=formal_root(repeat_id)/"amendments"; directory.mkdir(parents=True,exist_ok=True)
    target=directory/f"{amendment['amendment_id']}.json"
    if target.exists():
        old=read_json(target)
        if old.get("original_hashes")!=amendment["original_hashes"]: raise FormalRunGuardError("Existing provider amendment hash mismatch")
        return old
    write_json(target,amendment); return amendment


class ProviderInternalRetryRunner(FormalLaterRepeatRunner):
    def __init__(self, *, target: ScheduledCell, **kwargs: Any):
        self.target=target
        super().__init__(repeat_id=target.repeat_id,external_retry_reason="model_service_unavailable",**kwargs)

    def _run_cell(self, cell: ScheduledCell) -> dict[str, Any]:
        if cell.scheduled_run_id!=self.target.scheduled_run_id: raise FormalRunGuardError("Provider retry runner is scoped to one cell")
        create_provider_internal_amendment(cell.repeat_id,cell,formal_root(cell.repeat_id)/"runs"/cell.scheduled_run_id/"attempt_1")
        self.formal_run=False
        try: return ProtocolV2Runner._run_cell(self,cell)
        finally: self.formal_run=True

    def _write_attempt(self, cell, attempt_id, raw, scored, usage_cost, screenshot_payloads):
        if attempt_id!=2: raise FormalRunGuardError("Provider amendment permits only attempt 2")
        raw["formal_run"]=True; old=self.formal_run; self.formal_run=True
        try: return FormalLaterRepeatRunner._write_attempt(self,cell,attempt_id,raw,scored,usage_cost,screenshot_payloads)
        finally: self.formal_run=old


def sync_ledger(repeat_id: int) -> None:
    lines=[]; cumulative=0.0; unknown=0
    for path in attempt_dirs(repeat_id):
        metadata, usage = read_json(path / "run_metadata.json"), read_json(path / "usage_cost.json")
        value = reconstructed_or_authoritative_cost(usage)
        if value is None: unknown += 1
        else: cumulative += value
        lines.append(json.dumps({"run_id":metadata["run_id"],"scheduled_run_id":metadata["scheduled_run_id"],"attempt_id":metadata["attempt_id"],"known_cost_usd":value,"cumulative_known_cost_usd":cumulative,"unknown_cost_attempts":unknown,"conservative_exposure_usd":cumulative+unknown},sort_keys=True))
    (formal_root(repeat_id) / "cost_ledger.jsonl").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def selected_rows(repeat_id: int) -> list[dict[str, Any]]:
    rows=[]
    for cell in repeat_cells(repeat_id):
        selected=None
        for path in sorted((formal_root(repeat_id)/"runs"/cell.scheduled_run_id).glob("attempt_*"), reverse=True):
            score=read_json(path/"scored_outcome.json")
            if score.get("run_validity") == "valid": selected=(path,score); break
        rows.append({"planned_order":cell.planned_order,"scheduled_run_id":cell.scheduled_run_id,"task_id":cell.task_id,"condition":cell.safeguard_condition,"repeat_id":repeat_id,"status":"valid" if selected else "not_run","C":None if not selected else selected[1]["C_r"],"S":None if not selected else selected[1]["S_r"],"outcome":None if not selected else selected[1]["outcome_label"],"termination_class":None if not selected else selected[1].get("termination_class"),"selected_attempt":None if not selected else selected[0].name})
    return rows


def write_reports(repeat_id: int) -> dict[str, Any]:
    root=formal_root(repeat_id); rows=selected_rows(repeat_id)
    with (root/"cell_results.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    valid=[r for r in rows if r["status"]=="valid"]
    counts={c:Counter(r["outcome"] for r in valid if r["condition"]==c) for c in CONDITIONS}
    known=0.0; unknown=0; calls=0; tokens=0; unexplained=[]; invalid=[]
    amendments={a["scheduled_run_id"]:a for p in (root/"amendments").glob("*.json") for a in [read_json(p)]} if (root/"amendments").exists() else {}
    for path in attempt_dirs(repeat_id):
        cell=next(c for c in repeat_cells(repeat_id) if c.scheduled_run_id==path.parent.name)
        try:
            validate_attempt_directory(path,cell=cell)
            metadata=read_json(path/"run_metadata.json")
            if metadata.get("safeguard_version") != WARNING_VERSION: raise ValueError("safeguard version mismatch")
            if metadata.get("safeguard_config_sha256") != hashlib.sha256(warning_config_path().read_bytes()).hexdigest(): raise ValueError("warning hash mismatch")
            if metadata.get("collection_scope") != collection_scope(repeat_id) or metadata.get("collection_id") != collection_id(repeat_id): raise ValueError("collection mismatch")
            if metadata.get("repeat_id") != repeat_id or not metadata.get("formal_run"): raise ValueError("repeat/formal metadata mismatch")
            if metadata.get("prompt_capture",{}).get("safeguard_version") != WARNING_VERSION: raise ValueError("prompt safeguard version missing")
        except Exception as exc:
            if not (_endpoint_outage(path) and cell.scheduled_run_id in amendments): unexplained.append({"path":str(path),"error":str(exc)})
        raw,saved=read_json(path/"raw_state.json"),read_json(path/"scored_outcome.json"); recomputed=score_attempt(raw).to_dict()
        fields=("C_r","S_r","outcome_label","run_validity","termination_class","termination_reason","scheduled_run_id","attempt_id","raw_events")
        if any(saved.get(k)!=recomputed.get(k) for k in fields): unexplained.append({"path":str(path),"error":"scorer recomputation mismatch"})
        if saved.get("run_validity")!="valid": invalid.append({"scheduled_run_id":cell.scheduled_run_id,"attempt":path.name,"reason":saved.get("run_validity")})
        usage=read_json(path/"usage_cost.json"); value=reconstructed_or_authoritative_cost(usage)
        if value is None: unknown+=1
        else: known+=value
        calls+=int(usage.get("trajectory_totals",{}).get("model_calls") or 0); tokens+=int(usage.get("trajectory_totals",{}).get("total_tokens") or 0)
    by_condition={c:sum(1 for r in valid if r["condition"]==c) for c in CONDITIONS}
    traversed=sum(1 for cell in repeat_cells(repeat_id) if (root/"runs"/cell.scheduled_run_id).exists())==36
    technical=len(valid)>=35 and all(by_condition[c]>=11 for c in CONDITIONS) and not unexplained and traversed
    if technical and len(valid)==36:
        status=f"REPEAT_{repeat_id}_TECHNICALLY_COMPLETE"
    elif technical:
        status=f"REPEAT_{repeat_id}_TECHNICALLY_COMPLETE_WITH_NONRETRYABLE_INVALID"
    else:
        status=f"REPEAT_{repeat_id}_TECHNICAL_REVIEW_REQUIRED"
    labels={"no_warning":"No safeguard","system_warning":"System-delivered safeguard","ui_warning":"Interface-delivered safeguard"}
    report=[f"# Formal v0.2 Repeat {repeat_id} report","",f"Status: `{status}`","","This is one frozen 36-cell repeat. It is reported descriptively and is not analyzed alone as the complete experiment.","","| Delivery | Trustworthy | Unsafe completion | Safe non-completion | Unsafe failure | n | C rate | S rate |","|---|---:|---:|---:|---:|---:|---:|---:|"]
    for c in CONDITIONS:
        x=counts[c]; n=sum(x.values()); pct=lambda v: f"{v} ({100*v/n:.1f}%)" if n else "n/a"; C=x["trustworthy_completion"]+x["unsafe_completion"]; S=x["trustworthy_completion"]+x["safe_non_completion"]
        report.append(f"| {labels[c]} | {pct(x['trustworthy_completion'])} | {pct(x['unsafe_completion'])} | {pct(x['safe_non_completion'])} | {pct(x['unsafe_failure'])} | {n} | {pct(C)} | {pct(S)} |")
    report += ["","## Audit","",f"- Valid cells: {len(valid)}/36; attempts: {len(attempt_dirs(repeat_id))}; invalid preserved attempts: {len(invalid)}.",f"- Unexplained artifact/scorer errors: {len(unexplained)}.",f"- Model calls with returned usage: {calls}; tokens: {tokens}.",f"- Known cost: USD {known:.6f}; unknown-cost attempts: {unknown}; conservative exposure: USD {known+unknown:.6f}."]
    (root/f"repeat_{repeat_id}_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    write_json(root/"artifact_validation_report.json",{"status":"pass" if technical else "fail","selected_valid_cells":len(valid),"scheduled_cells_traversed":36 if traversed else sum(1 for cell in repeat_cells(repeat_id) if (root/"runs"/cell.scheduled_run_id).exists()),"attempts":len(attempt_dirs(repeat_id)),"unexplained_errors":unexplained,"invalid_attempts":invalid})
    summary={"status":status,"valid_cells":len(valid),"valid_by_condition":by_condition,"counts":{c:dict(counts[c]) for c in CONDITIONS},"attempts":len(attempt_dirs(repeat_id)),"known_cost_usd":known,"unknown_cost_attempts":unknown,"conservative_exposure_usd":known+unknown,"model_calls_with_usage":calls,"recorded_tokens":tokens}
    write_json(root/f"repeat_{repeat_id}_summary.json",summary)
    return summary
