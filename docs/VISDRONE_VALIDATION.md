# VisDrone Validation

This document describes how to run a public aerial-drone validation check.

The validation harness evaluates the existing person detector against the VisDrone DET validation split, using only the `pedestrian` and `people` categories.

This is not a full SAR operational validation. It is an aerial-person detection sanity check on public drone imagery.

## Dataset

Use the VisDrone DET validation split.

The original run used a local downloaded copy of `VisDrone2019-DET-val`; the dataset itself is not committed to this repository.

Expected layout:

```text
VisDrone2019-DET-val/
  images/
  annotations/
```

## Run

Example subset run:

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

Exact full validation split command used for the public baseline result:

```bash
python scripts/evaluate_visdrone_det.py \
  --dataset-root /path/to/VisDrone2019-DET-val \
  --split val \
  --model yolo26n.pt \
  --confidence-threshold 0.25 \
  --iou-threshold 0.5 \
  --output output/visdrone_det_validation_val.json
```

Replace `/path/to/VisDrone2019-DET-val` with the local path to the downloaded VisDrone DET validation split.

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

The public baseline reported here was run with `yolo26n.pt`. Other configs may use a different lightweight detector such as `yolov8n.pt`; results should only be compared when the model, confidence threshold, IoU threshold, and dataset split are held constant.

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

The low recall should be interpreted as a baseline limitation, not as a benchmark-leading claim. The baseline model was not trained specifically on VisDrone aerial-person imagery, so many small or difficult aerial-person instances are missed.

This result is intended to be reproducible and comparable over time. It is a documented baseline for future detector improvement rather than a claim that the current detector is state of the art on VisDrone.

It is not a full SAR benchmark, not a tracking benchmark, and not operational field validation.

## Threshold Sweep Status

The current published baseline uses:

- Confidence threshold: 0.25
- IoU threshold: 0.5

A multi-threshold sweep has not yet been published. Future validation work should evaluate thresholds such as `0.10`, `0.25`, and `0.50` to show the precision/recall tradeoff more clearly.

## How To Improve This Later

- Fine-tune the detector on aerial-person data, including VisDrone-like viewpoints and object scales.
- Evaluate multiple confidence thresholds to understand baseline precision/recall tradeoffs.
- Test larger detector models to see whether recall improves on small aerial targets.
- Add separate tracking or video-level validation later instead of treating this image-level DET check as an end-to-end benchmark.