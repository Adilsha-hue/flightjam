# FlightJam working software model

Run `./Start-Demo.ps1` from PowerShell or `python -m http.server 8765 --bind 127.0.0.1` from the repository. Open http://127.0.0.1:8765/sim/learning-lab.html . If a server already runs on that port, use it rather than starting a second one.

Click **Run project presentation** for a 25-second demonstration: clean telemetry, complete loss with virtual jammer enabled, recovery, modified data and replay rejection. Live mode produces two original messages per second. Manual scenario selection affects **Send one message**; live telemetry uses clean original messages with the virtual disturbance applied. Run the presentation from a fresh session for clear results. Reset stops the session and clears its results. Pausing stops original transmissions, while the receiver's freshness indicator continues aging.

## What is implemented

- Independent sender and receiver displays with evolving altitude and battery telemetry.
- Binary, big-endian header following the repository layout; JSON teaching payload rather than its packed floats.
- CRC16/CCITT-FALSE and real browser HMAC-SHA256, truncated to 16 bytes.
- Receiver sequence/time guard, held last verified telemetry and a 3-second demo stale warning.
- Software disturbance switch, continuous/burst patterns and strength control.
- CRC-only baseline beside the authenticated receiver, processing the same channel event.
- Original TX counts, losses, acceptance counts, authentication/replay rejection count, cumulative delivery failure chart, event log and CSV export.

The abstract loss probability is `(strength / 100)^2` while the disturbance is active and zero when inactive. Burst mode alternates three-second active and inactive windows. Strength 100 guarantees loss; strength 0 guarantees delivery for clean original messages. Intermediate results are random. This is an educational packet-erasure model, not a calibrated LoRa waveform simulator.

Protected delivery failure is failed original messages divided by original TX count. Replay attempts do not enter that denominator. Accepted counters include accepted replay attempts at the CRC-only receiver. Auth/replay rejection counts messages with valid CRC rejected by HMAC or freshness checks; CRC failures are visible separately in the log. No-response replay attempts under disturbance appear in the log but do not count as original channel losses.

## Project explanation

“My model demonstrates two separate properties: link availability and message authenticity. A virtual jammer reduces availability at both receivers. HMAC prevents modified messages from being accepted, and sequence checks prevent replay. Removing the disturbance restores communication. Authentication alone is not anti-jamming protection.”

Use the component model for the sender/receiver board assignments and `BUILD-AND-UNDERSTAND.md` for hardware planning and firmware gaps. This runs entirely on a laptop and needs no electronic components for demonstration. Physical firmware, dimensioned CAD and laboratory RF validation remain separate work. No interference transmitter is constructed or controlled.

The demo key is public and only for teaching. Browser cryptography needs localhost or another secure context. Session reset clears replay state intentionally; this is not production security or proof of physical hardware operation.

## Verification

The complete guided presentation was exercised in the Codex browser: 31 original transmissions, 10 channel losses during the disturbance phase, 20 authenticated acceptances, one HMAC rejection and one separate replay rejection. The CRC-only receiver accepted both altered and replayed frames. Browser console showed no errors. Counts can vary slightly with timer scheduling. Existing Python codec/replay self-tests passed all seven checks, and Node's syntax check passed the demo script. CSV generation was checked with a received packet and its visible export text; automated download capture was unavailable in the in-app browser, so the export offers a manual download link and copyable text.
