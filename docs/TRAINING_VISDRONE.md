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