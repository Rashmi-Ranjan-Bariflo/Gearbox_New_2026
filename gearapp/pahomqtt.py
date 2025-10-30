import time
import os
from datetime import datetime, date
import paho.mqtt.client as mqtt
from telegram import Bot
from telegram.ext import Updater, CommandHandler
from .models import gear_value
import asyncio
import threading

# MQTT Configuration
MQTT_BROKER = 'mqttbroker.bc-pl.com'
MQTT_PORT = 1883
MQTT_TOPIC = [
    'factory/gearbox1/input/rpm',
    'factory/gearbox1/out1/rpm',
    'factory/gearbox1/out2/rpm',
    'factory/gearbox1/out3/rpm',
    'factory/gearbox1/out4/rpm',
]
MQTT_USER = 'mqttuser'
MQTT_PASSWORD = 'Bfl@2025'

# Telegram Configuration
#TELEGRAM_BOT_TOKEN = '7119219406:AAHsLe6kqLiQmJMeTPCnYR3rg15__lvr92k'
#TELEGRAM_GROUPCHAT_IDS = [-1002559440335]

# Globals
last_message_time = datetime.now()
alert_sent = False
data_message_sent = False
NO_DATA_THRESHOLD = 5
last_rpm_file = "last_input_rpm.txt"
first_data_received = False
first_rpm_after_restart = None
last_input_rpm = None
last_rpm_received = None

topic_aliases = {
    "factory/gearbox1/input/rpm": "Input_rpm",
    "factory/gearbox1/out1/rpm": "Output1_rpm",
    "factory/gearbox1/out2/rpm": "Output2_rpm",
    "factory/gearbox1/out3/rpm": "Output3_rpm",
    "factory/gearbox1/out4/rpm": "Output4_rpm",
}

bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def async_send_message(bot, chat_id, message):
    try:
        bot.send_message(chat_id=chat_id, text=message)
        print(f"✅ Telegram message sent: {message}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

def send_telegram_message(message):
    for chat_id in TELEGRAM_GROUPCHAT_IDS:
        asyncio.run(async_send_message(bot, chat_id, message))

def save_last_input_rpm(value):
    try:
        with open(last_rpm_file, "w") as f:
            f.write(str(value))
        print(f"Saved last input RPM: {value}")
    except Exception as e:
        print(f"❌ Error saving input RPM: {e}")

def read_last_input_rpm():
    if os.path.exists(last_rpm_file):
        try:
            with open(last_rpm_file, "r") as f:
                return float(f.read())
        except Exception as e:
            print(f"❌ Error reading input RPM: {e}")
            return None
    return None

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT broker.")
        for topic in MQTT_TOPIC:
            client.subscribe(topic)
            print(f"Subscribed to: {topic}")
    else:
        print(f"❌ Connection failed. Code: {rc}")

def on_message(client, userdata, msg):
    global last_message_time, alert_sent, data_message_sent
    global first_data_received, first_rpm_after_restart, last_rpm_received, last_input_rpm

    try:
        values = msg.payload.decode('utf-8')
        topic_alias = topic_aliases.get(msg.topic, msg.topic)

        try:
            current_rpm = float(values)
        except ValueError:
            return

        if msg.topic == 'factory/gearbox1/input/rpm':
            if current_rpm == 0.0 and not first_data_received:
                print("⚠️ Skipping 0.0 RPM after restart (waiting for valid RPM)")
                return

            last_rpm_received = current_rpm

            if not data_message_sent:
                send_telegram_message(
                    f"\U0001F4CA New Data received\n"
                    f"Time: {datetime.now().strftime('%H:%M:%S')}\n"
                    f"Status: ✅ Connecting\n"
                    f"First Input RPM after restart: {current_rpm}"
                )
                data_message_sent = True
                alert_sent = False

            if not first_data_received:
                first_rpm_after_restart = current_rpm
                last_rpm_before_restart = read_last_input_rpm()

                if last_rpm_before_restart is not None:
                    rpm_diff = abs(first_rpm_after_restart - last_rpm_before_restart)
                    condition_text = ">= 20" if rpm_diff > 20 else "<= 20"

                    message = (
                        f"\U0001F501 Server Restarted\n"
                        f"Last Input RPM before stop: {last_rpm_before_restart}\n"
                        f"First Input RPM after restart: {first_rpm_after_restart}"
                    )
                    send_telegram_message(message)
                else:
                    print("⚠️ No previous RPM found for restart comparison.")

                first_data_received = True

            # Compare with previous entry (only based on value field)
            recent_rpms = gear_value.objects.filter(value__startswith="Input_rpm").order_by('-date', '-time')[:2]
            if recent_rpms.count() == 2:
                try:
                    previous_rpm = float(recent_rpms[1].value.split(':')[1].strip())
                    rpm_diff = abs(current_rpm - previous_rpm)
                    if previous_rpm == 0 and current_rpm == 0:
                        return
                    if rpm_diff > 20:
                        message = (
                            f"📈 Input RPM Change Detected\n"
                            f"Old Input RPM : {previous_rpm}\n"
                            f"New Input RPM : {current_rpm}"
                        )
                        send_telegram_message(message)
                except:
                    pass

            last_input_rpm = current_rpm

        formatted_value = f"{current_rpm:.2f}"
        print(f"Saving to DB: {topic_alias} : {formatted_value}")
        gear_value.objects.create(value=f"{topic_alias} : {formatted_value}")

        today = date.today()
        gear_value.objects.exclude(date=today).delete()
        last_message_time = datetime.now()

    except Exception as e:
        print(f"❌ Error processing MQTT message: {e}")

def mqtt_connect():
    global last_message_time, alert_sent, data_message_sent, last_input_rpm, first_data_received

    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"❌ MQTT connect error: {e}")
        return

    client.loop_start()

    try:
        while True:
            now = datetime.now()
            time_diff = (now - last_message_time).total_seconds()

            print(f"Last data received {time_diff:.2f} seconds ago.")

            if time_diff > NO_DATA_THRESHOLD:
                if not alert_sent:
                    if last_rpm_received is not None:
                        save_last_input_rpm(last_rpm_received)
                        message = (
                            f"⚠️ No data received since {last_message_time.strftime('%H:%M:%S')}\n"
                            f"Status: ❌ Disconnect\n"
                            f"Last Input RPM before Disconnect: {last_rpm_received}"
                        )
                    else:
                        message = (
                            f"⚠️ No data received since {last_message_time.strftime('%H:%M:%S')} (❌ Disconnect)\n"
                            f"⚠️ No RPM recorded before disconnect."
                        )
                    send_telegram_message(message)
                    alert_sent = True
                    data_message_sent = False
                    first_data_received = False  

            time.sleep(1)

    except KeyboardInterrupt:
        print("MQTT manually stopped.")
        if last_input_rpm is not None:
            save_last_input_rpm(last_input_rpm)
            send_telegram_message(f"Manual stop. Last Input RPM: {last_input_rpm}")
        else:
            send_telegram_message("Manual stop. No Input RPM before shutdown.")
        client.loop_stop()
        client.disconnect()

def check_rpm_changes():
    last_sent_rpm = None
    while True:
        try:
            latest = gear_value.objects.filter(value__startswith='Input_rpm').order_by('-date', '-time').first()
            if latest:
                rpm_str = latest.value.split(':')[1].strip()
                current_rpm = float(rpm_str)

                if last_sent_rpm is None or current_rpm != last_sent_rpm:
                    send_telegram_message(f"Input RPM changed to {current_rpm}")
                    last_sent_rpm = current_rpm
        except Exception as e:
            print(f"Error in RPM check thread: {e}")

        time.sleep(1)

def get_chat_id(update, context):
    chat_id = update.effective_chat.id
    update.message.reply_text(f"Chat ID: {chat_id}")
    print(f"Chat ID: {chat_id}")

def main():
    mqtt_thread = threading.Thread(target=mqtt_connect)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    rpm_monitor_thread = threading.Thread(target=check_rpm_changes)
    rpm_monitor_thread.daemon = True
    rpm_monitor_thread.start()

    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("getchatid", get_chat_id))

    print("🤖 Bot running. Use /getchatid to get chat ID.")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
