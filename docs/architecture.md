# Architecture

## System split

### Host computer
Responsible for:
- rendering patterns
- owning project state
- scheduling frames
- saving presets/projects
- grouping segments into zones
- dispatching frames to each controller

### ESP32-S3 controller
Responsible for:
- driving multiple physical outputs
- validating incoming packets
- buffering output frames
- swapping buffers cleanly
- freezing the last frame if the host disappears

## Data hierarchy

```text
Project
  Controllers
    Outputs
  Segments
  Zones
  Palette
  Playback
```

### Controllers
A controller represents one ESP32-S3 device.

### Outputs
A physical LED data line on that controller.

### Segments
An addressable slice of one physical output.

### Zones
Logical groupings of segments. A zone may span:
- multiple outputs
- multiple controllers

That is what makes the layout manageable once the installation grows.

## Runtime loop

1. Load project
2. Start frame loop
3. Render one frame per controller
4. Flatten each output to raw RGB bytes
5. Push bytes to connected transports
6. Sleep until the next frame deadline

## Why the transport abstraction matters

You asked for multiple controllers and growth beyond one controller's practical bandwidth.

The transport abstraction lets the backend treat every controller the same while still allowing:
- mock testing
- USB serial now
- network transport later, if you ever want Ethernet/Wi-Fi controllers

## UI design choice

This repo uses a no-build browser UI for a reason:
- quick to run
- easy to integrate with another local web dashboard later
- fewer dependencies than React/Vite for this stage
- easy to replace later without touching engine or transport code
