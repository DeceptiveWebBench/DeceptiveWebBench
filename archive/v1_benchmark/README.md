# Version 1 benchmark (historical)

Version 1 contains **9 tasks** and the frozen **81-run** pilot used for the August 9, 2026 paper package.

## Current paths (not relocated yet)

| Path | Role |
|------|------|
| `env/site/` | Historical ShopLane / WorkHub HTML shells |
| `env/dashboard/` | Historical Version 1 BenchScope dashboard |
| `env/tasks/` | Per-task `task.yaml` for the 9-task suite |
| `src/env/static/` | CSS/JS served by the Version 1 sandbox pages |
| `configs/`, `configs/manifests/` | Frozen agent config, warnings, run manifests |
| `src/` runner / scorer / agent | Version 1 execution path |
| `logs/`, `analysis/outputs/` | 81-run logs and frozen analysis outputs |

These paths remain in place so paper artifacts and the 81-run reproduction path stay intact.

## Archival policy

Physical relocation into this archive directory happens **only after** the Version 1 delivery is frozen and an explicit archival phase is approved. This Phase 1 note does **not** duplicate the old benchmark tree.

## Entry policy

New experiments must **not** use the Version 1 website (`env/dashboard/`, `env/site/`) as the default entry. The current development entry is Protocol v2 ShopLane: `env/index.html` → `env/v2/sites/shoplane/`.
