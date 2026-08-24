# Formal v0.2 complete collection report

> **Superseded aggregate view.** This report preserves the initial collection
> accounting. The append-only protocol-consistency adjudication described in
> `ADJUDICATION_NOTICE.md` produces the authoritative 108/108-valid analysis.

Status: `FORMAL_V02_COLLECTION_COMPLETE_WITH_ONE_UNAVAILABLE_CELL_AWAITING_AUTHOR_REVIEW`

All 108 scheduled cells were traversed. 107 are valid; one interface-delivered cell is unavailable because a model action-schema output failed the frozen contract and was not retryable.

## Primary C/S results

| Delivery | TC | Unsafe completion | Safe non-completion | Unsafe failure | Scheduled | Valid | C rate | S rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| No safeguard | 7/36 (19.4%) | 27/36 (75.0%) | 2/36 (5.6%) | 0/36 (0.0%) | 36 | 36 | 34/36 (94.4%) | 9/36 (25.0%) |
| System-delivered safeguard | 10/36 (27.8%) | 20/36 (55.6%) | 5/36 (13.9%) | 1/36 (2.8%) | 36 | 36 | 30/36 (83.3%) | 15/36 (41.7%) |
| Interface-delivered safeguard | 10/35 (28.6%) | 18/35 (51.4%) | 4/35 (11.4%) | 3/35 (8.6%) | 36 | 35 | 28/35 (80.0%) | 14/35 (40.0%) |

Safeguard-present is auxiliary only: trustworthy_completion=20/71 (28.2%), unsafe_completion=38/71 (53.5%), safe_non_completion=9/71 (12.7%), unsafe_failure=4/71 (5.6%); C=58/71 (81.7%); S=29/71 (40.8%).

## Paired diagnostics

- Unsafe No-safeguard → trustworthy System-delivered: 2/36 paired cells.
- Unsafe No-safeguard → trustworthy Interface-delivered: 4/35 paired cells.
- Completion loss, System-delivered: 6; Interface-delivered: 6.
- Structured C=0 termination decomposition: {'unclassified_agent_stop': 8, 'timeout_or_step_limit': 6, 'deliberate_safe_abort': 1}.

## Task-cluster uncertainty

10,000 bootstrap replicates (seed 20260807) resampled 12 task identities while retaining repeats and conditions. Intervals are coarse with only 12 clusters.
- system_warning_minus_no_warning TC: +8.3 pp (95% task-cluster bootstrap interval +0.0 to +16.7 pp).
- system_warning_minus_no_warning S: +16.7 pp (95% task-cluster bootstrap interval +2.8 to +33.3 pp).
- system_warning_minus_no_warning C: -11.1 pp (95% task-cluster bootstrap interval -22.2 to +0.0 pp).
- ui_warning_minus_no_warning TC: +9.1 pp (95% task-cluster bootstrap interval -8.3 to +31.1 pp).
- ui_warning_minus_no_warning S: +15.0 pp (95% task-cluster bootstrap interval -2.1 to +36.0 pp).
- ui_warning_minus_no_warning C: -14.4 pp (95% task-cluster bootstrap interval -25.0 to -5.6 pp).
- ui_warning_minus_system_warning TC: +0.8 pp (95% task-cluster bootstrap interval -16.7 to +19.4 pp).
- ui_warning_minus_system_warning S: -1.7 pp (95% task-cluster bootstrap interval -24.5 to +17.0 pp).
- ui_warning_minus_system_warning C: -3.3 pp (95% task-cluster bootstrap interval -18.6 to +11.1 pp).

## Operational audit

- Attempts: 112; invalid attempts preserved: 5; unavailable scheduled cells: 1.
- Known API cost: USD 7.513962; conservative exposure including 3 unknown-cost attempts: USD 10.513962.
- Model calls with usage: 1031; recorded tokens: 12383360.
- Repeat authorization status: {1: 'consumed', 2: 'consumed', 3: 'consumed'}. No further repeat is authorized.
- Protected paper/archive scope unchanged: True.

## Reproduction commands

- `PYTHONPATH=. .venv/bin/python -m scripts.v2.finalize_formal_v02_full`
- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests/v2 -p 'test_*.py'` (post-run: 99 tests passed)

This report is suitable for author review. It does not modify the paper or claim cross-agent, neutral-interface, detector, live-site, or population generalization.
