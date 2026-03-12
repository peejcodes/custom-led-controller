# Custom LED Controller — Rebuild

This repository replaces the earlier pygame-heavy prototype with a cleaner architecture:

- **Browser UI** served locally by a Python backend
- **PC-side animation engine**
- **Multiple controller support**
- **Named outputs, segments, and zones**
- **Transport abstraction** so you can start with mock controllers and move to serial hardware
- **Firmware scaffold** for an ESP32-S3 target

The design matches the requirements we locked in:

- ESP32-S3 controllers
- WS2812B LEDs
- animations generated on the **PC**, not on the controller
- multiple controllers
- up to **8 outputs** and roughly **800 LEDs** per controller as a practical first target
- target **30 FPS minimum**
- zones may span multiple outputs
- controller behavior on stream interruption: **freeze the last frame**

## What is included

### Working today
- FastAPI backend
- Local browser UI
- Pattern engine with:
  - `solid`
  - `chase`
  - `pulse`
  - `wave`
  - `rainbow`
  - `strobe`
  - `fire`
  - `rain`
- project configuration model
- live preview endpoint
- mock transport for local testing
- serial transport scaffold
- background streaming loop
- preset-ready project persistence

### Scaffold / next implementation target
- real ESP32-S3 firmware packet receiver
- production-grade binary framing / ACK handling
- per-zone scenes
- richer editor UX
- USB auto-discovery
- controller capability negotiation

## Repository layout

```text
src/custom_led_controller/
  api.py                FastAPI app and routes
  runtime.py            Streaming runtime and transport orchestration
  models.py             Pydantic data models
  engine.py             Pattern renderer / frame generation
  patterns.py           Pattern implementations
  storage.py            JSON persistence
  config.py             App settings
  static/               Browser UI assets
  transports/
    base.py
    mock.py
    serial_transport.py

firmware/
  protocol.md           host <-> controller protocol draft
  esp-idf/              starter firmware scaffold for ESP32-S3

tests/
  test_engine.py
  test_models.py
```

## Quick start

### 1. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install
```bash
pip install -e .[dev]
```

### 3. Run the app
```bash
custom-led-controller
```

Then open:

```text
http://127.0.0.1:8787
```

FastAPI docs will be available at:

```text
http://127.0.0.1:8787/docs
```

## Configuration model

A project contains:

- `controllers`
- `segments`
- `zones`
- `palette`
- `playback`

### Controller
A controller contains one or more outputs.

### Output
An output maps to a physical data line on the ESP32-S3.

### Segment
A segment is a slice of one output:
- controller id
- output id
- start index
- length
- optional reversed orientation

### Zone
A zone is a named logical grouping of segments, and **can span multiple outputs and controllers**.

## Current transport approach

The backend owns rendering and frame scheduling. Each frame is rendered on the PC, then dispatched to every connected controller.

This means the controller stays simple:
- receive frame chunks
- validate
- stage to back buffer
- swap on `SHOW`
- hold last frame if the PC pauses or disconnects

## Recommended development order

1. Run the backend and UI with the mock transport.
2. Edit `data/project.json` for your real controller / output layout.
3. Implement the serial frame packet handling in `serial_transport.py`.
4. Build the matching ESP-IDF firmware packet parser.
5. Add controller capability negotiation.
6. Add per-zone playback and preset scenes.

## Notes about bandwidth

For RGB LEDs, each pixel is 3 bytes. At 30 FPS:

- 300 LEDs ≈ 27 KB/s
- 600 LEDs ≈ 54 KB/s
- 800 LEDs ≈ 72 KB/s

That is practical over a high baud-rate USB serial link with careful framing, but once you scale beyond that, **multiple controllers** become the right way to grow.

## Replace-your-old-repo guidance

This zip is intended to replace the old repository structure.

Recommended migration:
1. back up the old repo
2. copy these files into a new branch
3. run the app in mock mode
4. edit the sample project layout for your real hardware
5. implement firmware and serial framing together

## Next milestone

The natural next milestone is to make the serial transport and the ESP-IDF receiver speak the protocol described in `firmware/protocol.md`, then verify:
- 2 controllers
- 8 outputs each
- 800 LEDs per controller
- 30 FPS stable
- last-frame hold on disconnect
