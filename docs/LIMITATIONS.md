# Limitations

- Not a real-time drone control system
- No live drone integration
- No terrain model
- No camera calibration workflow
- Pitch/roll-aware geotagging is supported only through the `pose_aware_flat_ground` flat-ground approximation, not as terrain-aware calibrated photogrammetry.
- Person tracks are detection sequences, not verified identities
- GeoJSON output is for visualization, not ground-truth localization
- SAR operational use would require field validation, sensor calibration, and human review