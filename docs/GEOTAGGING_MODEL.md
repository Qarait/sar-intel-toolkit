# Geotagging Model

This document describes the coordinate assumptions used by the toolkit geotagging modes.

The current implementation is still a flat-ground approximation. It is intended to make the model and assumptions explicit, not to claim operational SAR localization accuracy.

## Coordinate frames

### Image frame

- Pixel `x` increases to the right.
- Pixel `y` increases downward.
- The image origin is the top-left corner.
- The selected target point is derived from the bounding box using either `bbox_center` or `bbox_bottom_center`.

### Camera frame

- The optical axis points downward by default.
- The local ray model uses three intuitive components before attitude rotation:
  - right
  - forward
  - down
- With zero pitch and roll, the image center points straight down.
- Pixels above image center tilt the ray forward.
- Pixels to the right of image center tilt the ray right.

### Body / drone frame

- The pose-aware mode assumes the downward-facing camera is rigidly aligned with the aircraft body reference used by telemetry.
- At zero yaw, pitch, and roll:
  - image-right aligns with local east
  - image-up footprint displacement aligns with local north
  - the optical axis points toward the ground

### World frame

- The projection is solved in a local flat-ground east/north/up style frame centered at the drone position.
- Ground is modeled as a plane at `z = 0`.
- The drone is modeled as being located at `(0, 0, altitude_m)` above that plane.
- Offsets are converted back to latitude/longitude using local east/north meter offsets.

## Angle conventions

### yaw_deg

- `yaw_deg` is treated as clockwise from north.
- `yaw_deg = 0` means the aircraft forward direction points north.
- `yaw_deg = 90` means the aircraft forward direction points east.

### pitch_deg

- For `pose_aware_flat_ground`, positive `pitch_deg` is assumed to tilt the camera footprint toward the aircraft forward direction.
- With `yaw_deg = 0`, positive pitch moves the projected center footprint north.
- This is a geotagging convention and requires telemetry pitch to use a consistent sign convention.

### roll_deg

- For `pose_aware_flat_ground`, positive `roll_deg` is assumed to tilt the camera footprint toward the aircraft right side.
- With `yaw_deg = 0`, positive roll moves the projected center footprint east.
- This also requires telemetry roll to use a consistent sign convention.

## Camera assumption

- The camera is downward-facing by default.
- Ground is modeled as flat.
- No terrain model is used.
- No lens distortion correction is applied.
- No full camera calibration model is applied.

## Current modes

### nadir

- Uses image-space offsets directly under a nadir-camera assumption.
- Does not use telemetry attitude.

### heading_aware_nadir

- Uses the same nadir approximation as `nadir`.
- Rotates image-space offsets into world east/north directions using `yaw_deg`.
- Does not use `pitch_deg` or `roll_deg`.

## New mode

### pose_aware_flat_ground

- Builds a camera ray from the selected image point and the camera field of view.
- Rotates that ray using yaw, pitch, and roll.
- Intersects the rotated ray with a flat ground plane.
- Converts the resulting east/north ground offset to latitude/longitude.
- Can optionally fall back to a nadir-based mode only when config explicitly sets `pose_fallback_mode`.

This mode is more realistic than pure nadir offset rotation when aircraft attitude is available, but it remains approximate because it still assumes a flat ground plane and an idealized camera model.

## Limitations

- The mode requires telemetry yaw, pitch, and roll to use a consistent convention.
- Results remain approximate without camera calibration.
- The model is not terrain-aware photogrammetry.
- It does not account for lens distortion.
- It is not validated for real operational SAR localization.