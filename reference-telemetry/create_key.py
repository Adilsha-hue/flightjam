"""Create the local shared development key; never prints or commits its value."""
from pathlib import Path
import secrets

target = Path(__file__).parent / 'include' / 'secrets.h'
target.parent.mkdir(exist_ok=True)
if target.exists():
    raise SystemExit('Key already exists. Preserved existing key.')
target.write_text('#pragma once\n#include <stdint.h>\nstatic const uint8_t TELEMETRY_KEY[32] = {' +
                  ','.join('0x%02x' % b for b in secrets.token_bytes(32)) + '};\n', encoding='utf-8')
print('Created local shared key. Build both nodes from this directory; do not publish secrets.h.')
