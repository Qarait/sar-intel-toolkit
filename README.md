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

## Sample Output

`output/alerts.json` contains one entry per detected person per frame:

```json
[
  {
    "frame": 42,
    "timestamp": "2026-04-17T14:23:15Z",
    "drone_lat": 40.7128,
    "drone_lon": -74.0060,
    "target_lat": 40.7132,
    "target_lon": -74.0055,
    "confidence": 0.89,
    "bbox": [150, 200, 50, 120]
  }
]
```

- `frame`: video frame number
- `timestamp`: simulated drone time
- `drone_lat`, `drone_lon`: simulated drone position (follows the generated waypoint grid)
- `target_lat`, `target_lon`: estimated person location (nadir-camera projection from bbox and FOV)
- `confidence`: detector confidence score (0–1)
- `bbox`: [x, y, w, h] bounding box in frame coordinates

## Notes

- `config.yaml` uses a pretrained Ultralytics detect model.
- `config.offline.yaml` forces OpenCV HOG person detection so the pipeline can run without downloading model weights.
- The geotagging step is intentionally approximate: it assumes a nadir-looking camera, flat ground, and no terrain model.
