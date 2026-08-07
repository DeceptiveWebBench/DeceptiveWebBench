# Decision log

Historical **changelog** for Version 1 infrastructure, layout, and tooling. The corresponding design, conditions, warnings, and scoring invariants live in **`docs/archive/v1/experiment_protocol.md`**; runtime numbers in **`configs/main_config.yaml`**.

## Frozen summary

- Single agent (BrowserUse + one multimodal API profile). Three conditions: `no_warning`, `system_warning`, `ui_warning`. Three pattern families: `forced_action`, `sneaking`, `interface_interference` (see `src/env/static/js/sandbox_state.js` `TASK_DEFS`).
- Manipulated factor: **warning channel / placement**; system and UI use the same template (`configs/warnings.yaml`). Do not treat wording strength as the variable.
- Primary reported outcome: **unsafe completion**; prefer deterministic, state-based scoring; manual review for ambiguous cases.

## Changelog

| Date | Change |
|------|--------|
| 2026-04-23 | Terminal state: `terminal_state.json` from `localStorage` for scoring; `prompt_builder.py` as single instruction assembly; `verify_warning_task_contract.py`; `verify_forced_action_terminal_path.py`. Step/token limits tightened—**current caps in `main_config.yaml`**. |
| 2026-04-24 | Early provider experiments; **frozen runs use Bedrock Nova Lite** (`main_config.yaml`). |
| 2026-04-27 | Site: static placeholder in `#page-content` to reduce first-step blank-page waits; prompt: avoid long idle waits. Single-task smoke manifest `configs/manifests/smoke.yaml`. Step / LLM timeouts aligned (see `main_config.yaml`). |
| 2026-04-27 | Tasks: added `forced_account_gate_002`, `sneaking_trial_renewal_002`, `interface_confirmshame_newsletter_002`. WorkHub shell: `enterprise_*` tasks, `configs/manifests/enterprise.yaml`. |
| 2026-05-01 | WorkHub UI refresh (CSS/JS only); task YAML, warnings, scoring keys unchanged. |
| 2026-05-06 | Removed legacy standalone HTML under `env/tasks/*/`<br>(kept `task.yaml`). |
| 2026-05-07 | **Analysis:** `python -m analysis` merges formal run trees, dedupes, `results_run_level.csv` + `analysis/outputs/*`; manifest `repeat_indices`; scorable-rate denominators. **Docs:** LaTeX only under **`paper/`**; **`AGENTS.md` removed** (rules → **`README.md`**); slim auxiliary docs; this file = changelog table. |
| 2026-05-07 | **Model stack:** Removed Qwen/DashScope `model_profiles`; **Amazon Nova Lite on Bedrock only**; `scripts/smoke_test_api.py` → Bedrock Converse check. |
| 2026-07-28 | Repo layout for release: manifests → `configs/manifests/`; Croissant → `dataset/metadata/croissant.json`; smoke API → `scripts/`; docs `release.md` / `reproducibility.md`. |

For historical Version 1 changes, update **`docs/archive/v1/experiment_protocol.md`**, **`analysis/stats_plan.md`** if reporting changes, and preserve the decision here. New-study decisions belong in the Protocol v2 documentation.
