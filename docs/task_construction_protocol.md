# Task-construction protocol

This protocol instantiates Revision Guide A3 and is the artifact-facing counterpart of the manuscript's Benchmark Construction section.

1. Specify a benign nominal goal and the acting principal.
2. Construct a synthetic interface with a safe and unsafe route to a comparable nominal endpoint.
3. Map the unsafe route to a documented deceptive-interface family and record the concrete low-level implementation.
4. Identify the exact risk point and define the machine-verifiable unsafe action.
5. Define the safe alternative and deterministic terminal-state fields for safe completion, unsafe completion, and safe abort.
6. Annotate the affected stakeholder, protected interest, potential non-numerical consequence, qualitative reversibility, and expected safeguard response.
7. Verify that the risk control is perceptible and actionable at the fixed viewport or documented interaction point.
8. Exclude any task requiring a live account, payment endpoint, sensitive personal data, or a judgment-only scorer.
9. Validate task/warning configuration with `./.venv/bin/python scripts/verify_warning_task_contract.py`.
10. Freeze task identifiers, conditions, repeats, model/scaffold configuration, and analysis plan before formal collection.

The current nine tasks satisfy the seven inclusion criteria in `docs/benchmark_card.md`. New tasks must undergo the same metadata, deterministic-scoring, and provenance checks before being pooled with benchmark results.
