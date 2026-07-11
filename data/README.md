# Data Policy

`input.zip` at the repository root is the single canonical raw competition artifact.
Do not copy it into `data/raw/`.

Use `data/external/` for approved external datasets with provenance, `data/synthetic/` for reproducible generated examples, and `data/processed/` for rebuildable derived data.
Never commit patient data or mutate canonical raw text.
