"""Reproducible telemetry redundancy experiment; no RF transmission or hardware.

Packet-erasure model, fixed illustrative latency, duplicated telemetry on two
links with sequence de-duplication. Does not model a real radio waveform.
"""
import argparse
import csv
import math
import random
from pathlib import Path

SCENARIOS = [
    ('Clean primary only', 0.0, None, 0.0),
    ('Primary blocked, no backup', 1.0, None, 0.0),
    ('Primary blocked, clean backup', 1.0, 0.0, 0.0),
    ('Primary blocked, backup 2% loss', 1.0, 0.02, 0.0),
    ('Both links blocked', 1.0, 1.0, 0.0),
    ('Two independent links, each 30% loss', 0.3, 0.3, 0.0),
    ('Same links plus 20% common outage', 0.3, 0.3, 0.2),
]


def run(n, seed, primary_loss, backup_loss, common_outage):
    rng = random.Random(seed)
    received = primary = backup = duplicates = 0
    latency_sum = 0
    for _ in range(n):
        common = rng.random() < common_outage
        p = rng.random() >= primary_loss and not common
        b = backup_loss is not None and rng.random() >= backup_loss and not common
        primary += p
        backup += b
        duplicates += p and b
        received += p or b
        latency_sum += 80 if p else 120 if b else 0
    return dict(sent=n, received=received, lost=n-received,
                primary_delivered=primary, backup_delivered=backup,
                duplicates_discarded=duplicates,
                delivery_percent=100*received/n,
                mean_latency_ms=latency_sum/received if received else None)


def interval(k, n):
    z = 1.96
    p = k/n
    d = 1+z*z/n
    center = (p+z*z/(2*n))/d
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return 100*max(0, center-half), 100*min(1, center+half)


def checks():
    assert run(100, 7, 0, None, 0)['received'] == 100
    assert run(100, 7, 1, None, 0)['received'] == 0
    assert run(100, 7, 1, 0, 0)['received'] == 100
    assert run(100, 7, 1, 1, 0)['received'] == 0
    result = run(100, 7, 0, 0, 0)
    assert result['received'] == 100 and result['duplicates_discarded'] == 100
    assert run(100, 7, 0, 0, 1)['received'] == 0
    print('PASS: six boundary/accounting checks')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--packets', type=int, default=10000)
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--out', type=Path, default=Path('out/redundancy-results.csv'))
    args = ap.parse_args()
    if args.packets <= 0:
        ap.error('--packets must be positive')
    checks()
    rows = []
    for name, p, b, c in SCENARIOS:
        r = run(args.packets, args.seed, p, b, c)
        expected = 100*(1-c)*(1-p*(b if b is not None else 1))
        lo, hi = interval(r['received'], args.packets)
        r.update(scenario=name, primary_loss=p, backup_loss=b, common_outage=c,
                 model_expected_percent=expected, ci95_low=lo, ci95_high=hi,
                 seed=args.seed)
        rows.append(r)
        print(f"{name}: {r['delivery_percent']:.2f}% delivered "
              f"({r['received']}/{args.packets}); model expectation {expected:.2f}%")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'Results: {args.out}')


if __name__ == '__main__':
    main()
