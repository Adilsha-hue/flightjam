# Hardware design and research

## Scope and reference assembly

Two USB-powered integrated ESP32-S3/SX1262 development boards, one sender and one receiver. Optional sender potentiometer demonstrates a changing sensor value. Laptop provides power/programming/logging. The hardware simulator is at `sim/hardware-lab.html`; packet authentication and virtual disturbance are demonstrated at `sim/learning-lab.html`.

This is an assembly-level reference design and behavioral simulation. No physical hardware has been built, measured or flashed. It is not a transistor-level circuit simulation, RF calibration or a manufactured PCB. Interference is a software channel event, with no physical interference transmitter.

## Research findings

- Manufacturer V3.1 schematic shows the integrated SX1262, ESP32-S3, 3.3 V power system, RF switching and USB-UART subsystem. Source: [official schematic](https://resource.heltec.cn/download/WiFi_LoRa_32_V3/HTIT-WB32LA%28F%29_V3.1_Schematic_Diagram.pdf).
- V4 documentation includes revision-specific external power amplifier configuration (including the V4.2 GC1109 option). A V3-style SPI map alone does not establish V4 initialization compatibility. Source: [official V4 documentation](https://wiki.heltec.org/docs/devices/open-source-hardware/esp32-series/lora-32/wifi-lora-32-v4/).
- The repository already assigns GPIO 8/9/10/11/12/13/14 to NSS/SCK/MOSI/MISO/RESET/BUSY/DIO1. These are internal radio nets on the integrated boards, not seven external wires to add. Verify against the exact purchased revision before flashing.
- External potentiometer and its firmware are proposed extensions. Current upstream firmware produces mock telemetry; it does not read this input. The simulator uses a percentage rather than asserting ADC calibration or voltage measurements.

## Connection schedule

| ID | From | To | Purpose |
|---|---|---|---|
| P1 | Laptop USB port | TX board USB connector | USB power and programming/serial |
| P2 | Laptop USB port | RX board USB connector | USB power and programming/serial |
| S1 (optional) | TX board 3V3 | Potentiometer outer terminal A | 3.3 V reference |
| S2 (optional) | TX board GND | Potentiometer outer terminal B | Return |
| S3 (optional) | Potentiometer wiper | TX GPIO1, after revision/header verification | Analog demonstration input |

Use a 10 kΩ linear potentiometer and 3.3 V-compatible connections. No GPIO may be driven directly from USB 5 V. Radio traces and power regulation already exist on the board. Do not connect two radio outputs directly together. A physical RF path is outside this assembly diagram; the original conducted bench requires a separately engineered laboratory harness.

## Bill of materials

| Item | Qty | Required? | Assigned role |
|---|---:|---|---|
| Matching Heltec ESP32-S3/SX1262 integrated boards | 2 | Yes for physical nodes | TX and RX |
| Compatible USB data cables | 2 | Yes | Power, upload, logs |
| Laptop | 1 | Yes | Firmware build and logger |
| Insulating board mounts / enclosures | 2 sets | Yes for packaged demo | Prevent contact shorts |
| 10 kΩ linear potentiometer | 1 | Optional | Sender input demonstration |
| Breadboard and jumper wires | 1 set | Only with optional input | External sensor wiring |
| Multimeter | 1 shared | For bench checks | Supply and continuity measurements |
| Powered USB hub | 1 | If needed | Laptop port expansion |

Prices and stock are not verified. No aircraft motors, ESCs, flight controller or propellers are needed. Do not buy a separate SX1262 breakout for these integrated boards.

## Functional blocks

TX: USB → onboard regulator → MCU + radio. Optional input → MCU → frame encoder → internal SPI → radio.

RX: USB → onboard regulator → MCU + radio. Radio → internal SPI → decoder/authentication → USB serial → logger.

Behavioral model: each node needs power and valid radio initialization. Sensor absent selects mock fallback. Receiver USB data can fail independently of receiver power. Virtual interference erases packets in the model. These switches represent faults; toggling “internal SPI valid” does not imply a removable onboard cable.

## Physical validation still required

Identify board revision first. Use the manufacturer-supported initialization for that revision; review RF switch, oscillator and V4 front-end configuration. Resolve receiver actual-length parsing, clock synchronization, restart handling and private-key provisioning identified in `docs/BUILD-AND-UNDERSTAND.md`. Compile and flash each node only after these checks. Measure supply rails with a multimeter before adding the optional input. Verify that the input stays within 0–3.3 V and that the firmware actually reads it. Establish a safe authorized telemetry RF configuration separately; do not confuse a browser run with a working physical link.

Acceptance: both boards boot; radio initialization succeeds; sender sequence increases; receiver logs valid frames; sensor change appears when sensor support exists; loss and auth rejection are counted separately; power and USB faults produce the documented behavior. Document measured results alongside simulated results.

## Simulation checks completed

Browser checks verified normal delivery and logging, USB data disconnected while board reception continued, receiver power-off, restoration, sensor mock fallback, complete virtual channel loss at 100%, transmitter radio initialization failure and session restore. Browser console reported no errors. These checks establish simulated state behavior, not physical electrical correctness or RF performance.
