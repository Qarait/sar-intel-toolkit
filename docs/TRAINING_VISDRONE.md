# VisDrone Person Fine-Tuning

This document describes the repo-local workflow for preparing a person-only YOLO dataset from VisDrone DET and running fine-tuning experiments.

This workflow targets the current bottleneck: low aerial-person recall. It is for controlled detector experiments only. It does not change the runtime SAR pipeline automatically, and no fine-tuned checkpoint is published as a repository baseline here.

## Scope

- Merge VisDrone DET `pedestrian` and `people` annotations into a single YOLO class: `person`
- Ignore non-person categories
- Generate a standard YOLO folder layout and `visdrone_person.yaml`
- Run fine-tuning locally against the prepared dataset

## Prepare The Dataset

Expected input layout under the extracted VisDrone root:

```text
/path/to/VisDrone-extracted/
  VisDrone2019-DET-train/
    images/
    annotations/
  VisDrone2019-DET-val/
    images/
    annotations/
```

Example preparation command:

```bash
python scripts/prepare_visdrone_person_yolo.py \
  --visdrone-root /path/to/VisDrone-extracted \
  --output-root /path/to/visdrone-yolo-person
```

This generates:

```text
/path/to/visdrone-yolo-person/
  visdrone_person.yaml
  images/
    train/
    val/
  labels/
    train/
    val/
```

The generated `visdrone_person.yaml` uses a single class mapping:

```yaml
names:
  0: person
```

## Train Locally

Example fine-tuning command:

```bash
python scripts/train_visdrone_person.py \
  --data /path/to/visdrone-yolo-person/visdrone_person.yaml \
  --model yolo26n.pt \
  --epochs 50 \
  --imgsz 640 \
  --batch auto
```

By default, training outputs are written under `runs/visdrone_person/`, which is ignored by git.

## Safety Notes

- Do not commit extracted datasets, generated YOLO datasets, training runs, checkpoints, or local media artifacts.
- This workflow does not change the runtime pipeline automatically.
- Fine-tuned results should only be published after evaluation.
- Keep public docs conservative: a local fine-tuning workflow does not by itself establish a new public benchmark.