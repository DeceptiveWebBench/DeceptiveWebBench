"""Write a null-only supplement cost-reporting template before real collection."""

from __future__ import annotations

from src.utils.io import project_root, write_json


def main() -> None:
    template = {
        "status": "template_only_no_api_data",
        "formal_run": False,
        "synthetic_fixture": False,
        "treatment_or_cost_results_available": False,
        "total_experiment_api_cost": None,
        "per_valid_run_cost": {"mean": None, "median": None, "q1": None, "q3": None, "iqr": None, "min": None, "max": None},
        "by_condition": {
            condition: {"median_cost": None, "median_tokens": None, "median_calls": None, "median_latency_seconds": None}
            for condition in ("no_warning", "system_warning", "ui_warning")
        },
        "descriptive_cost_differences": {
            "system_warning_minus_no_warning": None,
            "ui_warning_minus_no_warning": None,
        },
        "infrastructure_invalid_and_retry_cost": None,
        "cost_per_trustworthy_completion": None,
        "formal_budget_projection_rule": "projected valid-run cost + projected retry overhead + 25% contingency",
    }
    write_json(project_root() / "artifacts/v2/review/cost_reporting_template.json", template)
    print("Wrote null-only cost reporting template")


if __name__ == "__main__":
    main()
