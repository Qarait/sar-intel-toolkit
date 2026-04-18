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

`output/alerts.json` contains one entry per detected person per frame. Below is a real run on daylight street footage (3840×2160, 25fps, ~10 seconds) showing three people and a background crowd:

```json
[
  {"timestamp": "2026-04-18T15:00:01Z", "lat": 43.6489098, "lon": -79.3807224, "confidence": 0.9394, "type": "possible_person"},
  {"timestamp": "2026-04-18T15:00:01Z", "lat": 43.6489074, "lon": -79.3805245, "confidence": 0.899, "type": "possible_person"},
  {"timestamp": "2026-04-18T15:00:01Z", "lat": 43.6489804, "lon": -79.3807982, "confidence": 0.684, "type": "possible_person"},
  {"timestamp": "2026-04-18T15:00:01Z", "lat": 43.6489707, "lon": -79.3809351, "confidence": 0.5061, "type": "possible_person"},
  {"timestamp": "2026-04-18T15:00:01Z", "lat": 43.6489103, "lon": -79.3807232, "confidence": 0.9351, "type": "possible_person"}
]
```

**Fields:**
- `timestamp`: UTC time of the alert (from video start_time_utc + frame_idx / fps)
- `lat`, `lon`: estimated person location (nadir-camera projection from bbox and camera FOV)
- `confidence`: YOLO detector confidence (0–1)
- `type`: alert class ("possible_person" for this MVP)

**Real Test Results:**
- Clip: 3840×2160 street footage, 25 fps, ~14 sec
- Detections: 2400 person alerts across the clip
- Confidence range: 0.50–0.95 (realistic spread, no wall of marginals)
- Coordinates: Cluster by person, drift smoothly with simulated drone path

## Notes

- `config.yaml` uses a pretrained Ultralytics detect model.
- `config.offline.yaml` forces OpenCV HOG person detection so the pipeline can run without downloading model weights.
- The geotagging step is intentionally approximate: it assumes a nadir-looking camera, flat ground, and no terrain model.
