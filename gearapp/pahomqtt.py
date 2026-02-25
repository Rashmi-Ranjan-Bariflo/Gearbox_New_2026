import os
import sys
import time
import json
import threading
from datetime import datetime

import paho.mqtt.client as mqtt
from telegram import Bot
from telegram.ext import Updater, CommandHandler

import django
from django.utils import timezone


# ================== Django Setup ==================

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gear_box.settings")
django.setup()

from gearapp.models import GearValue, GearRatio


# ================== Config ==================

MQTT_BROKER = "mqttbroker.bc-pl.com"
MQTT_PORT = 1883

MQTT_TOPICS = [
    "factory/gearbox1/input/rpm",
    "factory/gearbox1/out1/rpm",
    "factory/gearbox1/out2/rpm",
    "factory/gearbox1/out3/rpm",
    "factory/gearbox1/out4/rpm",
]

MQTT_USER = "mqttuser"
MQTT_PASSWORD = "Bfl@2025"

TELEGRAM_BOT_TOKEN = "7119219406:AAHsLe6kqLiQmJMeTPCnYR3rg15__lvr92k"
TELEGRAM_GROUPCHAT_IDS = [-1002559440335]

NO_DATA_THRESHOLD = 10
TELEGRAM_COOLDOWN = 60

# Buffer timeout (seconds)
BUFFER_TIMEOUT = 5


# ================== Topic Mapping ==================

TOPIC_ALIAS = {
    "factory/gearbox1/input/rpm": "Input_rpm",
    "factory/gearbox1/out1/rpm": "Output1_rpm",
    "factory/gearbox1/out2/rpm": "Output2_rpm",
    "factory/gearbox1/out3/rpm": "Output3_rpm",
    "factory/gearbox1/out4/rpm": "Output4_rpm",
}


# ================== Globals ==================

bot = Bot(token=TELEGRAM_BOT_TOKEN)

last_message_time = timezone.now()
last_telegram_alert = 0

# Buffers
data_buffer = {}
buffer_time = {}


# ================== Ratio Calculator ==================

def calculate_ratio_from_row(row):

    input_rpm = row["input"]
    out1 = row["out1"]
    out2 = row["out2"]
    out3 = row["out3"]
    out4 = row["out4"]
    dt = row["time"]

    if input_rpm <= 0:
        print("⚠️ Skipping ratio (input = 0):", dt)
        return

    # Prevent duplicate
    if GearRatio.objects.filter(timestamp=dt).exists():
        print("⚠️ Ratio already exists:", dt)
        return

    r1 = round(out1 / input_rpm, 4)
    r2 = round(out2 / input_rpm, 4)
    r3 = round(out3 / input_rpm, 4)
    r4 = round(out4 / input_rpm, 4)

    GearRatio.objects.create(
        timestamp=dt,
        input_rpm=input_rpm,
        output1_rpm=out1,
        output2_rpm=out2,
        output3_rpm=out3,
        output4_rpm=out4,
        ratio1=r1,
        ratio2=r2,
        ratio3=r3,
        ratio4=r4,
    )

    print("📊 Ratio Saved:", dt)


# ================== Telegram ==================

def send_telegram(msg):

    global last_telegram_alert

    now = time.time()

    if now - last_telegram_alert < TELEGRAM_COOLDOWN:
        return

    last_telegram_alert = now

    for cid in TELEGRAM_GROUPCHAT_IDS:
        try:
            bot.send_message(chat_id=cid, text=msg)
            print("✅ Telegram sent")
        except Exception as e:
            print("❌ Telegram error:", e)


# ================== Payload Parser ==================

def parse_payload(payload):

    # JSON
    try:
        data = json.loads(payload)

        ts = data.get("ts")
        rpm = data.get("rpm")

        if ts is not None and rpm is not None:
            return int(ts), float(rpm)

    except:
        pass

    # Plain float (fallback)
    try:
        rpm = float(payload)
        return None, rpm

    except:
        return None, None


# ================== MQTT ==================

def on_connect(client, userdata, flags, rc):

    if rc == 0:

        print("✅ MQTT Connected")

        for t in MQTT_TOPICS:
            client.subscribe(t)
            print("Subscribed:", t)

    else:
        print("❌ MQTT Failed:", rc)


def on_message(client, userdata, msg):

    global last_message_time
    global data_buffer
    global buffer_time

    try:

        payload = msg.payload.decode().strip()

        ts, rpm = parse_payload(payload)

        if rpm is None or ts is None:
            print("❌ Invalid payload:", payload)
            return


        # Convert timestamp
        device_dt = timezone.make_aware(
            datetime.fromtimestamp(ts / 1000)
        )


        channel = TOPIC_ALIAS.get(msg.topic, msg.topic)


        # Save RPM
        GearValue.objects.create(
            timestamp=device_dt,
            channel=channel,
            rpm=rpm
        )

        print(f"✅ Saved {device_dt} | {channel} | {rpm}")


        # ================= BUFFER =================

        now = time.time()

        if ts not in data_buffer:

            data_buffer[ts] = {
                "input": None,
                "out1": None,
                "out2": None,
                "out3": None,
                "out4": None,
                "time": device_dt
            }

            buffer_time[ts] = now


        row = data_buffer[ts]


        # Store values
        if channel == "Input_rpm":
            row["input"] = rpm

        elif channel == "Output1_rpm":
            row["out1"] = rpm

        elif channel == "Output2_rpm":
            row["out2"] = rpm

        elif channel == "Output3_rpm":
            row["out3"] = rpm

        elif channel == "Output4_rpm":
            row["out4"] = rpm


        # ================= CHECK =================

        if all([
            row["input"] is not None,
            row["out1"] is not None,
            row["out2"] is not None,
            row["out3"] is not None,
            row["out4"] is not None,
        ]):

            calculate_ratio_from_row(row)

            # cleanup
            del data_buffer[ts]
            del buffer_time[ts]


        # ================= CLEAN OLD =================

        expired = []

        for k in buffer_time:

            if now - buffer_time[k] > BUFFER_TIMEOUT:
                expired.append(k)

        for k in expired:
            print("🗑️ Removing stale buffer:", k)
            del data_buffer[k]
            del buffer_time[k]


        last_message_time = timezone.now()


    except Exception as e:

        print("❌ MQTT error:", e)


# ================== MQTT Thread ==================

def mqtt_thread():

    client = mqtt.Client()

    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

    client.on_connect = on_connect
    client.on_message = on_message


    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)

    except Exception as e:
        print("MQTT connect error:", e)
        return


    client.loop_start()

    print("🤖 MQTT Started")


    while True:

        diff = (timezone.now() - last_message_time).total_seconds()

        print(f"Last data: {diff:.1f}s ago")

        if diff > NO_DATA_THRESHOLD:
            send_telegram("⚠️ MQTT: No data received")

        time.sleep(2)


# ================== Telegram Commands ==================

def get_chat_id(update, context):

    cid = update.effective_chat.id

    update.message.reply_text(f"Chat ID: {cid}")

    print("Chat ID:", cid)


# ================== Main ==================

def main():

    t1 = threading.Thread(target=mqtt_thread, daemon=True)
    t1.start()


    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("getchatid", get_chat_id))


    print("🤖 Bot running")

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()