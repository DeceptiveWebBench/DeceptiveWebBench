# Protocol v2 Formal Manuscript Change Summary

## Empirical narrative

- Replaced the pre-results framing with the completed 108-cell Protocol v2 experiment.
- Made the capability--trustworthiness gap the headline: No safeguard reached 94.4% nominal completion but only 19.4% trustworthy completion, with 75.0% unsafe completion.
- Presented both safeguard strategies as safety--completion tradeoffs. Both increased safety by 16.7 percentage points; System and Interface delivery reduced completion by 11.1 and 16.7 points, respectively.
- Reported the direct Interface-minus-System comparison as unresolved and explicitly stated that an unresolved contrast is not evidence of equivalence.
- Applied the frozen malformed-action rule through a hash-linked append-only adjudication, yielding 108/108 valid outcomes without rerunning the API or changing original attempt artifacts.

## Main manuscript

- Preserved the exact title and Revision Guide research question.
- Updated the abstract, introduction, methods, results, discussion, limitations, research agenda, and conclusion.
- Replaced planned-run language with the frozen model, browser, sampling, timing, retry, and scoring configuration.
- Added the exact generic safeguard v0.2 payload and the required condition names: No safeguard, System-delivered safeguard, and Interface-delivered safeguard.
- Added a main outcome table, C/S quadrant figure, safeguard tradeoff figure, revised framework diagram, and representative task screenshots.
- Kept the body to eight pages; references follow the conclusion.

## Supplement

- Created a new Protocol v2 supplement without replacing the historical Version 1 supplement.
- Included run accounting, original invalid classifications, frozen configuration, exact payload, complete task-by-condition outcomes, task profiles, paired transitions, termination decomposition, repeat summaries, the protocol-consistency adjudication, exploratory family summaries, complete post-hoc leave-one-task-out sensitivity, operational cost, and reproduction commands.
- Classified analyses as prespecified primary, prespecified secondary, exploratory, or post-hoc.

## Reproducibility and protection

- Generated all manuscript tables and copied audited figures with scripts/v2/generate_manuscript_v02_assets.py.
- Created 41 claim-to-source mappings in manuscript_number_provenance.csv.
- Added scripts/v2/verify_manuscript_v02.py to validate review-source hashes, the 451-file formal source tree, condition counts, title, research question, payload, citations, page limits, compile logs, anonymity, and Version 1 supplement preservation.
- The raw formal artifact tree remains SHA-256 431089427c682dba9046391c4011c55d7ee603537346f3ffc81b871764cd0f12.
- The historical supplement source remains SHA-256 18a81491058602e7df1dd2bc708f2a3e5d42717bafa68312537fd7c73e72be08.
- No model/API call, new experiment, raw-data edit, commit, push, or public release was performed.

## Files in this delivery

- Main manuscript: paper/neurips_2026.tex and paper/neurips_2026.pdf.
- New supplement: paper/supplement_v2_formal.tex and paper/supplement_v2_formal.pdf.
- Bibliography: paper/references.bib.
- Generated main/supplement tables: paper/tabs/tab_results_v02.tex, tab_contrasts_v02.tex, tab_contrasts_v02_supp.tex, tab_task_outcomes_v02_supp.tex, tab_task_profiles_v02_supp.tex, tab_paired_v02_supp.tex, tab_termination_v02_supp.tex, tab_repeats_v02_supp.tex, tab_loto_v02_supp.tex, tab_family_v02_supp.tex, tab_adjudication_v02_supp.tex, tab_cost_v02_supp.tex, and tab_invalid_v02_supp.tex.
- Figures: paper/figs/trustworthy_completion_cs_pipeline.pdf and the protocol_v2_* result/interface figures used by the main paper and supplement.
- Build and verification: scripts/v2/generate_manuscript_v02_assets.py, scripts/v2/verify_manuscript_v02.py, and paper/figs/make_trustworthy_completion_figure.py.
- Audit outputs: manuscript_number_provenance.csv, manuscript_verification_report.md, change_summary.md, and remaining_author_decisions.md in this directory.
