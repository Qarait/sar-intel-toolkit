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
  --output output/visdrone_det_validation_val.json \
  --write-validation-manifest output/visdrone_det_val_manifest.json
```

Replace `/path/to/VisDrone2019-DET-val` with the local path to the downloaded VisDrone DET validation split.

## Output

The script writes:

`output/visdrone_det_validation.json`

with precision, recall, F1, average precision, PR-curve points, GT count, detection count, TP, FP, FN, per-image summaries, and the validation manifest checksum used for the run.

If `--sweep --sweep-thresholds ...` is provided, the script runs one detector pass per image at the lowest requested threshold, then writes a sweep summary by filtering those cached detections in memory for each threshold.

If `--sweep-thresholds` is omitted, the default sweep thresholds are `0.10`, `0.25`, and `0.50`.
## Pinned validation manifest

Before comparing a fine-tuned model against the published baseline, pin the exact validation inputs:

```bash
python scripts/evaluate_visdrone_det.py \
  --dataset-root /path/to/VisDrone2019-DET-val \
  --split val \
  --model yolo26n.pt \
  --iou-threshold 0.5 \
  --sweep \
  --sweep-thresholds 0.10,0.25,0.50 \
  --output output/visdrone_det_sweep.json \
  --write-validation-manifest output/visdrone_det_val_manifest.json
```

Future baseline and fine-tuned runs should reuse that manifest:

```bash
python scripts/evaluate_visdrone_det.py \
  --dataset-root /path/to/VisDrone2019-DET-val \
  --split val \
  --model /path/to/best.pt \
  --iou-threshold 0.5 \
  --sweep \
  --sweep-thresholds 0.10,0.25,0.50 \
  --validation-manifest output/visdrone_det_val_manifest.json \
  --output output/visdrone_det_finetuned_sweep.json
```

The manifest records the sorted image/annotation file list, file sizes, SHA256 hashes, and a manifest checksum. A run with a different file list, altered files, or a different `--max-images` value should be treated as a new benchmark, not a before/after comparison.

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

## Precision / recall threshold sweep

Dataset: `VisDrone2019-DET-val`  
Model: `yolo26n.pt`  
Categories: `pedestrian`, `people`  
IoU threshold: `0.5`

The sweep was generated by running the detector once at the lowest confidence threshold and filtering the same detections in memory for each threshold.

```bash
python scripts/evaluate_visdrone_det.py \
  --dataset-root /path/to/VisDrone2019-DET-val \
  --split val \
  --model yolo26n.pt \
  --iou-threshold 0.5 \
  --sweep \
  --sweep-thresholds 0.10,0.25,0.50 \
  --validation-manifest output/visdrone_det_val_manifest.json \
  --output output/visdrone_det_sweep.json
```

| Confidence | Detections | TP | FP | FN | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.10 | 975 | 802 | 173 | 13167 | 0.8226 | 0.0574 | 0.1073 |
| 0.25 | 975 | 802 | 173 | 13167 | 0.8226 | 0.0574 | 0.1073 |
| 0.50 | 299 | 271 | 28 | 13698 | 0.9064 | 0.0194 | 0.0380 |

These rows should be read as fixed-threshold sensitivity for the current baseline model, not as a benchmark-leading claim. Raising the threshold improves precision here, but recall remains low on small or difficult aerial-person instances. Do not claim improvement from the best recall discovered after trying many thresholds; compare fixed thresholds and the reported average precision / PR curve on the pinned manifest.

Lower confidence thresholds increase the chance of detecting small or difficult aerial-person instances, but may increase false positives. Higher thresholds reduce false positives but can miss more people.

This sweep is a baseline detector sensitivity check. It is not a claim of benchmark-leading performance or operational SAR readiness. The baseline model was not trained specifically on VisDrone aerial-person imagery, so low recall is expected.

## Domain-specific detector improvement

The current published baseline uses a general pretrained detector. The next validation step is to fine-tune a person-only model on the VisDrone training split by merging the `pedestrian` and `people` categories into a single `person` class.

The fine-tuning workflow is documented in [`docs/TRAINING_VISDRONE.md`](TRAINING_VISDRONE.md).

The fine-tuning workflow has been added, but no fine-tuned model metrics are published yet. Before/after results should only be added after the VisDrone train split is converted, a model is trained, and the resulting weights are evaluated on the validation split.

After training, this document should report a before/after comparison:

- baseline `yolo26n.pt`
- fine-tuned `best.pt`
- precision / recall / F1 at matching fixed thresholds
- average precision and PR-curve behavior on the same pinned validation manifest

The goal is to improve aerial-person recall while preserving honest reporting of false positives. A model should count as improved only when recall improves at fixed thresholds without an unacceptable precision collapse, and average precision / PR-curve behavior also improves on the same pinned manifest.


## Fine-tune comparison gate

After producing baseline and candidate sweep outputs on the same pinned validation manifest, run the comparison gate:

```bash
python scripts/compare_visdrone_runs.py \
  --baseline output/visdrone_det_sweep.json \
  --candidate output/visdrone_det_finetuned_sweep.json \
  --recall-delta 0.05 \
  --min-precision-ratio 0.90 \
  --ap-delta 0.03 \
  --output output/visdrone_det_comparison.json
```

A candidate detector should not be described as improved unless this gate passes on the same validation manifest. The gate requires matching manifest checksums, recall improvement at matching fixed thresholds, no unacceptable precision collapse, and average-precision improvement. This protects the project from accidental split drift and from threshold-shopping that makes recall look better while the detector becomes less useful.

## How To Improve This Later

- Fine-tune the detector on aerial-person data, including VisDrone-like viewpoints and object scales.
- Evaluate the same fixed confidence thresholds to understand precision/recall tradeoffs without threshold-shopping.
- Test larger detector models to see whether recall improves on small aerial targets.
- Add separate tracking or video-level validation later instead of treating this image-level DET check as an end-to-end benchmark.
