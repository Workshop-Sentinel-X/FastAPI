import hashlib
import hmac
import json
import time

import paho.mqtt.client as mqtt
from fastapi import FastAPI

SECRET = b"dev-secret-change-me"  # same key as the ESP8266
BROKER = "localhost"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
app = FastAPI()


def sign(device_id, timestamp, m):
    # String signed on both sides, e.g. SENTINEL-X-01|1775376120|21.80|44.50|0|142.30
    text = f"{device_id}|{timestamp}|{m['temperature']:.2f}|{m['humidity']:.2f}|{m['motion_detected']}|{m['distance_cm']:.2f}"
    return hmac.new(SECRET, text.encode(), hashlib.sha256).hexdigest()


def send_to_anomaly_model(frame):
    print("VALID ->", frame["metrics"])  # TODO: plug IA 2's model here


def on_message(c, userdata, msg):
    try:
        frame = json.loads(msg.payload)
        valid = hmac.compare_digest(
            sign(frame["device_id"], frame["timestamp"], frame["metrics"]), frame["signature"])
    except Exception:
        valid = False  # malformed frame = rejected too

    if not valid:
        print("REJECTED ->", msg.payload)
        c.publish("sentinel/alerts", json.dumps({
            "timestamp": int(time.time()),
            "source": "GATEWAY_SECURITY_FILTER",
            "event_type": "CYBER_SPOOFING",
        }))
        return

    send_to_anomaly_model(frame)


def on_connect(c, userdata, flags, reason_code, properties):
    print("Connected to broker")
    c.subscribe("sentinel/telemetry")  # here so it re-subscribes after a broker restart


@app.on_event("startup")
def start_mqtt():
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, 1883)
    client.loop_start()
