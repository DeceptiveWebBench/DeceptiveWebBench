"""Apply the exact provider Internal Server Error invalidity adjudication once."""

from __future__ import annotations

import json

from src.v2.pilot import PILOT_ROOT, adjudicate_model_internal_server_error, validate_adjudication


if __name__ == "__main__":
    attempt = (
        PILOT_ROOT
        / "runs/v2__interface_confirmshame_newsletter_002__ui_warning__r3/attempt_1"
    )
    record = adjudicate_model_internal_server_error(attempt)
    validate_adjudication(attempt)
    print(json.dumps(record, indent=2, sort_keys=True))
