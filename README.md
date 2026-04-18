# SAR-INTEL TOOLKIT — MVP v0.1

This version does exactly four things:

1. Generates a search grid from a bounding box.
2. Runs person detection on video frames using a pretrained detector.
3. Simulates drone telemetry along the generated path.
4. Fuses detection + telemetry into JSON alerts.

## Run

Ultralytics-first config:

```bash
pip install -r requirements.txt
python main.py --config config.yaml
```

Offline-safe config:

```bash
pip install -r requirements.txt
python main.py --config config.offline.yaml
```

## Inputs

- `config.yaml` or `config.offline.yaml`
- `sample_data/video.mp4`

## Outputs

- `sample_data/path.json`
- `output/alerts.json`

## Notes

- `config.yaml` uses a pretrained Ultralytics detect model.
- `config.offline.yaml` forces OpenCV HOG person detection so the pipeline can run without downloading model weights.
- The geotagging step is intentionally approximate: it assumes a nadir-looking camera, flat ground, and no terrain model.
