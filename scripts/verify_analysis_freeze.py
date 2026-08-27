"""Read-only gate for historical v1 data and the selected v2 front matter."""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.aggregate_results import validate_run_matrix


EXPECTED_TITLE = "Beyond Endpoint Success: Trustworthy Completion for Web Agents"
EXPECTED_CSV_SHA256 = "c7095c1189b03cb672b888209d41d18853e3236360587455368cca440c851b07"
EXPECTED_ABSTRACT_SHA256 = "4c1f28651e85ec7d39bc18bded506732e3bec965c5a86ecdc5c6d86a5734de74"


def main() -> int:
    root = ROOT
    csv_path = root / "logs/experiment_runs/results_run_level.csv"
    tex_path = root / "paper/neurips_2026.tex"
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8", newline="")))
    audit = validate_run_matrix(rows)
    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    tex = tex_path.read_text(encoding="utf-8")
    if f"\\title{{{EXPECTED_TITLE}}}" not in tex:
        raise SystemExit("FAIL: paper title differs from the protected title")
    if "\\begin{abstract}" not in tex or "\\end{abstract}" not in tex:
        raise SystemExit("FAIL: paper abstract block is missing")
    abstract = tex.split("\\begin{abstract}", 1)[1].split("\\end{abstract}", 1)[0]
    if digest != EXPECTED_CSV_SHA256:
        raise SystemExit(f"FAIL: canonical run CSV SHA-256 changed: {digest}")
    if hashlib.sha256(abstract.encode("utf-8")).hexdigest() != EXPECTED_ABSTRACT_SHA256:
        raise SystemExit("FAIL: paper abstract differs from the frozen abstract")
    if not audit["is_complete_unique"]:
        raise SystemExit(f"FAIL: run matrix invalid: {audit}")
    print("PASS: selected publication title and frozen abstract verified")
    print(f"PASS: canonical CSV SHA-256 {digest}")
    print("PASS: preserved historical v1 matrix has 9 tasks x 3 conditions x 3 repeats = 81 complete unique cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
