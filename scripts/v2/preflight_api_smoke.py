"""Static and opt-in credential-presence preflight; never prints credential values."""

from __future__ import annotations

import argparse
import os

from src.v2.runtime_config import load_runtime_config


REQUIRED_CREDENTIAL_NAMES = ("AWS_BEARER_TOKEN_BEDROCK",)
OPTIONAL_CREDENTIAL_NAMES: tuple[str, ...] = ()


def credential_presence(env: dict[str, str]) -> dict[str, bool]:
    return {name: bool(env.get(name)) for name in (*REQUIRED_CREDENTIAL_NAMES, *OPTIONAL_CREDENTIAL_NAMES)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--author-confirmed", action="store_true")
    parser.add_argument("--check-credential-presence", action="store_true")
    args = parser.parse_args()
    runtime = load_runtime_config()
    print(f"Static runtime valid: {runtime.raw['runtime_config_version']}")
    print("No network request was made.")
    if not args.check_credential_presence:
        print("Credential environment was not inspected.")
        return 0
    if not args.author_confirmed:
        print("Credential-presence check blocked: --author-confirmed is required.")
        return 2
    status = credential_presence(dict(os.environ))
    for name, present in status.items():
        print(f"{name}: {'present' if present else 'missing'}")
    return 0 if all(status[name] for name in REQUIRED_CREDENTIAL_NAMES) else 3


if __name__ == "__main__":
    raise SystemExit(main())
