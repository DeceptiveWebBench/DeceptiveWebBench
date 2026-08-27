# Anonymous release scope

The anonymous artifact is the submission-facing code, protocol, and tabular-data package. The author may later mirror the reviewed package to other hosting services, but no identifiable organization or account is required by the manuscript.

## Included

- Protocol v2 websites, task registry, safeguards, scorer, runner, tests, and frozen configuration;
- canonical 108-cell matrix and manifests;
- released 108-row selected-cell data and 112-row attempt audit;
- aggregate analysis CSVs, publication figure/table generators, and manuscript source;
- append-only adjudication notice plus the byte-identical evidence bundle for the corrected cell;
- licenses, limitations, data dictionary, and clean reproduction instructions.

## Intentionally omitted

- credentials and local environment files;
- full provider prompts, responses, and raw screenshots;
- the ignored 140MB formal trace tree;
- API-backed smoke/debug logs and model-free fixture trees;
- private submission metadata, author identities, and account-specific upload configuration.

The omitted raw traces cannot be reconstructed from the released tabular data. The release-safe pipeline reproduces the full aggregation, tables, and programmatic figures without claiming otherwise.

## Local staging only

```bash
python dataset/build_hf_package_v2.py
```

This creates ignored local staging under `dataset/hf_staging_v2/`. Any later upload, repository identifier, or publication action is author-owned and must be supplied explicitly outside the anonymous package.
