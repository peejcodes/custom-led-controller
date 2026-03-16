Pattern integration patch for the rebuild project.

Apply this ZIP at the root of the rebuild project, for example:
  /home/peej/PycharmProjects/custom_led_controller_rebuild

What changed:
- Added a standalone pattern library module based on the uploaded 1D/2D pattern pack.
- Integrated 1D patterns through an adapter layer in src/custom_led_controller/patterns.py.
- Switched playback.pattern from a rigid enum to a registry-driven string id.
- Added /api/patterns so the UI can query available pattern metadata.
- Replaced the hardcoded home-screen pattern chips with a scalable grouped selector.
- Kept the existing core pattern ids (solid, chase, pulse, wave, rainbow, strobe, fire, rain).
- Added many new pattern ids including scanner, comet_trail, meteor_rain, twinkle_stars, heartbeat, plasma_band, noise_shimmer, and more.
- Added tests to verify every registered pattern renders successfully.

How to apply:
1. Back up your current project folder.
2. Unzip this patch into the rebuild project root and overwrite files.
3. Restart the backend and hard refresh the browser.

This patch targets the rebuild architecture, not the original pygame prototype in the GitHub repo.