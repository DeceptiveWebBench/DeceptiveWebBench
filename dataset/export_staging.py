"""Export merged run-level CSV to JSONL (+ CSV copy) for Hugging Face upload. No pandas required."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INPUT = "logs/experiment_runs/results_run_level.csv"
DEFAULT_OUTDIR = "dataset/hf_staging"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-csv", default=DEFAULT_INPUT)
    p.add_argument("--output-dir", default=DEFAULT_OUTDIR)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = _REPO_ROOT
    src = Path(args.input_csv)
    if not src.is_absolute():
        src = root / src
    if not src.exists():
        print(f"Missing {src}; run: python -m analysis")
        return 1

    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    with src.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    jl = out_dir / "run_level.jsonl"
    csv_copy = out_dir / "run_level.csv"
    with jl.open("w", encoding="utf-8") as jout:
        for row in rows:
            jout.write(json.dumps(row, ensure_ascii=False) + "\n")
    with csv_copy.open("w", encoding="utf-8", newline="") as cout:
        if rows:
            w = csv.DictWriter(cout, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    try:
        import pandas as pd

        pd.DataFrame(rows).to_parquet(out_dir / "run_level.parquet", index=False)
        pq_ok = True
    except Exception as exc:
        pq_ok = False
        print(f"No Parquet ({exc}); optional: pip install pandas pyarrow")

    try:
        source_rel = str(src.relative_to(root))
    except ValueError:
        source_rel = str(src)
    meta = {
        "schema_version": "1",
        "source_csv": source_rel,
        "n_rows": len(rows),
        "columns": list(rows[0].keys()) if rows else [],
        "parquet_written": pq_ok,
    }
    (out_dir / "export_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {jl}")
    print(f"Wrote {csv_copy}")
    if pq_ok:
        print(f"Wrote {out_dir / 'run_level.parquet'}")
    print(f"Wrote {out_dir / 'export_meta.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
