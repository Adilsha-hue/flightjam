# Wokwi ESP32-S3 result

Executed in Wokwi through BrowserOS Neo. All 9 checks passed:

- Encryption
- Valid receive
- Payload matches
- Replay rejection
- Tampered authentication tag rejection
- Tampered ciphertext rejection
- Short frame rejection
- Wrong version rejection
- New session acceptance

Serial output: `RESULT 9/9 PASSED`.

This harness copies the reference AES-GCM function and models receiver acceptance with volatile state and an in-memory link. It does not run RadioLib/SX1262, test two separate boards, NVS restart behavior, GNSS, antennas or RF. The public zero test key is for this harness only. The simulator sketch is unsigned-in/unsaved online; local source and diagram are retained for reproduction. Open https://wokwi.com/projects/new/esp32-s3, replace sketch.ino with this folder's sketch, and start simulation. Do not paste the private secrets.h into Wokwi.
