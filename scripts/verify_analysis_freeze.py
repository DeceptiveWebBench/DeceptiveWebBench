"""Read-only gate for the frozen pilot analysis and protected paper front matter."""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.aggregate_results import validate_run_matrix


EXPECTED_TITLE = "Trustworthy Completion for Web Agents: A Benchmark and Research Agenda for Execution-Time Safeguards"
EXPECTED_CSV_SHA256 = "c7095c1189b03cb672b888209d41d18853e3236360587455368cca440c851b07"
EXPECTED_ABSTRACT_SHA256 = "96e628ec31ddcc7fba25e56a8a601babcde390614f448b376ba9efc0efb25875"


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
    print("PASS: protected title and abstract unchanged")
    print(f"PASS: canonical CSV SHA-256 {digest}")
    print("PASS: 9 tasks x 3 conditions x 3 repeats = 81 complete unique cells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
