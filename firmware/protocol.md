# Host <-> Controller Protocol Draft

This protocol is intentionally simple for the first real firmware pass.

## Goals
- deterministic
- binary
- easy to debug
- controller can hold the last frame if host disappears
- support multiple outputs
- support frame chunking later if needed

## Terms
- **front buffer**: currently displayed frame
- **back buffer**: frame being assembled from host packets

## Transport
USB serial over the ESP32-S3.

Recommended starting baud rates:
- 921600
- 1500000
- 2000000 (test carefully)

## Packet framing

### Header
```text
magic[4]   = "LEDC"
version[1] = 0x01
type[1]
flags[1]
reserved[1]
payload_len[4] big-endian
```

### Packet types
- `0x01` = PING
- `0x02` = CAPS_REQUEST
- `0x03` = CAPS_RESPONSE
- `0x10` = FRAME_BEGIN
- `0x11` = FRAME_OUTPUT_DATA
- `0x12` = FRAME_END
- `0x13` = SHOW
- `0x20` = ACK
- `0x21` = NACK

## Suggested workflow

### 1. Host connects
Host sends:
- `PING`
- `CAPS_REQUEST`

Controller responds with:
- firmware version
- controller id
- output count
- maximum LEDs per output
- total frame buffer capacity

### 2. Host sets or confirms layout
For V1, layout can be fixed in firmware or boot config.
For V1.1, add a `SET_LAYOUT` packet.

### 3. Host streams a frame
Host sends:
- `FRAME_BEGIN` with frame sequence
- one `FRAME_OUTPUT_DATA` packet per output
- `FRAME_END`
- `SHOW`

Controller behavior:
- write each output payload into the back buffer
- verify lengths
- on `SHOW`, swap buffers atomically

### 4. Link interruption
If packets stop arriving:
- keep displaying the current front buffer
- maintain a watchdog counter
- optionally expose timeout telemetry

## V1 simplification

The Python scaffold currently sends a reduced packet format per output:
```text
magic[4] | version[1] | type[1] | output_id_len[1] | payload_len[4] | output_id | raw_rgb_bytes
```

This is enough to stand up:
- host streaming
- receiver parsing
- output mapping

Once that is stable, upgrade to the fuller protocol above.

## Future extensions
- CRC32
- packet sequence numbers
- chunked output payloads
- resends
- controller timestamps
- sync groups
