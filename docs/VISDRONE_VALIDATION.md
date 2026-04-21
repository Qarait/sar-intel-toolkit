# VisDrone Validation

This document describes how to run a public aerial-drone validation check.

The validation harness evaluates the existing person detector against the VisDrone DET validation split, using only the `pedestrian` and `people` categories.

This is not a full SAR operational validation. It is an aerial-person detection sanity check on public drone imagery.

## Dataset

Use the VisDrone DET validation split.

Expected layout:

```text
VisDrone2019-DET-val/
  images/
  annotations/
```

## Run

```bash
python scripts/evaluate_visdrone_det.py \
  --dataset-root /path/to/VisDrone2019-DET-val \
  --split val \
  --max-images 50 \
  --model yolo26n.pt \
  --confidence-threshold 0.25 \
  --iou-threshold 0.5 \
  --output output/visdrone_det_validation.json
```

## Output

The script writes:

`output/visdrone_det_validation.json`

with precision, recall, F1, GT count, detection count, TP, FP, FN, and per-image summaries.

## Interpretation

This validation checks aerial-person detection behavior. It does not validate operational SAR use, exact geotag accuracy, or real flight safety.