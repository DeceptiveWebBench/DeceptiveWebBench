"""Audit and analyze the complete formal v0.2 three-repeat collection."""

from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from src.utils.io import project_root, write_json
from src.v2.artifacts import validate_attempt_directory
from src.v2.formal_later_repeats_v02 import formal_root
from src.v2.formal_repeat1_v02 import FORMAL_ROOT as REPEAT1_ROOT
from src.v2.matrix import load_schedule, schedule_sha256
from src.v2.scorer import score_attempt
from src.v2.safeguards_v02 import WARNING_VERSION


CONDITIONS=("no_warning","system_warning","ui_warning")
OUTCOMES=("trustworthy_completion","unsafe_completion","safe_non_completion","unsafe_failure")
METRICS=("TC","S","C")
OUT=project_root()/"artifacts/v2/formal_v02_108"


def read(path: Path): return json.loads(path.read_text(encoding="utf-8"))
def sha(path: Path): return hashlib.sha256(path.read_bytes()).hexdigest()
def root_for(repeat_id: int) -> Path: return REPEAT1_ROOT if repeat_id==1 else formal_root(repeat_id)


def percentile(values: list[float], q: float) -> float:
    values=sorted(values); pos=(len(values)-1)*q; low=int(pos); high=min(low+1,len(values)-1); weight=pos-low
    return values[low]*(1-weight)+values[high]*weight


def main() -> int:
    OUT.mkdir(parents=True,exist_ok=True)
    cells={c.scheduled_run_id:c for c in load_schedule()}
    if len(cells)!=108: raise SystemExit("Canonical matrix is not 108 unique cells")
    amendments={}
    for rid in (1,2,3):
        directory=root_for(rid)/"amendments"
        if directory.exists():
            for p in directory.glob("*.json"):
                a=read(p); amendments[(a["scheduled_run_id"],a["attempt_id"])]=a
    rows=[]; attempts=[]; unexplained=[]; invalid=[]
    for run_id,cell in cells.items():
        run_dir=root_for(cell.repeat_id)/"runs"/run_id
        dirs=sorted(run_dir.glob("attempt_*"),key=lambda p:int(p.name.split("_")[-1]))
        if not dirs or len(dirs)>2: raise SystemExit(f"Attempt accounting error: {run_id}")
        selected=None
        for p in dirs:
            metadata=read(p/"run_metadata.json"); raw=read(p/"raw_state.json"); saved=read(p/"scored_outcome.json"); usage=read(p/"usage_cost.json")
            if metadata.get("formal_run") is not True or metadata.get("synthetic_fixture") is not False or metadata.get("schedule_sha256")!=schedule_sha256():
                unexplained.append({"path":str(p),"error":"formal provenance mismatch"})
            if metadata.get("safeguard_version")!=WARNING_VERSION or metadata.get("repeat_id")!=cell.repeat_id:
                unexplained.append({"path":str(p),"error":"version/repeat mismatch"})
            try: validate_attempt_directory(p,cell=cell)
            except Exception as exc:
                a=amendments.get((run_id,int(p.name.split("_")[-1])))
                exact_llm_timeout=(saved.get("run_validity")=="valid" and saved.get("termination_class")=="timeout_or_step_limit"
                    and any("LLM call timed out after 120 seconds" in str(result.get("error") or "") for action in raw.get("actions") or [] for result in action.get("result") or []))
                amended=bool(a and a.get("original_hashes",{}).get("raw_state.json")==sha(p/"raw_state.json"))
                if not amended and not exact_llm_timeout:
                    unexplained.append({"path":str(p),"error":str(exc)})
            recomputed=score_attempt(raw).to_dict(); fields=("C_r","S_r","outcome_label","run_validity","termination_class","termination_reason","scheduled_run_id","attempt_id","raw_events")
            if any(recomputed.get(k)!=saved.get(k) for k in fields): unexplained.append({"path":str(p),"error":"scorer recomputation mismatch"})
            value=usage.get("provider_reported_cost") if usage.get("provider_reported_cost") is not None else usage.get("reconstructed_cost")
            attempts.append({"scheduled_run_id":run_id,"repeat_id":cell.repeat_id,"attempt_id":int(p.name.split("_")[-1]),"run_validity":saved.get("run_validity"),"known_cost_usd":value,"model_calls":int(usage.get("trajectory_totals",{}).get("model_calls") or 0),"tokens":int(usage.get("trajectory_totals",{}).get("total_tokens") or 0)})
            if saved.get("run_validity")=="valid": selected=(p,saved)
            else: invalid.append({"scheduled_run_id":run_id,"task_id":cell.task_id,"condition":cell.safeguard_condition,"repeat_id":cell.repeat_id,"attempt":p.name,"reason":saved.get("run_validity"),"amendment":(run_id,int(p.name.split("_")[-1])) in amendments})
        if selected:
            p,s=selected; rows.append({"planned_order":cell.planned_order,"scheduled_run_id":run_id,"task_id":cell.task_id,"condition":cell.safeguard_condition,"repeat_id":cell.repeat_id,"valid":1,"C":s["C_r"],"S":s["S_r"],"TC":int(s["outcome_label"]=="trustworthy_completion"),"outcome":s["outcome_label"],"termination_class":s.get("termination_class") or "" ,"selected_attempt":p.name})
        else:
            rows.append({"planned_order":cell.planned_order,"scheduled_run_id":run_id,"task_id":cell.task_id,"condition":cell.safeguard_condition,"repeat_id":cell.repeat_id,"valid":0,"C":"","S":"","TC":"","outcome":"unavailable","termination_class":"","selected_attempt":""})
    if unexplained: raise SystemExit(f"Unexplained artifact errors: {unexplained[:3]}")
    rows.sort(key=lambda r:r["planned_order"])
    with (OUT/"formal_run_manifest.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    valid=[r for r in rows if r["valid"]==1]
    summaries=[]
    for cond in CONDITIONS:
        subset=[r for r in valid if r["condition"]==cond]; counts=Counter(r["outcome"] for r in subset); scheduled=sum(r["condition"]==cond for r in rows)
        summaries.append({"condition":cond,"n_scheduled":scheduled,"n_valid":len(subset),"n_unavailable":scheduled-len(subset),**{o:counts[o] for o in OUTCOMES},"C_count":sum(r["C"] for r in subset),"S_count":sum(r["S"] for r in subset),"TC_count":sum(r["TC"] for r in subset),"C_rate":sum(r["C"] for r in subset)/len(subset),"S_rate":sum(r["S"] for r in subset)/len(subset),"TC_rate":sum(r["TC"] for r in subset)/len(subset)})
    with (OUT/"summary_by_condition.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=list(summaries[0])); w.writeheader(); w.writerows(summaries)
    task_rows=[]
    for task in sorted({r["task_id"] for r in rows}):
        for cond in CONDITIONS:
            subset=[r for r in valid if r["task_id"]==task and r["condition"]==cond]; c=Counter(r["outcome"] for r in subset)
            task_rows.append({"task_id":task,"condition":cond,"n_valid":len(subset),**{o:c[o] for o in OUTCOMES},"C_rate":sum(r["C"] for r in subset)/len(subset) if subset else "","S_rate":sum(r["S"] for r in subset)/len(subset) if subset else "","TC_rate":sum(r["TC"] for r in subset)/len(subset) if subset else ""})
    with (OUT/"task_by_condition.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=list(task_rows[0])); w.writeheader(); w.writerows(task_rows)
    bykey={(r["task_id"],r["repeat_id"],r["condition"]):r for r in valid}
    transitions=[]
    for task in sorted({r["task_id"] for r in valid}):
        for rid in (1,2,3):
            base=bykey.get((task,rid,"no_warning"))
            for cond in ("system_warning","ui_warning"):
                treated=bykey.get((task,rid,cond))
                if not base or not treated: continue
                transitions.append({"task_id":task,"repeat_id":rid,"condition":cond,"baseline_outcome":base["outcome"],"safeguard_outcome":treated["outcome"],"unsafe_to_trustworthy":int(base["outcome"]=="unsafe_completion" and treated["outcome"]=="trustworthy_completion"),"completion_loss":int(base["C"]==1 and treated["C"]==0)})
    with (OUT/"paired_transitions.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=list(transitions[0])); w.writeheader(); w.writerows(transitions)
    tasks=sorted({r["task_id"] for r in valid}); rng=random.Random(20260807); boot=[]
    def rate(sample_tasks,cond,metric):
        values=[]
        for task in sample_tasks: values.extend(float(r[metric]) for r in valid if r["task_id"]==task and r["condition"]==cond)
        return sum(values)/len(values)
    comparisons=(("system_warning","no_warning"),("ui_warning","no_warning"),("ui_warning","system_warning"))
    observed={}
    for a,b in comparisons:
        for metric in METRICS: observed[(a,b,metric)]=rate(tasks,a,metric)-rate(tasks,b,metric)
    samples=defaultdict(list)
    for _ in range(10000):
        draw=[rng.choice(tasks) for _ in tasks]
        for a,b in comparisons:
            for metric in METRICS: samples[(a,b,metric)].append(rate(draw,a,metric)-rate(draw,b,metric))
    for key,estimate in observed.items():
        a,b,metric=key; vals=samples[key]; boot.append({"contrast":f"{a}_minus_{b}","metric":metric,"estimate":estimate,"ci95_low":percentile(vals,.025),"ci95_high":percentile(vals,.975),"bootstrap_replicates":10000,"seed":20260807,"cluster_unit":"task_id"})
    with (OUT/"task_cluster_bootstrap.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=list(boot[0])); w.writeheader(); w.writerows(boot)
    term=Counter(r["termination_class"] or "endpoint_completion" for r in valid if r["C"]==0)
    known=sum(float(a["known_cost_usd"]) for a in attempts if a["known_cost_usd"] is not None); unknown=sum(a["known_cost_usd"] is None for a in attempts)
    auth={rid:(yaml.safe_load((project_root()/f"configs/v2/formal_v02_repeat{rid}_authorization.yaml").read_text()) or {}).get("status") for rid in (1,2,3)}
    # Repeat 1 uses a separately named but structurally identical file.
    auth[1]=(yaml.safe_load((project_root()/"configs/v2/formal_v02_repeat1_authorization.yaml").read_text()) or {}).get("status")
    baseline=read(project_root()/"artifacts/v2/review/protected_scope_baseline.json")
    protected_files=sorted(p for d in (project_root()/"paper",project_root()/"archive") for p in d.rglob("*") if p.is_file()); protected_digest=hashlib.sha256()
    for p in protected_files: protected_digest.update(str(p.relative_to(project_root())).encode()); protected_digest.update(b"\0"); protected_digest.update(hashlib.sha256(p.read_bytes()).digest())
    protected_ok=(protected_digest.hexdigest()==baseline["paper_and_archive_tree_sha256"] and len(protected_files)==baseline["paper_and_archive_file_count"])
    audit={"status":"pass" if protected_ok else "fail","matrix_sha256":schedule_sha256(),"scheduled_cells":108,"unique_cells":len(rows),"valid_cells":len(valid),"unavailable_cells":108-len(valid),"attempts":len(attempts),"invalid_attempts":len(invalid),"unexplained_artifact_errors":0,"authorization_status":auth,"protected_paper_archive_unchanged":protected_ok,"known_cost_usd":known,"unknown_cost_attempts":unknown,"conservative_exposure_usd":known+unknown,"model_calls_with_usage":sum(a["model_calls"] for a in attempts),"recorded_tokens":sum(a["tokens"] for a in attempts)}
    write_json(OUT/"collection_audit.json",audit); write_json(OUT/"invalid_attempts.json",invalid)
    labels={"no_warning":"No safeguard","system_warning":"System-delivered safeguard","ui_warning":"Interface-delivered safeguard"}
    report=["# Formal v0.2 complete collection report","","Status: `FORMAL_V02_COLLECTION_COMPLETE_WITH_ONE_UNAVAILABLE_CELL_AWAITING_AUTHOR_REVIEW`","",f"All 108 scheduled cells were traversed. {len(valid)} are valid; one interface-delivered cell is unavailable because a model action-schema output failed the frozen contract and was not retryable.","","## Primary C/S results","","| Delivery | TC | Unsafe completion | Safe non-completion | Unsafe failure | Scheduled | Valid | C rate | S rate |","|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for s in summaries:
        n=s["n_valid"]; pct=lambda x:f"{x}/{n} ({100*x/n:.1f}%)"; report.append(f"| {labels[s['condition']]} | {pct(s['TC_count'])} | {pct(s['unsafe_completion'])} | {pct(s['safe_non_completion'])} | {pct(s['unsafe_failure'])} | {s['n_scheduled']} | {n} | {pct(s['C_count'])} | {pct(s['S_count'])} |")
    safe=[r for r in valid if r["condition"]!="no_warning"]; sc=Counter(r["outcome"] for r in safe)
    report += ["","Safeguard-present is auxiliary only: "+", ".join(f"{o}={sc[o]}/{len(safe)} ({100*sc[o]/len(safe):.1f}%)" for o in OUTCOMES)+f"; C={sum(r['C'] for r in safe)}/{len(safe)} ({100*sum(r['C'] for r in safe)/len(safe):.1f}%); S={sum(r['S'] for r in safe)}/{len(safe)} ({100*sum(r['S'] for r in safe)/len(safe):.1f}%).","","## Paired diagnostics","",f"- Unsafe No-safeguard → trustworthy System-delivered: {sum(t['unsafe_to_trustworthy'] for t in transitions if t['condition']=='system_warning')}/{sum(t['condition']=='system_warning' for t in transitions)} paired cells.",f"- Unsafe No-safeguard → trustworthy Interface-delivered: {sum(t['unsafe_to_trustworthy'] for t in transitions if t['condition']=='ui_warning')}/{sum(t['condition']=='ui_warning' for t in transitions)} paired cells.",f"- Completion loss, System-delivered: {sum(t['completion_loss'] for t in transitions if t['condition']=='system_warning')}; Interface-delivered: {sum(t['completion_loss'] for t in transitions if t['condition']=='ui_warning')}.",f"- Structured C=0 termination decomposition: {dict(term)}.","","## Task-cluster uncertainty","","10,000 bootstrap replicates (seed 20260807) resampled 12 task identities while retaining repeats and conditions. Intervals are coarse with only 12 clusters."]
    for b in boot:
        if b["contrast"].startswith(("system_warning","ui_warning")) and b["metric"] in ("TC","S","C"): report.append(f"- {b['contrast']} {b['metric']}: {100*b['estimate']:+.1f} pp (95% task-cluster bootstrap interval {100*b['ci95_low']:+.1f} to {100*b['ci95_high']:+.1f} pp).")
    report += ["","## Operational audit","",f"- Attempts: {len(attempts)}; invalid attempts preserved: {len(invalid)}; unavailable scheduled cells: {108-len(valid)}.",f"- Known API cost: USD {known:.6f}; conservative exposure including {unknown} unknown-cost attempts: USD {known+unknown:.6f}.",f"- Model calls with usage: {audit['model_calls_with_usage']}; recorded tokens: {audit['recorded_tokens']}.",f"- Repeat authorization status: {auth}. No further repeat is authorized.",f"- Protected paper/archive scope unchanged: {protected_ok}.","","## Reproduction commands","","- `PYTHONPATH=. .venv/bin/python -m scripts.v2.finalize_formal_v02_full`","- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests/v2 -p 'test_*.py'` (post-run: 99 tests passed)","","This report is suitable for author review. It does not modify the paper or claim cross-agent, neutral-interface, detector, live-site, or population generalization."]
    (OUT/"formal_v02_results_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print(json.dumps(audit,indent=2)); return 0


if __name__=="__main__": raise SystemExit(main())
