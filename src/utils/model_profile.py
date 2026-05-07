from __future__ import annotations

from typing import Any


def resolve_model_profile(config: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    Resolve active model profile from config.

    Returns:
      (profile_name, profile_dict)

    Backward compatibility:
    - If model_profiles is absent, return ("legacy", model_cfg).
    - If active_model_profile is absent but model_profiles exists, default to the first profile key
      in YAML insertion order.
    """
    model_cfg = config.get("model", {}) if isinstance(config, dict) else {}
    profiles = model_cfg.get("model_profiles")
    if not isinstance(profiles, dict) or not profiles:
        return "legacy", dict(model_cfg)

    active = str(model_cfg.get("active_model_profile") or "").strip()
    if not active:
        active = next(iter(profiles.keys()))

    if active not in profiles:
        raise RuntimeError(
            f"Unknown model.active_model_profile={active!r}; available profiles: {sorted(profiles.keys())}"
        )

    profile = profiles.get(active)
    if not isinstance(profile, dict):
        raise RuntimeError(f"Model profile {active!r} must be a mapping in configs/main_config.yaml")
    return active, dict(profile)
