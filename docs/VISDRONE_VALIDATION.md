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

## Initial DET validation run

Dataset: VisDrone2019-DET-val  
Task: Person-category detection sanity check  
Categories evaluated: `pedestrian`, `people`  
Model: `yolo26n.pt`  
Confidence threshold: 0.25  
IoU threshold: 0.5  

### Small subset run

Images evaluated: 25  
GT person boxes: 628  
Detections: 93  
TP: 68  
FP: 25  
FN: 560  
Precision: 0.7312  
Recall: 0.1083  
F1: 0.1886  

### Full validation split run

Images evaluated: 548  
GT person boxes: 13969  
Detections: 975  
TP: 802  
FP: 173  
FN: 13167  
Precision: 0.8226  
Recall: 0.0574  
F1: 0.1073  

### Interpretation

This is a public aerial-drone detection sanity check. It evaluates the existing person detector against VisDrone `pedestrian` and `people` annotations.

The baseline model was not trained specifically on VisDrone aerial-person imagery, so low recall or precision is expected. This result establishes a reproducible baseline for future detector improvement.

It is not a full SAR benchmark, not a tracking benchmark, and not operational field validation.