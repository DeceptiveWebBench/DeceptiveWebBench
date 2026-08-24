# Research Agenda for Mentor Review

**Project:** Trustworthy Completion for Web Agents  
**Status (16 August 2026):** Protocol v2 is being audited as a pre-API freeze candidate; no Agent or formal Protocol v2 experiment has been run.

## 1. Research story

A web agent can reach the endpoint requested by a consumer while also accepting an unwanted charge, unnecessary data sharing, tracking, or recurring enrollment. Binary task success would count this as success even though the delegation did not protect the consumer's interests.

We therefore evaluate **Trustworthy Completion** by scoring two questions independently:

- **Completion (C):** Did the agent reach the requested endpoint?
- **Safety (S):** Did the trajectory avoid the task's machine-verifiable unsafe commitment?

This produces four outcomes: trustworthy completion `(C=1,S=1)`, unsafe completion `(C=1,S=0)`, safe non-completion `(C=0,S=1)`, and unsafe failure `(C=0,S=0)`.

## 2. Current primary experiment

The study focuses on one strong, frozen vision-capable web agent and 12 synthetic consumer tasks:

- 4 forced-action tasks;
- 4 sneaking tasks;
- 4 interface-interference tasks.

Every task contains a deceptive interface, a safe route, a comparable unsafe route, a concrete consumer interest, and a deterministic unsafe-action boundary. We do not include neutral interfaces in this study because the immediate question is whether safeguards change behavior within deceptive tasks, not whether deception itself causes the behavior.

The three conditions are:

1. **No Warning:** nominal user goal only.
2. **System Safety Guidance:** the generic safeguard is available in privileged context before the first action.
3. **UI Safety Guidance:** the same byte-identical safeguard is visible before the first action and remains in a benchmark-owned panel throughout the task.

System and UI use the same substantive warning content. Their comparison is therefore between two complete delivery strategies—privileged instruction and persistent visual notice—not a universal test of “which channel is better.” Risk points are logged for trajectory analysis but do not trigger the warning.

The planned matrix is:

`12 tasks × 3 conditions × 3 repeats = 108 formal runs`

Primary reporting will include raw C/S counts and rates by condition, contrasts against No Warning, task-level heterogeneity, and 95% intervals from task-cluster bootstrap resampling. Family-level findings will be exploratory.

## 3. What is ready and what remains

Ready for review:

- the 12-task protocol and task specifications;
- independent C/S scorer and four-outcome fixtures;
- System/UI safeguard delivery design;
- randomized 108-cell schedule;
- validity, retry, logging, and analysis rules.

Before formal collection, we still need to:

1. approve the final task interfaces and consumer-facing copy;
2. select and freeze the exact agent/model and API version;
3. freeze sampling parameters, browser settings, step/time limits, dependencies, and repository commit;
4. run a non-formal end-to-end smoke test;
5. authorize and execute the 108 formal runs.

## 4. Planned execution after approval

1. **Freeze:** approve the 12 tasks, agent configuration, prompts, scorer, matrix, and rerun rules.
2. **Collect:** execute the randomized 108-run matrix with isolated browser state and complete artifacts.
3. **Audit:** verify warning exposure, run validity, scorer outputs, retries, and protocol deviations before examining aggregate claims.
4. **Analyze:** report the four C/S outcomes, condition contrasts, uncertainty, task heterogeneity, and supported trajectory diagnostics.
5. **Revise the paper:** insert audited results and update the Abstract, Results, Limitations, and Conclusion without broadening claims beyond the evidence.

## 5. Research after the primary study

The next studies should add one scientific factor at a time:

1. **Neutral-interface controls:** estimate whether deceptive choice architecture itself changes agent behavior.
2. **Cross-agent validation:** test whether unsafe completion and safeguard response depend on the model or scaffold.
3. **Warning wording and timing:** separate content, authority, visual persistence, and start-of-task versus risk-point delivery.
4. **Imperfect detection:** introduce missed, false, delayed, and poorly localized warnings.
5. **Broader tasks:** add longer trajectories, more consumer domains, and later enterprise settings while preserving deterministic scoring.
6. **Human calibration:** conduct a separately approved study before making human–agent or population-level claims.

## 6. Decisions requested from the mentor

- Confirm the revised primary design: one agent, 12 consumer tasks, three warning conditions, and 108 runs.
- Confirm that neutral interfaces and cross-agent comparison remain follow-up studies rather than part of the primary run.
- Approve the paper's scoped claim: the study evaluates safeguard response under curated deceptive interfaces, not the causal effect of deception or general superiority of System versus UI warnings.
- After interface review, approve the exact model/configuration freeze and formal-run authorization.
