# Revision Guide compliance audit

Audit date: 2026-08-05

The Word Revision Guide is the governing source for the workshop revision. `docs/archive/v1/paper_revision_inputs.md` and `docs/stakeholder_harm_annotations.md` supply implementation facts, but they do not override the Guide's positioning, research question, scope, or deliverables.

## Locked manuscript elements

| Element | Audit result | Action |
|---|---|---|
| Title | Exact match to the Revision Guide working title | Locked; no Codex edits without explicit author instruction |
| Abstract | Author states the current abstract is already updated | Locked; use as a consistency constraint |
| Research question | The first auxiliary draft was semantically similar but not verbatim | Corrected to the exact Revision Guide wording |

## Audit of work completed on August 5

| Work completed | Revision Guide basis | Result |
|---|---|---|
| Added stakeholder/harm fields to all nine task YAML files | A2 | Compliant: all eight required qualitative fields are present; no numerical severity score was added |
| Created the claim hierarchy and eight-page structure | A1, B2, B3 | Compliant after correcting the research question and locking the existing title/abstract |
| Created reviewer-to-revision matrix | Appendix B and Section C | Compliant; this is an explicit Version 1 deliverable |
| Audited `interface_perm_001` wording provenance | A5 and Section 7 | The 81 outcomes remain primary and unchanged; repository history establishes a System-warning wording deviation, which is quantified in a labeled 72-run sensitivity analysis. |
| Created the August 9 execution plan | Sections 2, 3, and C | Compliant; D and E remain future work and are not started before Version 1 is stable |

## A--C acceptance matrix

| Guide item | Version 1 evidence | Status |
|---|---|---|
| A1: interdisciplinary framing and scoped claims | Locked approved title/abstract; rewritten Introduction, contributions, implications, and Conclusion; verbatim research question | Complete; author directed that the historical wording issue remain outside the main paper |
| A2: nine stakeholder/harm annotations | Nine task YAML files; `docs/stakeholder_harm_annotations.md`; main and supplement tables | Complete |
| A3: task-construction protocol | Formal tuple and seven criteria in manuscript, `docs/benchmark_card.md`, and `docs/task_construction_protocol.md` | Complete |
| A4: three evaluation layers | Main conceptual figure and Framework section | Complete |
| A5: existing-data reanalysis | 81-cell audit, four-way counts, explicit denominators, task table/heatmap, task-cluster intervals, conservative failure audit, path diagnostic, wording sensitivity | Complete |
| A6: artifact repair/extension | Benchmark card, metadata, protocol, staging builder, run manifest, exact commands, logged-out checks | Locally complete; external repository sync and non-empty HF upload require author authorization |
| B1: narrower related work | Threat-source structure, compact comparison table, 26-row literature matrix, bibliography | Complete |
| B2: workshop structure | Eight required sections and workshop style | Complete; 7 PDF pages total, with main text ending on page 5 and References beginning on page 6 |
| B3: concrete research agenda | D, E, detector, scale, long-horizon, human, and population designs labeled planned | Complete |
| C: delivery package | Source, figures, tables, supplement, matrices, manifest, logs, memo, and visually verified PDFs | Complete locally; author-owned external sync remains unresolved |

## Rules for subsequent Codex work

1. Do not modify the current title or abstract unless the author explicitly requests it.
2. Use the Revision Guide research question verbatim.
3. Treat A-C as the complete August 9 deliverable; describe D, E, and longer-term work as planned studies.
4. Do not add numerical harm-severity scores.
5. Do not make general warning-channel, human-comparison, population-causal, or taxonomy-completeness claims.
6. Keep counts, denominators, uncertainty, invalid runs, reruns, and protocol deviations explicit.
7. When repository evidence conflicts with prose, flag the conflict and preserve an audit trail rather than silently rewriting the study history.
