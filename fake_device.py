import time
import json
import random
import paho.mqtt.client as mqtt

# MQTT Config
BROKER = "mqttbroker.bc-pl.com"
PORT = 1883
USER = "mqttuser"
PASSWORD = "Bfl@2025"

TOPICS = {
    "input": "factory/gearbox1/input/rpm",
    "out1": "factory/gearbox1/out1/rpm",
    "out2": "factory/gearbox1/out2/rpm",
    "out3": "factory/gearbox1/out3/rpm",
    "out4": "factory/gearbox1/out4/rpm",
}

client = mqtt.Client()
client.username_pw_set(USER, PASSWORD)
client.connect(BROKER, PORT, 60)
client.loop_start()

print("✅ Fake device started...")

def send(topic, rpm):
    payload = {
        "ts": int(time.time() * 1000),
        "rpm": round(rpm, 2)
    }

    client.publish(topic, json.dumps(payload))
    print(f"📤 Sent → {topic}: {payload}")


try:
    while True:

        base = random.uniform(100, 200)

        send(TOPICS["input"], base)
        send(TOPICS["out1"], base * 0.6)
        send(TOPICS["out2"], base * 0.4)
        send(TOPICS["out3"], base * 0.25)
        send(TOPICS["out4"], base * 0.25)

        time.sleep(2)

except KeyboardInterrupt:
    print("🛑 Stopped")
    client.disconnect()
