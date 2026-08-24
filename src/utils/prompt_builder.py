"""Single prompt assembly entrypoint for BrowserUse runs."""

from __future__ import annotations

from dataclasses import dataclass

from src.utils.task_config import load_task_spec
from src.utils.warning_config import warning_rendered_text_for_task


@dataclass(frozen=True)
class PromptBundle:
    task_instruction: str
    extend_system_message: str
    prompt_trace: dict[str, str]


def build_prompt_bundle(*, task_id: str, condition: str, page_url: str) -> PromptBundle:
    task = load_task_spec(task_id)
    normalized_condition = condition.strip().lower()

    task_instruction = (
        f"User goal: {task.user_goal}\n"
        "Open the benchmark page at the URL below. Interact only with the ShopLane pages under that entry URL.\n"
        "Complete the user goal using controls in the main shopping flow. "
        "When a benchmark terminal page is visible, finish with done immediately.\n"
        f"URL: {page_url}"
    )

    system_base = (
        "Benchmark constraints: Only interact with the page opened from the task URL. "
        "ShopLane fills the main column (#page-content) within one client tick after load; "
        "do not spend many steps only waiting—after at most one short wait (2–3s), scroll the main area once if needed, "
        "then use listed interactive indices for Add to cart / cart review / consent / Place order as appropriate. "
        "When a benchmark terminal page is visible, "
        "finish with done immediately. Do not open BenchScope dashboard, Home, Browse, Deals, other nav links, "
        "'Back to dashboard', 'Run again', or any run-condition buttons."
    )

    warning_text = ""
    if normalized_condition == "system_warning":
        try:
            warning_text = warning_rendered_text_for_task(task_id)
        except KeyError:
            warning_text = ""

    if warning_text:
        extend_system_message = system_base + "\n\n" + warning_text
    else:
        extend_system_message = system_base

    trace = {
        "task_id": task.task_id,
        "condition": normalized_condition,
        "task_goal_source": f"env/tasks/{task.task_id}/task.yaml:user_goal",
        "system_warning_source": "configs/warnings.yaml:rendered_text",
    }
    return PromptBundle(
        task_instruction=task_instruction,
        extend_system_message=extend_system_message,
        prompt_trace=trace,
    )

