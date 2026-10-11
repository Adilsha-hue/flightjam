# Simulation software and experiment

## Researched options

| Tool | Useful layer | Relevant limitation |
|---|---|---|
| [GNU Radio channel models](https://wiki.gnuradio.org/index.php/Dynamic_Channel_Model) | Waveform processing; noise, frequency drift and fading | Requires transmitter/modem and channel models matching the real radio; not a drop-in validation of ESP32 firmware |
| [OMNeT++ / INET wireless tutorial](https://inet.omnetpp.org/docs/tutorials/wireless/doc/index.html) | Network behavior, wireless medium and interference | Model selection and calibration determine what results mean; generic wireless models are not automatically SX1262 models |
| [ns-3](https://www.nsnam.org/about/what-is-ns-3/) | Discrete-event network and protocol experiments | Requires an appropriate radio/module model and a configured toolchain |

These tools were researched, not installed or run in this review. The local test below is a Python packet-level Monte Carlo model. It is suitable for checking the logic and accounting of duplicated telemetry, not for predicting a hardware link budget or resistance to a physical interferer.

## Local reproducible test

```powershell
python host/sim/redundancy_sim.py --packets 10000 --seed 7 --out out/redundancy-results.csv
```

Each original sequence is sent on the primary and, when enabled, a backup link. A receiver delivers each original once; a second copy is discarded. Assumed latency is 80 ms on primary and 120 ms on backup. There are no queues, acknowledgements, retransmissions or calibrated physical parameters. Bernoulli erasures are independent between packets, except that a configured common outage disables both links for a packet.

Test conditions: clean primary, blocked primary without backup, blocked primary with clean backup, blocked primary with imperfect backup, both blocked, two independent imperfect links, and a common outage affecting both. “Blocked” means 100% erasure in the model. It does not specify a jammer waveform or operational RF configuration.

Six deterministic boundary checks verify clean delivery, total loss, backup delivery, both blocked, de-duplication and complete common outage. CSV includes transmitted counts, unique deliveries, drops, duplicates, illustrative latency and Wilson confidence intervals. Confidence intervals reflect randomness under this model; they do not describe uncertainty about real RF hardware.

For a physical project, obtain exact radio models, antenna/installation configuration, range and measured packet-loss data, then choose and calibrate a waveform/network simulator. Encryption protects contents independently of delivery. A backup only helps when it remains usable; interference that blocks both paths still prevents live tracking.
