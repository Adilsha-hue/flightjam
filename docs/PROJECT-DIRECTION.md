# Project direction: private and resilient RC telemetry

The project demonstrates authenticated telemetry, encrypted position reports and redundant delivery. It does not demonstrate aircraft invisibility or real-world jammer operation.

Open `sim/flight-world.html` through the local server. Enable backup, then turn virtual jammer ON at 100%: the simulated primary is blocked and the receiver uses the independent backup. Disable backup to see total primary-link loss. Enable Block both links to show common failure even with backup. The receiver keeps its last decoded position and reports increasing data age. An outside receiver cannot decode captured AES-GCM telemetry with its different key.

Backup is idealized: zero loss, no additional delay or capacity constraint, unaffected by primary disturbance unless both links are explicitly blocked. There is no physical radio or automatic firmware failover in this demonstration. The guided explanation temporarily disables backup to retain its existing loss/recovery lesson; re-enable backup for the redundancy experiment.

Research and numerical experiments are in `SIMULATION-RESEARCH.md`; hardware assignments and unresolved physical validation are in `../hardware/HARDWARE-DESIGN.md`. Keep original firmware unchanged until exact board revisions and a real backup transport have been selected. A defensible report must distinguish the implemented browser encryption, modeled channel behavior, and untested hardware.
