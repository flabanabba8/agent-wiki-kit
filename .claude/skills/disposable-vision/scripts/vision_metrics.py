#!/usr/bin/env python3
"""Local job metrics and optional network sampling; counters include ALL host traffic.

Run --seconds 60 while the main session is busy to correlate traffic with RTT.
No prompts, image data, addresses, or credentials are recorded.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import time

STATE = Path(os.environ.get('VISION_WORKER_STATE',
             str(Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'disposable-vision'))).expanduser()


def network_bytes():
    try:
        routes = Path('/proc/net/route').read_text().splitlines()[1:]
        interface = next(line.split()[0] for line in routes if line.split()[1] == '00000000')
        return {f'host_{direction}_bytes': int(Path(f'/sys/class/net/{interface}/statistics/{direction}_bytes').read_text())
                for direction in ('tx', 'rx')}
    except (OSError, StopIteration, ValueError, IndexError):
        return {}


def record(**values):
    try:
        STATE.mkdir(parents=True, exist_ok=True)
        values['timestamp'] = datetime.now(timezone.utc).isoformat()
        session = os.environ.get('CODEX_THREAD_ID')
        if session:
            values['parent_session'] = session
        # One short O_APPEND write, so overlapping jobs do not interleave JSON lines.
        fd = os.open(STATE / 'metrics.jsonl', os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(fd, (json.dumps(values) + '\n').encode())
        finally:
            os.close(fd)
    except OSError:
        pass  # Metrics must not make a completed image job fail.


@contextmanager
def measured_job(kind, **values):
    before = network_bytes()
    start = time.monotonic()
    status = 'failed'
    try:
        yield values
        status = 'ok'
    finally:
        after = network_bytes()
        delta = {k: after[k] - v for k, v in before.items() if k in after and after[k] >= v}
        record(kind=kind, status=status, elapsed_seconds=round(time.monotonic() - start, 3),
               **values, **delta)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=0, help='Sample traffic/RTT each second; otherwise show recent metrics')
    args = parser.parse_args()
    if not 0 <= args.seconds <= 3600:
        parser.error('seconds must be between 0 and 3600')
    if not args.seconds:
        path = STATE / 'metrics.jsonl'
        if path.exists():
            from collections import deque
            with path.open() as stream:
                print(''.join(deque(stream, maxlen=20)), end='')
        return
    until = time.monotonic() + args.seconds
    while time.monotonic() < until:
        start = time.monotonic()
        before = network_bytes()
        rtt = None
        try:
            result = subprocess.run(['ping', '-n', '-c', '1', '-W', '1', '1.1.1.1'],
                                    capture_output=True, text=True, timeout=2)
            match = re.search(r'time[=<]([\d.]+)', result.stdout)
            if match:
                rtt = float(match[1])
        except (OSError, subprocess.TimeoutExpired):
            pass
        time.sleep(max(0, min(1, until - start) - (time.monotonic() - start)))
        elapsed = time.monotonic() - start
        after = network_bytes()
        delta = {k: after[k] - v for k, v in before.items() if k in after and after[k] >= v}
        row = dict(kind='network_sample', elapsed_seconds=round(elapsed, 3), internet_rtt_ms=rtt, **delta)
        record(**row)
        print(json.dumps(row), flush=True)


if __name__ == '__main__':
    main()


def child_env():
    """Environment for a worker process. Variables whose names start with a prefix listed in
    VISION_WORKER_DROP_ENV_PREFIXES (comma separated) are dropped, so a host application's own
    session variables do not leak into a nested worker. The default drops nothing."""
    prefixes = tuple(p.strip() for p in os.environ.get('VISION_WORKER_DROP_ENV_PREFIXES', '').split(',') if p.strip())
    return {k: v for k, v in os.environ.items() if not (prefixes and k.startswith(prefixes))}
