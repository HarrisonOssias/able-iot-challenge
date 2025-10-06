#!/usr/bin/env python3
"""
IoT Device Event Stream Generator

Simulates an event stream of heterogeneous telemetry:
- Legacy platform extension: platform_extension_ticks (0–3000)
- New platform extension: platform_extension_mm (-150 to 150)
- Battery charge (%)
- Platform height (mm)

Each event is generated individually and randomly. Occasionally generates malformed or incomplete events.
"""

import json
import random
import time

# Configuration
NUM_DEVICES = 5
MESSAGE_INTERVAL = 0.2  # seconds between messages
MALFORMED_PROB = 0.1    # 10% of messages malformed

EVENT_TYPES = ["platform_extension_ticks", "platform_extension_mm", "battery_charge", "platform_height_mm"]

def generate_event(device_id):
    """Randomly generate a valid or malformed event."""
    if random.random() < MALFORMED_PROB:
        return generate_malformed(device_id)
    
    event_type = random.choice(EVENT_TYPES)
    
    if event_type == "platform_extension_ticks":
        value = random.randint(0, 3000)
    elif event_type == "platform_extension_mm":
        value = random.randint(-150, 150)
    elif event_type == "battery_charge":
        value = round(random.uniform(10, 100), 1)
    elif event_type == "platform_height_mm":
        value = random.randint(0, 200)
    
    return {
        "device_id": device_id,
        "event_type": event_type,
        "value": value,
        "timestamp": time.time()
    }

def generate_malformed(device_id):
    """Randomly generate a malformed event."""
    options = [
        {},  # empty
        {"device_id": device_id},  # missing fields
        {"event_type": "platform_extension_mm"},  # missing value
        {"event_type": "battery_charge", "value": "high"},  # wrong type
        {"device_id": device_id, "value": 123},  # missing event_type
    ]
    return random.choice(options)

def main():
    print("Starting device event stream generator...")
    try:
        while True:
            device_id = random.randint(1, NUM_DEVICES)
            event = generate_event(device_id)
            print(json.dumps(event))
            time.sleep(MESSAGE_INTERVAL)
    except KeyboardInterrupt:
        print("\nGenerator stopped.")

if __name__ == "__main__":
    main()
