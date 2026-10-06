# Fake ESP8266. Run: python simulate.py        -> valid frames
#                    python simulate.py fake   -> forged frames (wrong key)
import json
import random
import sys
import time

import paho.mqtt.client as mqtt

import main

if len(sys.argv) > 1 and sys.argv[1] == "fake":
    main.SECRET = b"wrong-key"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect("localhost", 1883)
client.loop_start()  # background thread: keeps the connection alive

while True:
    ts = int(time.time())
    metrics = {
        "temperature": round(21.5 + random.uniform(-0.3, 0.3), 2),
        "humidity": round(44 + random.uniform(-1, 1), 2),
        "motion_detected": 0,
        "distance_cm": round(140 + random.uniform(-2, 2), 2),
    }
    frame = {"device_id": "SENTINEL-X-01", "timestamp": ts, "metrics": metrics,
             "signature": main.sign("SENTINEL-X-01", ts, metrics)}
    client.publish("sentinel/telemetry", json.dumps(frame))
    print(frame)
    time.sleep(1)
