# VisDrone Person Detector Fine-Tuning

The current published baseline uses a general pretrained detector and shows low recall on aerial-person imagery.

This workflow prepares a person-only VisDrone dataset by merging:

- `pedestrian`
- `people`

into one YOLO class:

- `person`

This keeps the trained model compatible with the existing SAR-INTEL detector pipeline, where class `0` is treated as person.

## Prepare the dataset

```bash
python scripts/prepare_visdrone_person_yolo.py \
  --visdrone-root /path/to/VisDrone \
  --output-root /path/to/datasets/visdrone_person
```

Expected raw layout:

```text
VisDrone/
  VisDrone2019-DET-train/
    images/
    annotations/
  VisDrone2019-DET-val/
    images/
    annotations/
```

Expected converted layout:

```text
datasets/visdrone_person/
  images/train/
  images/val/
  labels/train/
  labels/val/
  visdrone_person.yaml
```

## Dataset requirement

The full fine-tuning workflow requires both:

- `VisDrone2019-DET-train`
- `VisDrone2019-DET-val`

A validation-only conversion is useful for sanity-checking label formatting, but training requires the train split.

## Train

```bash
python scripts/train_visdrone_person.py \
  --data /path/to/datasets/visdrone_person/visdrone_person.yaml \
  --model yolo26n.pt \
  --epochs 50 \
  --imgsz 640 \
  --batch auto \
  --project runs/visdrone_person \
  --name yolo26n_visdrone_person
```

## Evaluate without threshold-shopping

After training, evaluate the model against the same pinned validation manifest used by the baseline:

```bash
python scripts/evaluate_visdrone_det.py \
  --dataset-root /path/to/VisDrone2019-DET-val \
  --split val \
  --model runs/visdrone_person/yolo26n_visdrone_person/weights/best.pt \
  --iou-threshold 0.5 \
  --sweep \
  --sweep-thresholds 0.10,0.25,0.50 \
  --validation-manifest output/visdrone_det_val_manifest.json \
  --output output/visdrone_det_finetuned_sweep.json
```

Treat `output/visdrone_det_val_manifest.json` as part of the benchmark definition. If the manifest checksum changes, the run is a new benchmark and should not be compared directly with the published baseline.

A fine-tuned model should only be described as improved when recall improves at fixed thresholds without an unacceptable precision collapse, and average precision / PR-curve behavior also improves on the same pinned manifest.
