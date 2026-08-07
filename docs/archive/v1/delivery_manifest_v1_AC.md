# Version 1 A--C delivery manifest

Target handoff: 2026-08-09 18:00 Asia/Shanghai

## Manuscript package

- Main LaTeX: `paper/neurips_2026.tex`
- Main PDF: `paper/paper_v1_AC_2026-08-09.pdf`
- Supplement LaTeX: `paper/supplement_v1_2026-08-09.tex`
- Supplement PDF: `paper/supplement_v1_2026-08-09.pdf`
- Bibliography: `paper/references.bib`
- Figures: `paper/figs/trustworthy_completion_framework.png`, `paper/figs/task_condition_heatmap.png`
- Tables: `paper/tabs/tab_main.tex`, `paper/tabs/tab_benchmark_comparison.tex`, `paper/tabs/tab_stakeholder_summary.tex`, `paper/tabs/tab_research_agenda.tex`, and the three `*_supp.tex` tables
- Style/build dependency: `paper/neurips_2026.sty`; build commands in `docs/reproducibility.md`

## Analysis and audit package

- Frozen analysis code: `analysis/aggregate_results.py`, `analysis/report.py`, `analysis/generate_figures.py`
- Statistical specification: `analysis/stats_plan.md`
- All generated CSV/Markdown results: `analysis/outputs/`
- 81-row run manifest: `analysis/outputs/run_manifest_v1.csv`
- Result confirmation: `docs/archive/v1/results_confirmation_report.md`
- Artifact verification: `docs/archive/v1/artifact_verification_log.md`
- Revision matrix: `docs/archive/v1/reviewer_revision_matrix.csv`
- Literature matrix: `docs/archive/v1/literature_extraction_matrix.csv`
- Compliance audit: `docs/archive/v1/revision_guide_compliance_audit.md`
- Protocol deviation audit: `docs/archive/v1/protocol_deviation_audit.md`
- Unresolved decisions: `docs/archive/v1/unresolved_decisions_memo.md`

## Benchmark documentation

- Benchmark card: `docs/benchmark_card.md`
- Task-construction protocol: `docs/task_construction_protocol.md`
- Full stakeholder/harm annotations: `docs/stakeholder_harm_annotations.md` and nine task YAML files under `env/tasks/`
- Dataset card and local staging builder: `dataset/README.md`, `dataset/build_hf_package.py`

Both PDFs are populated and passed compilation, page-count, metadata, and page-by-page visual checks. Local complete-delivery and anonymous-artifact ZIP archives are generated under `delivery/`. External publication and submission remain author-owned actions.
