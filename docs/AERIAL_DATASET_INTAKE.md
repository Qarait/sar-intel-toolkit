# Aerial Dataset Intake

The detector is still the pre-fine-tune baseline until a candidate model passes the fine-tune report gate. This file tracks the external aerial-person datasets that can close that gap.

## Audit external datasets

Datasets are not committed to this repository. Keep raw data local, review license/access terms, then audit the local layout:

```bash
python scripts/audit_aerial_datasets.py \
  --dataset-root heridal=/data/HERIDAL \
  --dataset-root seadronessee=/data/SeaDronesSee \
  --dataset-root visdrone-person=/data/visdrone_person \
  --output output/aerial_dataset_audit.json
```

A dataset marked `ready_for_converter` has the expected top-level paths for a converter. That does not mean it is validated, licensed for redistribution, or sufficient for a recall claim.

## Priority

1. HERIDAL: closest wilderness/mountain SAR fit.
2. SeaDronesSee: maritime SAR-relevant imagery.
3. VisDrone person-only: existing general aerial baseline and fixed validation path.
4. Okutama-Action and AU-AIR: supplemental domain-transfer sources.

The next recall milestone is not visual polish. It is: audit local dataset roots, write converters for ready datasets, train a candidate, evaluate on the pinned manifest, then publish only if `scripts/report_visdrone_finetune.py` returns `claim.allowed: true`.