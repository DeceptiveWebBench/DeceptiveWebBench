"""Apply the documented ShopLane endpoint-overwrite adjudications offline."""

from __future__ import annotations

import json

from src.v2.pilot import (
    PILOT_ROOT,
    adjudicate_shoplane_endpoint_overwrite,
    validate_adjudication,
)


SCHEDULED_RUN_IDS = (
    "v2__sneaking_pay_001__no_warning__r1",
    "v2__sneaking_pay_001__system_warning__r2",
    "v2__sneaking_pay_001__ui_warning__r3",
)


if __name__ == "__main__":
    records = []
    for scheduled_run_id in SCHEDULED_RUN_IDS:
        attempt = PILOT_ROOT / "runs" / scheduled_run_id / "attempt_1"
        records.append(
            {
                "scheduled_run_id": scheduled_run_id,
                "record": adjudicate_shoplane_endpoint_overwrite(attempt),
            }
        )
        validate_adjudication(attempt)
    print(json.dumps(records, indent=2, sort_keys=True))
