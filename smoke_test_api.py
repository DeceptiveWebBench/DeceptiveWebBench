"""
Minimal Bedrock Converse check for the active model in configs/main_config.yaml.

Requires: boto3, PyYAML. Env: AWS_ACCESS_KEY_ID, AWS_API_KEY (secret), optional AWS_REGION.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    try:
        import boto3  # noqa: PLC0415
        import yaml  # noqa: PLC0415
    except ImportError as exc:
        print("Install boto3 and PyYAML:", exc)
        sys.exit(1)

    root = Path(__file__).resolve().parent
    cfg_path = root / "configs" / "main_config.yaml"
    with cfg_path.open(encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle) or {}
    model = cfg.get("model") or {}
    profiles = model.get("model_profiles") or {}
    active = str(model.get("active_model_profile") or "").strip() or next(iter(profiles.keys()), "")
    prof = profiles.get(active) if active else {}
    model_id = os.getenv("BEDROCK_TEST_MODEL_ID", str(prof.get("model_name") or "")).strip()
    region = os.getenv("AWS_REGION", str(prof.get("region_name") or "us-east-1")).strip()
    if not model_id:
        raise SystemExit("No model_name in config profile; set BEDROCK_TEST_MODEL_ID.")

    api_env = str(prof.get("api_key_env") or "AWS_API_KEY")
    secret = os.getenv(api_env)
    access_id = os.getenv("AWS_ACCESS_KEY_ID")
    if not secret or not access_id:
        raise SystemExit(f"Set AWS_ACCESS_KEY_ID and {api_env}.")

    client = boto3.client(
        "bedrock-runtime",
        region_name=region,
        aws_access_key_id=access_id,
        aws_secret_access_key=secret,
    )
    print(f"Testing Converse: model={model_id!r} region={region!r}")
    try:
        resp = client.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": "Reply with exactly: API works."}],
                }
            ],
            inferenceConfig={"maxTokens": 64, "temperature": 0.0},
        )
    except Exception as exc:  # noqa: BLE001
        print(type(exc).__name__)
        print(exc)
        sys.exit(1)

    block = (resp.get("output") or {}).get("message") or {}
    parts = block.get("content") or []
    text = ""
    for p in parts:
        if isinstance(p, dict) and "text" in p:
            text += str(p.get("text") or "")
    print("Success:")
    print(text.strip() or resp)


if __name__ == "__main__":
    main()
