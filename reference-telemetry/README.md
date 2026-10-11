# Separate encrypted telemetry reference

Target: **Heltec WiFi LoRa 32 V3**, matching 863–870 MHz variant, two boards. It is not a V4 port. The original repository files are unchanged. Firmware transmits mock position once per minute or slower; it is a bench software reference, not flight-tested tracking.

Generate the local key with `python create_key.py`. Build both roles using the same generated key:

```powershell
pio run -d reference-telemetry -e transmitter
pio run -d reference-telemetry -e receiver
```

Run key creation from this directory or `python reference-telemetry/create_key.py` from the repository. Upload only after identifying the exact boards and validating their RF setup. PlatformIO dependencies are pinned for reproducibility. Do not publish `include/secrets.h` or compiled binaries containing that key. Protect or reprovision keys before real use.

Wire format: version(1), device(4), persistent boot session(4), sequence(4), encrypted mock lat/lon/alt(12), GCM tag(16). Header fields are big endian and authenticated as additional data. Nonce is device/session/sequence. TX increments a persistent boot counter before generating packets. RX verifies the tag and rejects already accepted session/sequence values, persisting its high-water state. This differs from the original HMAC frame and logger format; do not mix the implementations.

NVS reset/rollback on TX can reuse nonces under the old key: rekey whenever TX storage is erased or replaced. Cloning devices with the same device id/key is forbidden. RX state reset can allow replay of older packets: reprovision a new key after reset. Per-packet persistence is intended for this slow bench rate and needs a storage endurance strategy at higher rates. No independent trustworthy clock is implemented, so a previously unseen authentic delayed packet can still pass the monotonic guard.

No real GNSS input, backup radio, flight control, display driver or aircraft failsafe is implemented. Use the serial monitor for received values. Physical board initialization, oscillator voltage and RF-switch behavior must be verified against your exact V3 revision. V4 has different front-end requirements and is excluded from this reference.

Antenna: use a manufacturer-compatible antenna for the chosen regional band and matching board RF connector; both nodes need the proper RF termination. Do not connect a radio output to another output directly. Keep the repository's conducted bench as a separately engineered lab setup. Antennas are for lawful telemetry only; this project does not build an interference transmitter.

Build verification: both PlatformIO environments (`transmitter` and `receiver`) compiled successfully with the pinned dependencies. No firmware has been flashed or physically tested.
