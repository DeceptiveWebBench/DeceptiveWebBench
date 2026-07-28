# Frozen analysis summaries

These CSV/Markdown files are **frozen paper-facing aggregates** from the formal run set (81 merged run-level rows). They ship on GitHub so reviewers can inspect headline rates without downloading Hugging Face artifacts.

Regenerate from merged logs (local only):

```bash
python -m analysis
```

Raw per-run logs stay under `logs/` (gitignored) and are released via Hugging Face when applicable.
