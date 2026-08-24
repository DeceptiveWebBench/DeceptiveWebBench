# Protocol v2 Manuscript Verification Report

Status: **PASS**

## Verified

- review source hash: analysis_dataset.csv
- review source hash: attempt_audit.csv
- review source hash: author_decision_checklist.md
- review source hash: claim_evidence_matrix.csv
- review source hash: condition_summary.csv
- review source hash: contrast_bootstrap.csv
- review source hash: cost_by_task.csv
- review source hash: cost_efficiency_analysis.md
- review source hash: cost_summary.csv
- review source hash: data_integrity_audit.json
- review source hash: data_integrity_audit.md
- review source hash: family_summary_exploratory.csv
- review source hash: fig_cost_latency_supplement.png
- review source hash: fig_cs_quadrants_by_condition.png
- review source hash: fig_paired_transitions.png
- review source hash: fig_task_condition_heatmap.png
- review source hash: fig_tradeoff_contrasts.png
- review source hash: leave_one_task_out_posthoc.csv
- review source hash: manuscript_insight_memo.md
- review source hash: missing_cell_sensitivity.csv
- review source hash: paired_transitions.csv
- review source hash: proposed_results_outline.md
- review source hash: repeat_consistency.csv
- review source hash: repeat_summary.csv
- review source hash: statistical_analysis_report.md
- review source hash: task_condition_summary.csv
- review source hash: task_level_insights.md
- review source hash: termination_and_failure_analysis.md
- review source hash: termination_summary.csv
- 451 raw formal source artifacts retain their audited tree hash
- append-only malformed-action adjudication is hash-valid and records no rerun
- historical Version 1 supplement source is unchanged
- historical Version 1 supplement PDF is unchanged
- all 108 analysis rows are rebuilt from original attempts plus verified adjudication with identical C/S and termination fields
- raw deterministic rebuild has 112 attempts and no scientific/data errors
- 108 scheduled cells and 108 valid outcomes
- recomputed condition counts: no_warning = (36, 7, 27, 2, 0, 34, 9)
- recomputed condition counts: system_warning = (36, 10, 20, 5, 1, 30, 15)
- recomputed condition counts: ui_warning = (36, 10, 18, 5, 3, 28, 15)
- paper title is exactly preserved
- Revision Guide research question is verbatim
- main paper includes the exact v0.2 safeguard payload
- supplement includes the exact v0.2 safeguard payload
- main paper excludes obsolete phrase: Results will be populated
- main paper excludes obsolete phrase: [TO BE FROZEN
- main paper excludes obsolete phrase: No Warning
- main paper excludes obsolete phrase: System Warning
- main paper excludes obsolete phrase: UI Warning
- main paper excludes obsolete phrase: 81 runs
- main paper excludes obsolete phrase: Nova Lite
- main paper excludes obsolete phrase: nine tasks
- main paper excludes obsolete phrase: two sandboxes
- all 20 citation keys exist
- both required PDFs exist
- main PDF has 8 body pages plus references (10 total; References starts after the conclusion on page 8)
- supplement PDF is readable (10 pages)
- neurips_2026.log has no undefined references/citations or overfull boxes
- supplement_v2_formal.log has no undefined references/citations or overfull boxes
- number provenance contains 39 explicit claim mappings
- rendered manuscript source is anonymized

## Failures

- None.

## Reproduction commands

    PYTHONPATH=. .venv/bin/python -m scripts.v2.generate_manuscript_v02_assets
    cd paper && tectonic --keep-logs --keep-intermediates neurips_2026.tex
    cd paper && tectonic --keep-logs --keep-intermediates supplement_v2_formal.tex
    PYTHONPATH=. .venv/bin/python -m scripts.v2.verify_manuscript_v02

Main PDF: 10 pages; body: 8 pages; References begins after the conclusion on page 8.
Supplement: 10 pages.

## Output SHA-256

- Main PDF: 7e457cbf349f0641b28c432d441f9a708ea545a205428cda7b777d9cd739d04d
- Main LaTeX: c882c8e33bea9943734d8ab0e3313afe9b62ea1444c0fa580f1c060f5fb2ab90
- Supplement PDF: 9d4af6330c4f3177301a44d3c5d37b7476c49d9a16b94b0d41bd2a89bb6ff872
- Supplement LaTeX: 77da931e7de3c06980e527b5c4adc037df8df03c0a22a9e19ac4524e5c50819b
No model or paid API call is made by this verification.
