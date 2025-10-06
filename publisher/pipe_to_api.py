#!/usr/bin/env python3
import sys
import json
import os
import time
import signal
import argparse
import urllib.request


def post_batch(endpoint: str, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as resp:
        body = resp.read().decode("utf-8")
        return body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=os.getenv("INGEST_URL", "http://localhost:8000/ingest"))
    parser.add_argument("--batch", type=int, default=int(os.getenv("BATCH", "1")))
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    buffer = []
    interrupted = False

    def _sigint(_signum, _frame):
        nonlocal interrupted
        interrupted = True
    signal.signal(signal.SIGINT, _sigint)

    for line in sys.stdin:
        if interrupted:
            break
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if args.verbose:
                print(f"-> {obj}", flush=True)
            buffer.append(obj)
        except json.JSONDecodeError:
            buffer.append({"_raw": line})
        if len(buffer) >= args.batch:
            try:
                out = post_batch(args.url, buffer if args.batch > 1 else buffer[0])
                print(out, flush=True)
            except Exception as e:
                print(f"ERROR posting batch: {e}", file=sys.stderr, flush=True)
            buffer.clear()

    if buffer and not interrupted:
        try:
            out = post_batch(args.url, buffer if args.batch > 1 else buffer[0])
            print(out, flush=True)
        except Exception as e:
            print(f"ERROR posting final batch: {e}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
