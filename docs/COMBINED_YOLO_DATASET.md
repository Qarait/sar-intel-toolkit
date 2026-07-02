# Combined Person YOLO Dataset

Use this after converting individual sources such as VisDrone-person and HERIDAL-person. It creates one training dataset with source-prefixed filenames and a provenance manifest.

```bash
python scripts/combine_person_yolo_datasets.py \
  --source heridal=/data/heridal_person_yolo \
  --source visdrone=/data/visdrone_person \
  --output-root /data/sar_intel_person_yolo
```

Output:

```text
sar_intel_person_yolo/
  images/train/
  images/val/
  labels/train/
  labels/val/
  combined_person.yaml
  combined_manifest.json
```

The manifest records source ids, counts, output files, and SHA256 hashes of source images/labels. This is the dataset provenance anchor for future training runs. A combined dataset still does not prove recall improved; only the fine-tune report gate can allow that claim after evaluation.