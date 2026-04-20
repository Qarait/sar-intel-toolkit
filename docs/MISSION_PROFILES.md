# Mission Profiles

Mission profiles are named configuration presets.

They tune existing pipeline settings such as detector confidence thresholds, Kalman noise parameters, and track scoring weights.

They do not change the core pipeline, replace validation, or authorize real-world drone operations.

## Verified built-in profiles

### sar_daylight

Default search-and-rescue daylight profile.

### sar_low_visibility

A lower-visibility SAR profile that lowers the detector confidence threshold and increases Kalman measurement noise so tracking relies more on temporal continuity.

This profile does not guarantee performance in rain, fog, smoke, or poor contrast. It is a tuning preset, not an automatic weather detector.

## Future profile templates

### sar_night_thermal

Requires thermal or IR footage and a detector trained or validated on that sensor modality.

This template requires a custom validated detector model and authorized mission context.

### wildfire

Requires a validated fire/smoke detector and authorized operating context.

This template requires a custom validated detector model and authorized mission context.

The toolkit must not be used to imply permission to fly near wildfires. The FAA warns that drones near wildfires can ground firefighting aircraft and delay airborne response, which can threaten firefighters, residents, and property.