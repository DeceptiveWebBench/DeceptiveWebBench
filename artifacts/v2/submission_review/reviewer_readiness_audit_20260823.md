# Reviewer-readiness audit (2026-08-23)

## Bottom line

The manuscript is internally complete and submission-readable. The main empirical claims match the audited 108-cell dataset, the four-quadrant framing is consistently defined, the safeguard comparison is appropriately described as a comparison of complete delivery strategies, and limitations do not overclaim causal or cross-agent generality. The main paper remains 8 body pages (10 PDF pages including references). The formal supplement was reduced from 13 to 10 pages without removing any unique numerical result.

## Immediate fixes completed

- Reworded the abstract's malformed-action sentence to state the append-only adjudication and frozen validity rule directly.
- Replaced the misleading phrase “formerly unavailable” with an explicit correction of the adapter's original invalid label.
- Removed unresolved author/artifact TODO comments from the anonymous manuscript source; private submission metadata remains outside the PDF source.
- Added a Responsible Research and Intended Use section covering synthetic sites/data, absence of human participants and real transactions, and the benchmark's intended use.
- Removed duplicate supplement presentations: the raw task-outcome table and task-profile heatmap remain, while the redundant task-rate table was dropped; the cost table remains, while the redundant cost figure was dropped.
- Reformatted the invalid-attempt audit table in portrait orientation and removed overfull boxes.

## Remaining reviewer risks requiring author or new-study decisions

### High priority before submission

1. **Anonymous artifact availability.** The PDF is reproducible from the local repository, but no anonymous, logged-out-accessible artifact URL has been supplied. Add and test one if the venue permits artifacts; otherwise avoid implying that reviewers can access it.
2. **Narrow empirical scope.** One agent/scaffold, 12 synthetic tasks, and three repeats support a controlled diagnostic result, not broad web-agent prevalence. The paper discloses this clearly. Stronger generality requires a new model or live/neutral-site experiment and cannot be repaired by prose.
3. **No neutral-interface controls.** The experiment estimates safeguard-condition differences within deceptive tasks, not the causal effect of deception. Keep the present framing; a neutral twin design is the appropriate follow-up.
4. **Delivery-strategy confounding.** A privileged instruction and a persistent UI notice differ in more than an abstract “channel.” The manuscript correctly calls them complete delivery strategies. A factorial timing/persistence/content study is needed for a channel-mechanism claim.
5. **Model reproducibility.** The provider exposed neither a snapshot nor a sampling seed. The frozen identifier, configuration, schedule, three repeats, and task-cluster intervals are the available mitigation, but exact replay is not guaranteed.
6. **Submission packaging and policy.** IAEval and AI4GOOD lack a separate supplement field; decide whether to append the 10-page supplement or ask the chairs. Written permission is still needed from IAEval and Verify-Agents before identical-core multi-workshop submission.

### Medium priority / positioning choices

- **Title breadth.** “A Benchmark and Research Agenda” is defensible, but reviewers may view 12 synthetic tasks as a diagnostic suite rather than a broad benchmark. If title changes are allowed, “A Diagnostic Benchmark…” would calibrate scope more tightly.
- **Safety terminology.** Here, $S$ means avoidance of a task-specific annotated unsafe commitment, not general agent safety. The manuscript defines this repeatedly; retain that qualification in metadata and presentations.
- **Post-collection adjudication.** The append-only, hash-linked correction follows the frozen malformed-action rule and preserves originals, but remains a likely reviewer question. Keep the current transparent accounting and do not hide it in the supplement only.
- **Task heterogeneity.** With four tasks per family, family comparisons are exploratory. The current wording is appropriately cautious; avoid stronger family-level claims in the abstract or OpenReview metadata.

## Verification completed

- Manuscript verifier: 60 checks passed, 0 failed.
- Protocol/browser tests: 101 passed in the full run; one browser-start timeout passed immediately when rerun in isolation, indicating a transient test-environment delay rather than a contract failure.
- LaTeX: main and supplement compile without undefined citations/references, LaTeX errors, or overfull boxes.
- Visual QA: all 10 main-paper pages and all 10 supplement pages were rendered and inspected; no clipping, overlap, or unreadable final-page content was found.
- Venue wrappers: AI4GOOD, IAEval, and Verify-Agents versions compile successfully.

