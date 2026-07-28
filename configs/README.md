# Configs

| File | Role |
|------|------|
| `main_config.yaml` | Frozen agent / model / browser settings |
| `warnings.yaml` | Warning template + per-task risk slots |
| `task_index.yaml` | Task inventory (id, pattern family, start page) |
| `manifests/` | Batch run grids (see below) |

## Manifests

| Manifest | Use |
|----------|-----|
| `manifests/formal.yaml` | Full 9-task formal grid (default for `run_experiment`) |
| `manifests/shoplane.yaml` | ShopLane tasks only |
| `manifests/enterprise.yaml` | WorkHub / enterprise tasks only |
| `manifests/smoke.yaml` | Single task × condition developer smoke |
| `manifests/archive/` | One-off / pattern-scoped / retry manifests (kept for provenance) |

```bash
python -m src.runner.run_experiment --manifest configs/manifests/shoplane.yaml
```
