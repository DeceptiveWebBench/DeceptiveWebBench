# Statistical analysis report

## Denominators and four-quadrant outcomes

Primary rates use every valid scheduled run, not a post-hoc ‘scorable’ subset. After the protocol-consistency adjudication, all three conditions have 36 valid outcomes.

| Condition | Scheduled/valid/unavailable | TC | Unsafe completion | Safe non-completion | Unsafe failure | C | S |
|---|---|---|---|---|---|---|---|
| No safeguard | 36/36/0 | 7/36 (19.4%) | 27/36 (75.0%) | 2/36 (5.6%) | 0/36 (0.0%) | 34/36 (94.4%) | 9/36 (25.0%) |
| System-delivered | 36/36/0 | 10/36 (27.8%) | 20/36 (55.6%) | 5/36 (13.9%) | 1/36 (2.8%) | 30/36 (83.3%) | 15/36 (41.7%) |
| Interface-delivered | 36/36/0 | 10/36 (27.8%) | 18/36 (50.0%) | 5/36 (13.9%) | 3/36 (8.3%) | 28/36 (77.8%) | 15/36 (41.7%) |

No safeguard produced high nominal completion (94.4%) but low safety (25.0%): unsafe completion was the modal result (27/36, 75.0%). This is the clearest evidence that task capability and trustworthy completion diverge in this suite.

## Prespecified contrasts and uncertainty

| Contrast | Metric | Estimate | 95% task-cluster bootstrap interval |
|---|---|---|---|
| system − no | S | +16.7 pp | [+2.8 pp, +33.3 pp] |
| system − no | C | -11.1 pp | [-22.2 pp, +0.0 pp] |
| system − no | TC | +8.3 pp | [+0.0 pp, +16.7 pp] |
| ui − no | S | +16.7 pp | [+0.0 pp, +38.9 pp] |
| ui − no | C | -16.7 pp | [-30.6 pp, -5.6 pp] |
| ui − no | TC | +8.3 pp | [-8.3 pp, +30.6 pp] |
| ui − system | S | +0.0 pp | [-22.2 pp, +19.4 pp] |
| ui − system | C | -5.6 pp | [-22.2 pp, +11.1 pp] |
| ui − system | TC | +0.0 pp | [-16.7 pp, +16.7 pp] |

The safeguards increased safety descriptively by 16.7 percentage points, but nominal completion fell by 11.1 points under System delivery and 16.7 points under Interface delivery. Consequently, trustworthy-completion gains were 8.3 points for both strategies. The direct Interface−System estimates remain small with wide intervals; the data do not distinguish the two complete delivery strategies.

## Paired mechanisms

Among paired task-repeat cells, unsafe No-safeguard completion changed to trustworthy completion in 2/36 System pairs and 4/36 Interface pairs. Completion loss occurred in 6 and 7 pairs, respectively. Thus, the average safety gain cannot be described as uniformly finding a safe alternative route.

## Protocol-consistency adjudication

The previously unavailable Interface cell is now a valid safe non-completion under the frozen malformed-action rule. Its C/S assignment was observable from the preserved state and lies within the previously reported worst/best bounds. The correction strengthens the completion-loss component but does not change the headline qualitative findings.

## Stability and post-hoc sensitivity

Leave-one-task-out (LOTO) is explicitly post-hoc and diagnostic, not a replacement for the prespecified full-suite analysis. Ranges:

- system_warning_minus_no_warning: S +12.1 pp to +18.2 pp; C -15.2 pp to -9.1 pp; TC +6.1 pp to +9.1 pp.
- ui_warning_minus_no_warning: S +9.1 pp to +21.2 pp; C -18.2 pp to -12.1 pp; TC +0.0 pp to +12.1 pp.

The broad directions—safety up and completion down—persist across LOTO checks, but trustworthy-completion gains are task-sensitive and should not be presented as a universal effect.

## Scope

These estimates apply to one frozen Qwen web-agent configuration on 12 curated deceptive-interface sandbox tasks. They do not identify a deception-versus-neutral causal effect, detector performance, a pure channel effect, cross-agent generalization, live-site behavior, human behavior, or downstream harm severity.
