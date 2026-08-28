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
- refreshable data-integrity audit preserves the 451-file source tree, deterministic rescoring, and 108-cell grid
- append-only malformed-action adjudication is hash-valid and records no rerun
- historical Version 1 supplement source is unchanged
- historical Version 1 supplement PDF is unchanged
- 451 raw formal source artifacts retain their audited tree hash
- all 108 analysis rows are rebuilt from original attempts plus verified adjudication with identical C/S and termination fields
- raw deterministic rebuild has 112 attempts and no scientific/data errors
- 108 scheduled cells and 108 valid outcomes
- recomputed condition counts: no_warning = (36, 7, 27, 2, 0, 34, 9)
- recomputed condition counts: system_warning = (36, 10, 20, 5, 1, 30, 15)
- recomputed condition counts: ui_warning = (36, 10, 18, 5, 3, 28, 15)
- paper title matches the selected publication title
- publication research question is present
- main paper includes the exact v0.2 safeguard payload
- supplement includes the exact v0.2 safeguard payload
- audited main-text claim is present: completed 34/36 runs (94.4\%)
- audited main-text claim is present: 7/36 (19.4\%)
- audited main-text claim is present: 27/36 (75.0\%)
- audited main-text claim is present: System delivery increased $S$ by 16.7 percentage points
- audited main-text claim is present: reducing $C$ by 11.1 points
- audited main-text claim is present: reduced $C$ by 16.7 points
- audited main-text claim is present: $TC$ $0.0$ points ($[-16.7,+16.7]$)
- audited main-text claim is present: Known inference cost across all attempts was USD~7.51396168
- audited main-text claim is present: conservative exposure of USD~10.51396168
- audited main-text claim is present: Known invalid/retry overhead was USD~0.04736343
- Results contains exactly three numbered findings
- main paper and appendix use the approved anonymous artifact URL
- official checklist contains all 16 questions with no unanswered placeholder
- shared scientific source contains no individual workshop name
- all three venue wrappers contain only header metadata plus the shared master input
- main paper excludes obsolete phrase: Results will be populated
- main paper excludes obsolete phrase: [TO BE FROZEN
- main paper excludes obsolete phrase: No Warning
- main paper excludes obsolete phrase: System Warning
- main paper excludes obsolete phrase: UI Warning
- main paper excludes obsolete phrase: 81 runs
- main paper excludes obsolete phrase: Nova Lite
- main paper excludes obsolete phrase: nine tasks
- main paper excludes obsolete phrase: two sandboxes
- reviewer-facing doc excludes obsolete Version 1 phrasing: README.md
- reviewer-facing doc excludes obsolete Version 1 phrasing: docs/README.md
- reviewer-facing doc excludes obsolete Version 1 phrasing: docs/benchmark_card.md
- reviewer-facing doc excludes obsolete Version 1 phrasing: docs/stakeholder_harm_annotations.md
- reviewer-facing doc excludes obsolete Version 1 phrasing: docs/reproducibility.md
- reviewer-facing doc excludes obsolete Version 1 phrasing: docs/release.md
- reviewer-facing doc excludes obsolete Version 1 phrasing: dataset/README.md
- all 20 citation keys exist
- both required PDFs exist
- combined PDF orders body, references, appendix, and checklist (28 total; References page 8, appendix page 11, checklist page 22)
- supplement PDF is readable (11 pages)
- neurips_2026.log has no undefined references/citations or overfull boxes
- supplement_v2_formal.log has no undefined references/citations or overfull boxes
- number provenance contains 39 explicit claim mappings
- rendered manuscript source is anonymized

## Failures

- None.

## Reproduction commands

    PYTHONPATH=. .venv/bin/python -m scripts.v2.generate_manuscript_v02_assets
    PYTHONPATH=. .venv/bin/python -m scripts.v2.reproduce_release_v02
    node scripts/export_figure1_drawio.mjs
    PYTHONPATH=. .venv/bin/python scripts/export_figure1_pdf.py
    PYTHONPATH=. .venv/bin/python scripts/generate_figure2_interface_crops.py
    .venv/bin/python scripts/v2/generate_publication_figures_v02.py
    cd paper && tectonic --keep-logs --keep-intermediates neurips_2026.tex
    cd paper && tectonic --keep-logs --keep-intermediates supplement_v2_formal.tex
    PYTHONPATH=. .venv/bin/python -m scripts.v2.verify_manuscript_v02

Combined PDF: 28 pages; References begins on page 8; appendix begins on page 11; checklist begins on page 22.
Supplement: 11 pages.

## Output SHA-256

- Main PDF: d73cb80f53e1cfb2d1d3ad9c4048cbfe6e224a607801033c659b1b0e1bb91504
- Main LaTeX: dafaaa6590bc2001525bde00d8d175afacb734664ad5d6fc1a4d97f9908a2505
- Supplement PDF: a197db708e4938c4ca8b41f9cf9afd1b0b48c3800d39a09fa320018d89001d85
- Supplement LaTeX: 90f24dbb73d89041600f82744d3c5d1d0c84e296c1e84e6a28ef1a5b2dbac6f3
No model or paid API call is made by this verification.
