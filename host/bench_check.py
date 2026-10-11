"""Capture reference telemetry serial logs without flashing or sending radio commands."""
import argparse
import json
import re
import time
from pathlib import Path

TX = re.compile(r"^TX,(\d+),(\d+),(-?\d+)$")
RX = re.compile(r"^RX,OK,(\d+),(\d+),lat_e7=(-?\d+),lon_e7=(-?\d+),alt_mm=(-?\d+),rssi=(-?\d+(?:\.\d+)?)$")

def parse(line):
    if match := TX.fullmatch(line):
        boot, sequence, code = map(int, match.groups())
        return dict(kind="tx", boot=boot, sequence=sequence, code=code)
    if match := RX.fullmatch(line):
        boot, sequence, lat, lon, alt, rssi = match.groups()
        return dict(kind="rx", boot=int(boot), sequence=int(sequence), lat_e7=int(lat), lon_e7=int(lon), alt_mm=int(alt), rssi=float(rssi))
    if line in ("RX,BAD_HEADER", "RX,BAD_TAG", "RX,REPLAY"):
        return dict(kind="reject", reason=line.split(",")[1])
    return dict(kind="other", text=line)

def summarize(events):
    tx = {(e["boot"], e["sequence"]) for e in events if e["kind"] == "tx" and e["code"] == 0}
    rx_events = [e for e in events if e["kind"] == "rx"]
    rx = {(e["boot"], e["sequence"]) for e in rx_events}
    return dict(tx_success=len(tx), tx_errors=sum(e["kind"] == "tx" and e["code"] != 0 for e in events), rx_unique=len(rx), rx_duplicate_logs=len(rx_events)-len(rx), matched=len(tx & rx), observed_delivery_percent=round(100*len(tx & rx)/len(tx), 2) if tx else None, rejections=sum(e["kind"] == "reject" for e in events), note="Capture-window metric only; not a range or RF certification. Missing initial logs can skew results.")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tx-port")
    parser.add_argument("--rx-port")
    parser.add_argument("--seconds", type=int, default=190)
    parser.add_argument("--log", type=Path, help="Analyze an existing JSONL capture")
    parser.add_argument("--output", type=Path, default=Path("out/bench-capture.jsonl"))
    args = parser.parse_args()
    if args.log:
        events = [json.loads(line) for line in args.log.read_text().splitlines() if line.strip()]
    else:
        if not args.tx_port or not args.rx_port or args.tx_port == args.rx_port or args.seconds <= 0:
            parser.error("Provide two different verified serial ports and positive capture duration")
        import serial
        ports = []
        events = []
        buffers = {}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        try:
            for role, name in (("tx", args.tx_port), ("rx", args.rx_port)):
                port = serial.Serial(port=None, baudrate=115200, timeout=0)
                port.port = name
                port.dtr = False
                port.rts = False
                port.open()
                ports.append((role, port))
                buffers[role] = b""
            end = time.monotonic() + args.seconds
            with args.output.open("w", encoding="utf-8") as output:
                while time.monotonic() < end:
                    for role, port in ports:
                        buffers[role] += port.read(port.in_waiting)
                        while b"\n" in buffers[role]:
                            raw, buffers[role] = buffers[role].split(b"\n", 1)
                            line = raw.decode("utf-8", errors="replace").strip()
                            if not line:
                                continue
                            event = dict(parse(line), port_role=role, time=time.time())
                            events.append(event)
                            output.write(json.dumps(event)+"\n")
                            output.flush()
                            print(role, line, flush=True)
                    time.sleep(0.02)
        finally:
            for _, port in ports:
                port.close()
    print(json.dumps(summarize(events), indent=2))

if __name__ == "__main__":
    main()
