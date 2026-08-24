"""Resolve which local benchmark site renders a given Protocol v2 task.

The four ShopLane tasks use the shared ShopLane storefront. The remaining
eight tasks are routed across four scenario-appropriate consumer sites. This
module is the single source of truth for those mappings so tests and review
artifact generation stay in sync.
"""

from __future__ import annotations

# Tasks that render inside env/v2/sites/shoplane/ (the realistic storefront).
SHOPLANE_TASKS: frozenset[str] = frozenset(
    {
        "forced_action_sub_001",
        "sneaking_pay_001",
        "sneaking_gift_wrap_003",
        "interface_perm_001",
    }
)

SHOPLANE_INDEX = "env/v2/sites/shoplane/index.html"
SCENARIO_SITE_INDEXES: dict[str, str] = {
    "forced_account_gate_002": "env/v2/sites/journey/index.html",
    "sneaking_travel_bundle_004": "env/v2/sites/journey/index.html",
    "forced_contact_share_003": "env/v2/sites/events/index.html",
    "interface_confirmshame_newsletter_002": "env/v2/sites/events/index.html",
    "forced_identity_upload_004": "env/v2/sites/local-services/index.html",
    "interface_location_access_003": "env/v2/sites/local-services/index.html",
    "sneaking_trial_renewal_002": "env/v2/sites/digital/index.html",
    "interface_contact_import_004": "env/v2/sites/digital/index.html",
}


def is_shoplane_task(task_id: str) -> bool:
    return task_id in SHOPLANE_TASKS


def site_index_path(task_id: str) -> str:
    """Return the repo-relative index.html that renders ``task_id``."""
    if is_shoplane_task(task_id):
        return SHOPLANE_INDEX
    try:
        return SCENARIO_SITE_INDEXES[task_id]
    except KeyError as exc:
        raise KeyError(f"No Protocol v2 site is registered for {task_id!r}") from exc
