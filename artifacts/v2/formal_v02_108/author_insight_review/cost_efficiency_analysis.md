# Cost and efficiency analysis

Cost is operational metadata and does not affect C/S scoring or validity.

| Condition | Valid / cost-known | Median cost | Median tokens | Median calls | Median wall time |
|---|---|---|---|---|---|
| No safeguard | 36/35 | USD 0.0536 | 86,648 | 7.5 | 99.5s |
| System-delivered | 36/36 | USD 0.0537 | 86,940 | 7.5 | 88.4s |
| Interface-delivered | 36/36 | USD 0.0555 | 92,636 | 8.0 | 103.8s |

Across all 112 attempts, known cost is USD 7.51396168; 3 attempts have unknown cost, giving the preregistered conservative exposure of USD 10.51396168 when each unknown attempt is counted as USD 1. Known invalid/retry overhead is USD 0.04736343. Recorded usage totals 1031 model calls and 12,383,360 tokens.

Condition differences in tokens, calls, latency, or cost are descriptive and partly reflect trajectory length and completion behavior. They do not identify a causal compute cost of the warning channel. This analysis belongs in the supplement.
