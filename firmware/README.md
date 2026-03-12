# Firmware Notes

This repository targets an **ESP32-S3** controller that behaves as a deterministic frame sink.

The controller is intentionally simple:

1. initialize outputs
2. receive frame packets from the PC
3. validate and buffer frame payloads
4. swap the back buffer to front on `SHOW`
5. if the PC stops sending, **hold the last rendered frame**

## Why this design

The PC owns the expensive work:
- animation generation
- zone logic
- palette interpolation
- future audio / DSP work
- project state

The ESP32-S3 owns only:
- output timing
- packet intake
- buffering
- fail-safe behavior

## First implementation target

- ESP-IDF
- USB serial
- 8 outputs
- 800 total LEDs
- 30 FPS target
- WS2812B via RMT

Use `protocol.md` as the source of truth for the host/controller handshake until the firmware implementation is finalized.
