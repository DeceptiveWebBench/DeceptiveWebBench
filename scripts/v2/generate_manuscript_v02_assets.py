"""Generate Protocol v2 manuscript assets from audited machine-readable outputs."""

from __future__ import annotations

import csv
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "artifacts/v2/formal_v02_108/author_insight_review"
TABS = ROOT / "paper/tabs"
FIGS = ROOT / "paper/figs"
OUT = ROOT / "artifacts/v2/formal_v02_108/manuscript_update"
CONDS = ("no_warning", "system_warning", "ui_warning")
LABEL = {"no_warning": "No safeguard", "system_warning": "System-delivered safeguard", "ui_warning": "Interface-delivered safeguard"}
SHORT = {"no_warning": "No", "system_warning": "System", "ui_warning": "Interface"}


def load(name: str) -> list[dict[str, str]]:
    with (SRC / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def esc(value: object) -> str:
    text = str(value)
    for old, new in (("\\", r"\textbackslash{}"), ("_", r"\_"), ("%", r"\%"), ("&", r"\&"), ("#", r"\#")):
        text = text.replace(old, new)
    return text


def pct(value: object) -> str:
    return f"{100 * float(value):.1f}"


def pp(value: object) -> str:
    return f"{100 * float(value):+.1f}"


def write(path: Path, lines: list[str] | str) -> None:
    body = lines if isinstance(lines, str) else "\n".join(lines)
    path.write_text(body.rstrip() + "\n", encoding="utf-8")


def table(path: str, caption: str, label: str, spec: str, header: str, body: list[str], *,
          size: str = r"\small", landscape: bool = False) -> None:
    lines = []
    if landscape:
        lines.append(r"\begin{landscape}")
    lines += [r"\begin{table}[p]" if landscape else r"\begin{table}[t]", f"\\caption{{{caption}}}", f"\\label{{{label}}}",
              r"\centering", size, r"\setlength{\tabcolsep}{4pt}", f"\\begin{{tabular}}{{{spec}}}",
              r"\toprule", header, r"\midrule", *body, r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    if landscape:
        lines.append(r"\end{landscape}")
    write(TABS / path, lines)


def generate_tables(data: dict[str, object]) -> None:
    condition = data["condition"]
    body = []
    for row in condition:
        n = int(row["n_valid"])
        body.append(
            f"{LABEL[row['condition']]} & {row['trustworthy_completion']} & {row['unsafe_completion']} & "
            f"{row['safe_non_completion']} & {row['unsafe_failure']} & {n} & {pct(row['C_rate'])}\\% & "
            f"{pct(row['S_rate'])}\\% & {pct(row['TC_rate'])}\\% \\\\"
        )
    table("tab_results_v02.tex",
          r"Run-level outcomes by safeguard delivery. Rates use all 36 valid scheduled runs per condition. $C_r$: nominal completion; $S_r$: safety; $TC_r=C_r\land S_r$.",
          "tab:v02-main-results", "lrrrrrrrr",
          r"Condition & TC & Unsafe comp. & Safe non-comp. & Unsafe failure & Valid & $C$ & $S$ & $TC$ \\",
          body, size=r"\scriptsize")

    contrast = data["contrast"]
    order = ("system_warning_minus_no_warning", "ui_warning_minus_no_warning", "ui_warning_minus_system_warning")
    names = {order[0]: "System $-$ No", order[1]: "Interface $-$ No", order[2]: "Interface $-$ System"}
    lookup = {(r["contrast"], r["metric"]): r for r in contrast}
    body = []
    for name in order:
        for metric in ("S", "C", "TC"):
            row = lookup[(name, metric)]
            body.append(f"{names[name] if metric == 'S' else ''} & {metric} & {pp(row['estimate'])} & [{pp(row['ci95_low'])}, {pp(row['ci95_high'])}] \\\\")
        if name != order[-1]:
            body.append(r"\addlinespace[2pt]")
    caption = r"Prespecified percentage-point contrasts with 95\% task-cluster bootstrap intervals (10{,}000 replicates; seed 20260807). The direct Interface-minus-System contrast is secondary."
    table("tab_contrasts_v02.tex", caption, "tab:v02-contrasts", "llrr",
          r"Contrast & Metric & Estimate (pp) & 95\% interval (pp) \\", body, size=r"\scriptsize")
    table("tab_contrasts_v02_supp.tex", caption, "tab:v02-contrasts-supp", "llrr",
          r"Contrast & Metric & Estimate (pp) & 95\% interval (pp) \\", body)

    dataset = data["dataset"]
    tasks = sorted({r["task_id"] for r in dataset})
    body = []
    for task_id in tasks:
        task_rows = [r for r in dataset if r["task_id"] == task_id]
        cells = []
        for condition_name in CONDS:
            selected = [r for r in task_rows if r["condition"] == condition_name and r["valid"] == "1"]
            counts = Counter(r["outcome"] for r in selected)
            cell = "/".join(str(counts[k]) for k in ("trustworthy_completion", "unsafe_completion", "safe_non_completion", "unsafe_failure"))
            if len(selected) < 3:
                cell += r"$^{\dagger}$"
            cells.append(cell)
        body.append(f"\\texttt{{{esc(task_id)}}} & {task_rows[0]['pattern_family'].replace('_', ' ')} & " + " & ".join(cells) + r" \\")
    table("tab_task_outcomes_v02_supp.tex",
          r"Complete task-by-condition outcome counts. Cells report TC/UC/SNC/UF over three valid repeats.",
          "tab:v02-task-outcomes", "llccc",
          r"Task & Family & No safeguard & System-delivered & Interface-delivered \\", body, landscape=True)

    transitions = data["transitions"]
    body = []
    for condition_name in ("system_warning", "ui_warning"):
        selected = [r for r in transitions if r["condition"] == condition_name]
        body.append(
            f"{LABEL[condition_name]} & {len(selected)} & {sum(int(r['unsafe_to_trustworthy']) for r in selected)} & "
            f"{sum(int(r['unsafe_to_safe_noncompletion']) for r in selected)} & {sum(int(r['completion_loss']) for r in selected)} \\\\"
        )
    table("tab_paired_v02_supp.tex",
          "Paired task-repeat transitions relative to No safeguard. Pairs require both cells to be valid.",
          "tab:v02-paired", "lrrrr",
          r"Delivery & Valid pairs & Unsafe$\to$TC & Unsafe$\to$SNC & Completion loss \\", body)

    term = data["term"]
    classes = ("deliberate_safe_abort", "human_confirmation_requested", "unclassified_agent_stop", "timeout_or_step_limit", "agent_navigation_or_grounding_failure")
    lookup_term = {(r["condition"], r["termination_class"]): int(r["count"]) for r in term}
    body = [f"\\texttt{{{esc(kind)}}} & {lookup_term[(CONDS[0], kind)]} & {lookup_term[(CONDS[1], kind)]} & {lookup_term[(CONDS[2], kind)]} \\\\" for kind in classes]
    totals = [sum(lookup_term[(condition_name, kind)] for kind in classes) for condition_name in CONDS]
    body += [r"\midrule", f"Total non-completions & {totals[0]} & {totals[1]} & {totals[2]} \\\\"]
    table("tab_termination_v02_supp.tex",
          "Structured termination classes for valid non-completions. No cause is inferred from free-text reasoning.",
          "tab:v02-termination", "lrrr",
          r"Termination class & No safeguard & System-delivered & Interface-delivered \\", body)

    body = [f"{r['repeat_id']} & {LABEL[r['condition']]} & {r['n_valid']} & {pct(r['C_rate'])} & {pct(r['S_rate'])} & {pct(r['TC_rate'])} \\\\" for r in data["repeat"]]
    table("tab_repeats_v02_supp.tex",
          "Condition-wide rates by repeat. Every row contains 12 valid task cells.",
          "tab:v02-repeats", "llrrrr",
          r"Repeat & Delivery & Valid & $C$ (\%) & $S$ (\%) & $TC$ (\%) \\", body)

    loto = data["loto"]
    lookup_loto = {(r["omitted_task"], r["contrast"], r["metric"]): r for r in loto}
    body = []
    for task_id in sorted({r["omitted_task"] for r in loto}):
        vals = []
        for contrast_name in ("system_warning_minus_no_warning", "ui_warning_minus_no_warning"):
            vals.extend(pp(lookup_loto[(task_id, contrast_name, metric)]["estimate"]) for metric in ("S", "C", "TC"))
        body.append(f"\\texttt{{{esc(task_id)}}} & " + " & ".join(vals) + r" \\")
    table("tab_loto_v02_supp.tex",
          "Post-hoc leave-one-task-out sensitivity. Entries are percentage-point contrasts after omitting the named task; this was not a primary analysis.",
          "tab:v02-loto", "lrrrrrr",
          r"Omitted task & Sys. $\Delta S$ & Sys. $\Delta C$ & Sys. $\Delta TC$ & UI $\Delta S$ & UI $\Delta C$ & UI $\Delta TC$ \\",
          body, size=r"\scriptsize", landscape=True)

    family = data["family"]
    body = [f"{r['pattern_family'].replace('_', ' ')} & {LABEL[r['condition']]} & {r['n_valid']} & {pct(r['C_rate'])} & {pct(r['S_rate'])} & {pct(r['TC_rate'])} \\\\" for r in family]
    table("tab_family_v02_supp.tex",
          "Exploratory pattern-family summaries. Each family contains only four task identities.",
          "tab:v02-family", "llrrrr",
          r"Family & Delivery & Valid & $C$ (\%) & $S$ (\%) & $TC$ (\%) \\", body)

    body = [
        r"Original adapter output & \texttt{configuration\_contract\_failure} & -- & -- \\",
        r"Append-only adjudication & Valid safe non-completion & 0 & 1 \\",
    ]
    table("tab_adjudication_v02_supp.tex",
          "Protocol-consistency adjudication of the malformed-action cell. Original artifacts remain unchanged and no rerun was performed.",
          "tab:v02-adjudication", "lccc",
          r"Record & Classification & $C$ & $S$ \\", body)

    cost = [r for r in data["cost"] if r["grouping"] == "condition"]
    body = [f"{LABEL[r['group']]} & {r['n_valid']}/{r['n_cost_known']} & {float(r['cost_median_usd']):.4f} & {float(r['tokens_median']):,.0f} & {float(r['model_calls_median']):.1f} & {float(r['wall_clock_median_seconds']):.1f} \\\\" for r in cost]
    table("tab_cost_v02_supp.tex",
          "Operational cost and latency by delivery. Medians are descriptive; cost is reconstructed from the frozen AWS price table.",
          "tab:v02-cost", "lrrrrr",
          r"Delivery & Valid/cost-known & USD & Tokens & Calls & Wall time (s) \\", body)

    audit = data["audit"]
    body = [f"\\path{{{r['scheduled_run_id']}}} & {SHORT[r['condition']]} & {r['repeat_id']} & {r['attempt_id']} & {r['model_calls']} & \\path{{{r['original_run_validity']}}} \\\\" for r in audit["invalid_attempt_records"]]
    table("tab_invalid_v02_supp.tex",
          "Attempts originally classified invalid and retained in the audit. Four infrastructure failures produced permitted retries; the malformed-action attempt was append-only adjudicated as a valid behavioral outcome without rerun.",
          "tab:v02-invalid", r"L{.43\linewidth}lrrrL{.22\linewidth}",
          r"Scheduled cell & Condition & Repeat & Attempt & Calls & Machine reason \\", body, size=r"\scriptsize")


def copy_figures() -> None:
    # The publication crops are generated directly from the actual v2 sites by
    # scripts/generate_figure2_interface_crops.py.  Keep the manuscript asset
    # generator from replacing them with the older full-page review captures.
    expected = (
        FIGS / "task_family_forced_action_crop.png",
        FIGS / "task_family_sneaking_crop.png",
        FIGS / "task_family_interface_crop.png",
    )
    missing = [path for path in expected if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing publication interface crops; run "
            "PYTHONPATH=. .venv/bin/python scripts/generate_figure2_interface_crops.py: "
            + ", ".join(str(path) for path in missing)
        )
    write(FIGS / "task_family_examples_v02.tex", r"""
\begin{figure}[t]
  \centering
  \begingroup
  \setlength{\tabcolsep}{0pt}
  \begin{tabular}{c}
    \scriptsize\textbf{(a) Forced action: account creation versus guest checkout} \\[-1pt]
    \includegraphics[width=.98\linewidth]{task_family_forced_action_crop.png} \\[2pt]
    \scriptsize\textbf{(b) Sneaking: auto-renewing trial versus one-time rental} \\[-1pt]
    \includegraphics[width=.98\linewidth]{task_family_sneaking_crop.png} \\[2pt]
    \scriptsize\textbf{(c) Interface interference: broad versus necessary-only cookie consent} \\[-1pt]
    \includegraphics[width=.98\linewidth]{task_family_interface_crop.png}
  \end{tabular}
  \endgroup
  \caption{Focused crops from three benchmark task families at the frozen 1280$\times$720 viewport. Orange identifies the task's unsafe commitment boundary and blue the outcome-equivalent safe route; the annotations expose neither agent choices nor experimental outcomes.}
  \label{fig:task-families}
\end{figure}
""")


def provenance(data: dict[str, object]) -> int:
    out: list[dict[str, object]] = []

    def add(location: str, metric: str, shown: str, numerator: object, denominator: object,
            source: str, calculation: str, status: str) -> None:
        out.append({"manuscript_location": location, "metric": metric, "displayed_value": shown,
                    "numerator": numerator, "denominator": denominator, "source_artifact": source,
                    "source_field_or_calculation": calculation, "analysis_status": status})

    for row in data["condition"]:
        n = int(row["n_valid"])
        location = f"Main Results/Table 1/{LABEL[row['condition']]}"
        metrics = (("C", row["C_count"], row["C_rate"]), ("S", row["S_count"], row["S_rate"]),
                   ("TC", row["TC_count"], row["TC_rate"]),
                   ("unsafe completion", row["unsafe_completion"], float(row["unsafe_completion"]) / n),
                   ("safe non-completion", row["safe_non_completion"], float(row["safe_non_completion"]) / n),
                   ("unsafe failure", row["unsafe_failure"], float(row["unsafe_failure"]) / n))
        for metric, count, rate in metrics:
            add(location, metric, f"{count}/{n} ({pct(rate)}%)", count, n,
                "author_insight_review/condition_summary.csv", f"{metric} count / n_valid", "prespecified primary")
        add(location, "scheduled/valid/unavailable", f"{row['n_scheduled']}/{row['n_valid']}/{row['n_unavailable']}",
            row["n_valid"], row["n_scheduled"], "author_insight_review/condition_summary.csv",
            "n_scheduled,n_valid,n_unavailable", "prespecified accounting")
    for row in data["contrast"]:
        status = "prespecified secondary" if row["contrast"] == "ui_warning_minus_system_warning" else "prespecified primary"
        add("Main Results/contrasts and Figure 3", f"{row['contrast']} {row['metric']}",
            f"{pp(row['estimate'])} pp [{pp(row['ci95_low'])}, {pp(row['ci95_high'])}]",
            "", "12 task clusters", "author_insight_review/contrast_bootstrap.csv",
            "estimate,ci95_low,ci95_high; 10,000 task-cluster bootstrap replicates", status)
    fixed = (
        ("Main Results/run accounting", "scheduled cells", "108", 108, 108, "data_integrity_audit.json", "scheduled_cells", "prespecified accounting"),
        ("Main Results/run accounting", "valid cells", "108", 108, 108, "data_integrity_audit.json", "valid_cells", "prespecified accounting plus append-only protocol adjudication"),
        ("Main Results/run accounting", "attempts/invalid/retries", "112/5/4", 112, "", "data_integrity_audit.json", "attempts,invalid_attempts,retries", "prespecified accounting"),
        ("Main Results/adjudication", "malformed action C/S", "C=0; S=1", 0, 1, "technical_adjudication.json", "C_r,S_r; no rerun", "protocol-consistency adjudication"),
        ("Main Results/paired transitions", "unsafe-to-TC System", "2/36", 2, 36, "paired_transitions.csv", "sum(unsafe_to_trustworthy), system", "secondary diagnostic"),
        ("Main Results/paired transitions", "unsafe-to-TC Interface", "4/36", 4, 36, "paired_transitions.csv", "sum(unsafe_to_trustworthy), interface", "secondary diagnostic"),
        ("Main Results/paired transitions", "completion loss", "6 System; 7 Interface", "6;7", 36, "paired_transitions.csv", "sum(completion_loss) by condition", "secondary diagnostic"),
        ("Methods/design", "design cells", "12 x 3 x 3 = 108", 108, 108, "docs/experiment_matrix_v2.csv", "unique task-condition-repeat grid", "prespecified design"),
        ("Methods/statistics", "bootstrap", "10,000; seed 20260807; 12 task clusters", "", 12, "contrast_bootstrap.csv", "bootstrap_replicates,seed,cluster_unit", "prespecified primary"),
    )
    for args in fixed:
        add(*args)
    with (OUT / "manuscript_number_provenance.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)
    return len(out)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    TABS.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    data = {
        "condition": load("condition_summary.csv"),
        "contrast": load("contrast_bootstrap.csv"),
        "dataset": load("analysis_dataset.csv"),
        "task": load("task_condition_summary.csv"),
        "transitions": load("paired_transitions.csv"),
        "term": load("termination_summary.csv"),
        "repeat": load("repeat_summary.csv"),
        "loto": load("leave_one_task_out_posthoc.csv"),
        "family": load("family_summary_exploratory.csv"),
        "missing": load("missing_cell_sensitivity.csv"),
        "cost": load("cost_summary.csv"),
        "audit": json.loads((SRC / "data_integrity_audit.json").read_text(encoding="utf-8")),
    }
    generate_tables(data)
    copy_figures()
    count = provenance(data)
    print(json.dumps({"tables": 12, "copied_figures": 3, "provenance_rows": count}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
