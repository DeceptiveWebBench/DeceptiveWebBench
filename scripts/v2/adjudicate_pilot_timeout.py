"""Apply the one documented structured-timeout adjudication without an API call."""

from __future__ import annotations

import json

from src.v2.pilot import PILOT_ROOT, adjudicate_llm_timeout, validate_adjudication


SCHEDULED_RUN_ID = "v2__interface_location_access_003__system_warning__r3"


if __name__ == "__main__":
    attempt = PILOT_ROOT / "runs" / SCHEDULED_RUN_ID / "attempt_1"
    record = adjudicate_llm_timeout(attempt)
    validate_adjudication(attempt)
    print(json.dumps(record, indent=2, sort_keys=True))
