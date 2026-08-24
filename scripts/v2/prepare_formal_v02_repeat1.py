"""Materialize the exact scoped authorization and pre-API freeze records."""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from src.utils.io import project_root, write_json
from src.v2.formal_repeat1_v02 import (
    AUTHORIZATION_PATH,
    authorization_template,
    frozen_hashes,
    repeat1_cells,
    tranche_hash,
)
from src.v2.pilot import verify_frozen_manifest
from src.v2.safeguards_v02 import EXPECTED_PAYLOAD, warning_config_path


def tree_hash(root: Path) -> tuple[str, int]:
    digest = hashlib.sha256(); count = 0
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode()); digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest()); count += 1
    return digest.hexdigest(), count


def main() -> int:
    verify_frozen_manifest()
    root = project_root()
    auth = authorization_template()
    AUTHORIZATION_PATH.write_text(yaml.safe_dump(auth, sort_keys=False), encoding="utf-8")
    paper_hash, paper_count = tree_hash(root / "paper")
    archive_hash, archive_count = tree_hash(root / "docs/archive")
    write_json(root / "artifacts/v2/review/v02_repeat1_protected_baseline.json", {
        "v01_manifest_verified": True,
        "v01_warning_sha256": hashlib.sha256((root / "configs/v2/warnings.yaml").read_bytes()).hexdigest(),
        "v02_warning_config_sha256": hashlib.sha256(warning_config_path().read_bytes()).hexdigest(),
        "v02_payload_sha256": hashlib.sha256(EXPECTED_PAYLOAD.encode("utf-8")).hexdigest(),
        "paper_tree_sha256": paper_hash,
        "paper_file_count": paper_count,
        "archive_tree_sha256": archive_hash,
        "archive_file_count": archive_count,
        "repeat1_cell_count": len(repeat1_cells()),
        "repeat1_tranche_sha256": tranche_hash(),
        "frozen_hashes": frozen_hashes(),
    })
    print(f"prepared {len(repeat1_cells())} cells; tranche={tranche_hash()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
