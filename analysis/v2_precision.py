"""Design-only precision simulation; never consumes benchmark outcomes."""

from __future__ import annotations

import math
import random
from statistics import mean, pstdev
from typing import Any


SIMULATION_SEED = 20260816
SIMULATIONS = 20_000


def simulate_repeat_precision(repeats: int, *, simulations: int = SIMULATIONS) -> dict[str, Any]:
    rng = random.Random(SIMULATION_SEED + repeats)
    paired_differences: list[float] = []
    for _ in range(simulations):
        task_differences = []
        for _task in range(12):
            # Null design check: both conditions share an unobserved task propensity.
            propensity = rng.betavariate(2, 2)
            a = sum(rng.random() < propensity for _ in range(repeats)) / repeats
            b = sum(rng.random() < propensity for _ in range(repeats)) / repeats
            task_differences.append(a - b)
        paired_differences.append(mean(task_differences))
    return {
        "tasks": 12,
        "repeats_per_task_condition": repeats,
        "scheduled_runs_for_three_conditions": 12 * repeats * 3,
        "task_condition_rate_granularity": 1 / repeats,
        "condition_rate_granularity": 1 / (12 * repeats),
        "null_paired_contrast_monte_carlo_sd": pstdev(paired_differences),
        "null_paired_contrast_central_95_width": (
            sorted(paired_differences)[int(simulations * 0.975)]
            - sorted(paired_differences)[int(simulations * 0.025)]
        ),
    }


def precision_report() -> dict[str, Any]:
    three = simulate_repeat_precision(3)
    five = simulate_repeat_precision(5)
    return {
        "status": "synthetic_design_only_not_treatment_evidence",
        "seed": SIMULATION_SEED,
        "simulations": SIMULATIONS,
        "assumption": (
            "Null paired conditions with heterogeneous beta(2,2) task propensities; "
            "used only to compare measurement granularity."
        ),
        "three_repeats": three,
        "five_repeats": five,
        "sd_ratio_five_over_three": (
            five["null_paired_contrast_monte_carlo_sd"]
            / three["null_paired_contrast_monte_carlo_sd"]
        ),
        "cluster_warning": (
            "Only 12 task identities are available. Task-cluster bootstrap intervals may be "
            "coarse and unstable; raw task profiles and paired task contrasts remain essential."
        ),
        "author_decision": (
            "Keep the frozen 108-cell/three-repeat design unless the author changes it before "
            "any API-backed smoke or formal collection. Five repeats would require 180 cells."
        ),
    }

