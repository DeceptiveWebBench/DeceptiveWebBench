# Artifact verification log — Version 1 A--C

Date: 2026-08-05 (Asia/Shanghai)

## Local reproducibility

| Check | Command | Result |
|---|---|---|
| Frozen data, title, abstract, and 81-cell matrix | `./.venv/bin/python scripts/verify_analysis_freeze.py` | PASS |
| Aggregate counts, denominators, task table, uncertainty, failure decomposition, sensitivity, and manifest | `./.venv/bin/python -m analysis --input-csv logs/experiment_runs/results_run_level.csv --output-dir analysis/outputs --bootstrap-samples 10000 --seed 42` | PASS |
| Figure generation | `./.venv/bin/python analysis/generate_figures.py` | PASS |
| Current task/warning configuration contract | `./.venv/bin/python scripts/verify_warning_task_contract.py` | PASS |
| Clean-environment aggregation | `tmpv=$(mktemp -d /tmp/tc-clean-analysis.XXXXXX); python3 -m venv "$tmpv"; "$tmpv/bin/python" -m analysis --input-csv logs/experiment_runs/results_run_level.csv --output-dir "$tmpv/outputs" --bootstrap-samples 10000 --seed 42` | PASS; no package installation required |
| Local Hugging Face staging build | `./.venv/bin/python dataset/build_hf_package.py` | PASS; 81 scrubbed raw-run folders and versioned manifest included |
| PDF build | `cd paper && tectonic --outdir <clean-temp-dir> --keep-logs neurips_2026.tex` and the same for `supplement_v1_2026-08-09.tex` | PASS |
| Page limit | `pdfinfo paper/paper_v1_AC_2026-08-09.pdf`; text extraction locates Conclusion on page 5 and References on page 6 | PASS: 7 PDF pages total; main text ends on page 5 and References begins on page 6 |
| Supplement layout | `pdfinfo paper/supplement_v1_2026-08-09.pdf` | PASS: 4 pages |
| PDF metadata | `pdfinfo` on both final PDFs | PASS: no Author or Title metadata; Creator/Producer only |
| Visual QA | Render every page with `pdftoppm -png -r 120`, then inspect all 7 main-paper and all 4 supplement page images | PASS: no clipping, overlap, unreadable table, link boxes, or blank trailing page |
| Local delivery archives | `unzip -tq delivery/*.zip` and extracted-tree identity/credential scan | PASS: both archives are structurally valid; no author name, local user path, AWS key, or Hugging Face token was found. Code-level environment-variable names are retained, without values. |

Canonical CSV SHA-256: `c7095c1189b03cb672b888209d41d18853e3236360587455368cca440c851b07`.

## External anonymous access

| Resource | Logged-out result | Limitation / action |
|---|---|---|
| Anonymous repository: `https://anonymous.4open.science/r/DeceptiveWebBench-960E/` | PASS: content opened in the signed-out in-app browser; a Sign In control was visible | Remote content is stale and still uses the earlier Evaluations & Datasets framing. Owner synchronization is required. |
| Hugging Face dataset: `https://huggingface.co/datasets/deceptive-web-benchmark/execution-time-warnings-web-agents` | PARTIAL: page is public | The dataset currently reports as empty. Authorized upload and a second logged-out check are required. |

No external write, submission, publication, or account-authorized action was performed.

## Anonymity

Source and built artifacts are checked for author names, affiliations, local absolute paths, credentials, and identifying PDF metadata during final verification. Private coordination fields are not included in the anonymous paper or supplement.

Final PDF SHA-256 values:

- Main: `42c9102d2905ab0d1469ca700dd86b92a7a36323429a1b4c0fc8825c7b2bb6b5`
- Supplement: `fa96803505972b82339feb7e6eb7913f37191d9550bd144d48366530a0e9e1c0`
