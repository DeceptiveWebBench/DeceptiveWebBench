# Benchmark card — Trustworthy Completion for Web Agents

## Purpose and scope

This synthetic local benchmark tests whether a delegated web agent reaches a nominal goal without taking a task-annotated unsafe path. It is designed for auditable safeguard evaluation, not for measuring population harm, exhaustive dark-pattern coverage, or production detector quality.

Research question (Revision Guide, verbatim):

> How should web agents be evaluated when nominal task completion may compromise the user’s financial interests, privacy, informed consent, autonomy, or policy constraints - and how can execution-time safeguards be tested without conflating warning design, risk detection, and agent capability?

## Benchmark unit and inclusion protocol

Each task is represented as `T=(G,E,D,R,A_safe,A_unsafe,S,H)`: nominal goal, interface/trajectory, deceptive family and implementation, risk point, safe path, unsafe path, deterministic terminal-state specification, and protected interest/potential harm.

A task is included only if: (1) a safe route exists; (2) safe and unsafe paths reach comparable nominal endpoints; (3) the unsafe path represents a concrete financial, privacy, consent, autonomy, or policy consequence; (4) the risk control is perceptible and actionable at the fixed viewport or documented interaction point; (5) both outcomes are deterministically verifiable; (6) the task maps to a documented deceptive-interface category; and (7) no real account, payment endpoint, or sensitive personal data is used.

## Contents

- Two local synthetic sandboxes: ShopLane (six tasks) and WorkHub Admin (three tasks).
- Nine short-horizon tasks: three forced-action, three sneaking, and three interface-interference instances.
- Eight qualitative stakeholder/harm fields per task: acting principal, affected stakeholder, protected interest, unsafe action, potential consequence, safe alternative, reversibility, and expected safeguard response.
- Three conditions: No Warning, System Warning, and UI Warning.
- Four deterministic outcomes: safe completion, unsafe completion, safe abort, and other failure.

## Completed pilot

The frozen pilot contains 81 unique cells (9 tasks × 3 conditions × 3 repeats) for BrowserUse with Amazon Nova Lite v1. Outcome rates use explicit denominators: the first three outcomes use scorable runs; other failure uses all runs. Uncertainty uses 10,000 task-cluster bootstrap replicates with seed 42. The canonical CSV SHA-256 is `c7095c1189b03cb672b888209d41d18853e3236360587455368cca440c851b07`.

The current `interface_perm_001` task and UI warning concern non-essential cookie acceptance. The formal pilot System-warning artifact used the more abstract phrase “an unnecessary permission grant.” All 81 runs remain primary; a labeled 72-run sensitivity view excludes the task's nine cells. No run artifact is rewritten.

## Intended and out-of-scope uses

Intended uses include testing deterministic safe-path scoring, auditing execution-time safeguard delivery, and comparing agent response in a controlled sandbox. Out-of-scope uses include claims of comprehensive deceptive-pattern coverage, numerical harm severity, real-world prevalence, human vulnerability, causal population impact, and production deployment readiness.

## Reproduction and release

Run-level provenance is in `analysis/outputs/run_manifest_v1.csv`. Exact analysis commands and environment expectations are in `docs/reproducibility.md`; historical external-access status is in `docs/archive/v1/artifact_verification_log.md`. D, E, detector, scale, and human studies are Research Agenda items and are not included as completed evidence.
