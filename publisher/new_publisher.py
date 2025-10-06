#!/usr/bin/env python3
"""
IoT Device Event Stream Generator (with device startup/provisioning)

Simulates an event stream of heterogeneous telemetry:
- Legacy platform extension: platform_extension_ticks (0–3000)
- New platform extension: platform_extension_mm (-150 to 150)
- Battery charge (%)
- Platform height (mm)

Adds a "device_startup" event that advertises a new device using a
provision token (HMAC-SHA256 over a device serial with a shared secret).
When a startup event is emitted, the device is added to the active fleet.

CLI/ENV:
  --num-devices N            initial devices seeded (default 5; ENV NUM_DEVICES)
  --message-interval S       seconds between messages (default 0.2; ENV MESSAGE_INTERVAL)
  --malformed-prob P         probability [0..1] of malformed event (default 0.1; ENV MALFORMED_PROB)
  --new-device-rate R        probability [0..1] per cycle to emit a device_startup (default 0.02; ENV NEW_DEVICE_RATE)
  --secret SECRET            shared HMAC secret (default ABLE-SECRET; ENV PROVISION_SECRET)
"""

import argparse
import hmac
import hashlib
import json
import os
import random
import string
import time
from typing import Dict, List

# ----------------------------
# Defaults (overridable by env/CLI)
# ----------------------------
DEFAULT_NUM_DEVICES = int(os.getenv("NUM_DEVICES", "5"))
DEFAULT_MESSAGE_INTERVAL = float(os.getenv("MESSAGE_INTERVAL", "0.2"))
DEFAULT_MALFORMED_PROB = float(os.getenv("MALFORMED_PROB", "0.1"))
DEFAULT_NEW_DEVICE_RATE = float(os.getenv("NEW_DEVICE_RATE", "0.02"))
DEFAULT_SECRET = os.getenv("PROVISION_SECRET", "ABLE-SECRET")

EVENT_TYPES = [
    "platform_extension_ticks",
    "platform_extension_mm",
    "battery_charge",
    "platform_height_mm",
]

FIRMWARE_POOL = ["1.0.0", "1.1.0", "1.1.1", "2.0.0-beta"]


# ----------------------------
# Helpers
# ----------------------------
def random_serial(prefix: str = "AI-", n: int = 6) -> str:
    return prefix + "".join(random.choices(string.hexdigits.upper(), k=n))


def sign_serial(secret: str, serial: str) -> str:
    mac = hmac.new(secret.encode("utf-8"),
                   serial.encode("utf-8"), hashlib.sha256)
    return mac.hexdigest()


def generate_device_startup(secret: str) -> dict:
    serial = random_serial()
    token = sign_serial(secret, serial)
    return {
        "event_type": "device_startup",
        "serial": serial,
        "provision_token": token,
        "firmware": random.choice(FIRMWARE_POOL),
        "timestamp": time.time(),
    }


def generate_event(device_id: int, malformed_prob: float) -> dict:
    """Randomly generate a valid or malformed telemetry event."""
    if random.random() < malformed_prob:
        return generate_malformed(device_id)

    event_type = random.choice(EVENT_TYPES)

    if event_type == "platform_extension_ticks":
        value = random.randint(0, 3000)
    elif event_type == "platform_extension_mm":
        value = random.randint(-150, 150)
    elif event_type == "battery_charge":
        value = round(random.uniform(10, 100), 1)
    else:  # platform_height_mm
        value = random.randint(0, 200)

    return {
        "device_id": device_id,
        "event_type": event_type,
        "value": value,
        "timestamp": time.time(),
    }


def generate_malformed(device_id: int) -> dict:
    """Randomly generate a malformed event."""
    options = [
        {},  # empty
        {"device_id": device_id},  # missing fields
        {"event_type": "platform_extension_mm"},  # missing value
        {"event_type": "battery_charge", "value": "high"},  # wrong type
        {"device_id": device_id, "value": 123},  # missing event_type
    ]
    return random.choice(options)


# ----------------------------
# Main loop
# ----------------------------
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-devices", type=int, default=DEFAULT_NUM_DEVICES)
    parser.add_argument("--message-interval", type=float,
                        default=DEFAULT_MESSAGE_INTERVAL)
    parser.add_argument("--malformed-prob", type=float,
                        default=DEFAULT_MALFORMED_PROB)
    parser.add_argument("--new-device-rate", type=float, default=DEFAULT_NEW_DEVICE_RATE,
                        help="Probability per cycle to emit a device_startup")
    parser.add_argument("--secret", type=str, default=DEFAULT_SECRET,
                        help="Shared secret used to sign device serials")

    args = parser.parse_args()

    num_devices: int = max(0, args.num_devices)
    message_interval: float = max(0.0, args.message_interval)
    malformed_prob: float = min(max(args.malformed_prob, 0.0), 1.0)
    new_device_rate: float = min(max(args.new_device_rate, 0.0), 1.0)
    secret: str = args.secret

    # Active devices: start with ids 1..num_devices
    active_devices: List[int] = list(range(1, num_devices + 1))
    next_device_id = (active_devices[-1] + 1) if active_devices else 1

    print("Starting device event stream generator...")
    print(
        f"(seeded devices: {active_devices or 'none'}; new-device-rate={new_device_rate})")

    try:
        while True:
            # Occasionally emit a device_startup to introduce a new unit
            if random.random() < new_device_rate:
                startup = generate_device_startup(secret)
                print(json.dumps(startup))  # announce startup
                # Simulate that the backend will accept and assign an id; here we just add a new numeric id
                active_devices.append(next_device_id)
                next_device_id += 1

            # If there are active devices, emit a telemetry event for one of them
            if active_devices:
                device_id = random.choice(active_devices)
                event = generate_event(device_id, malformed_prob)
                print(json.dumps(event))

            time.sleep(message_interval)

    except KeyboardInterrupt:
        print("\nGenerator stopped.")


if __name__ == "__main__":
    main()
