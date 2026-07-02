# HERIDAL Person YOLO Conversion

This is the first converter on the aerial recall track. It does not fix recall by itself; it prepares local HERIDAL-style aerial-person data for training experiments.

Supported local annotation layouts:

- `annotations/*.xml` in Pascal VOC bounding-box form
- `annotations/annotations.csv` with `filename,xmin,ymin,xmax,ymax,class`

Raw datasets are not committed to this repo.

```bash
python scripts/prepare_heridal_person_yolo.py \
  --heridal-root /data/HERIDAL \
  --output-root /data/heridal_person_yolo \
  --copy-mode copy
```

Output:

```text
heridal_person_yolo/
  images/train/
  labels/train/
  heridal_person.yaml
```

Train only after checking dataset license/access terms. Publish no recall-improvement claim until the trained candidate passes `scripts/report_visdrone_finetune.py` on a pinned validation manifest.