# Termination and failure analysis

Termination causes are assigned only from structured events; free-text reasoning was not used.

| Termination class | Count |
|---|---|
| deliberate_safe_abort | 1 |
| timeout_or_step_limit | 6 |
| unclassified_agent_stop | 9 |

| Condition | Non-completions | Structured decomposition |
|---|---|---|
| No safeguard | 2 | timeout_or_step_limit=1, unclassified_agent_stop=1 |
| System-delivered | 6 | deliberate_safe_abort=1, timeout_or_step_limit=2, unclassified_agent_stop=3 |
| Interface-delivered | 8 | timeout_or_step_limit=3, unclassified_agent_stop=5 |

There were 16 valid non-completions: 9 ordinary/unclassified stops, 6 timeouts or step-limit terminations, and 1 deliberate safe abort. No structured human-confirmation or evidenced grounding/navigation termination was recorded.

The main mechanism is therefore not a clean shift toward deliberate safe refusal. Some safety gains arise because the agent did not finish, often through an ordinary stop or timeout. This supports a safety–completion trade-off interpretation and does not establish improved risk reasoning.

## Attempt accounting and adjudication

The collection contains 5 attempts originally labeled invalid. Four retry-eligible infrastructure failures produced valid retries. The remaining malformed-action attempt was not rerun; it was append-only adjudicated as a valid safe non-completion under the frozen outcome specification. Original classifications and cost evidence remain in the attempt audit.
