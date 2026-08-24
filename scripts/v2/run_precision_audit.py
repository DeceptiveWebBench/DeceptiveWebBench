"""Write the Protocol v2 design-only precision audit."""

from __future__ import annotations

from src.utils.io import project_root, write_json
from analysis.v2_precision import precision_report


if __name__ == "__main__":
    destination = project_root() / "artifacts" / "v2" / "review" / "precision_sensitivity.json"
    write_json(destination, precision_report())
    print(destination)
