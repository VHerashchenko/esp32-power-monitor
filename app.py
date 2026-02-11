from flask import Flask, request
import time
import requests
import os
import threading
import random

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# --- Device tracking ---
status = {}          # "ON" or "OFF"
last_seen = {}       # last ping time
last_on_time = {}    # last time device turned ON
last_off_time = {}   # last time device turned OFF
intervals = {}       # list of ON durations
downtimes = {}       # list of OFF durations

on_emojis = ["🌞","☀️","💡","✨","🔆","🌻","💛","😄","😃","😁","😎","🤩","🥳","🌸","🌼","🌷","🍀"]
off_emojis = ["🌧️","💤","😔","😢","😭","😡","😠","🖤","😱","😤","🤬","🥶"]

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": text
        }, timeout=5)
    except Exception as e:
        print("Failed to send Telegram message:", e)

def format_duration(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    parts = []
    if h > 0:
        parts.append(f"{h}h")
    if m > 0:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)

@app.route("/ping")
def ping():
    device_id = request.args.get("id", "unknown")
    now = time.time()

    last_seen[device_id] = now

    # Initialize device if first time
    if device_id not in status:
        status[device_id] = "OFF"
        last_on_time[device_id] = 0
        last_off_time[device_id] = now
        intervals[device_id] = []
        downtimes[device_id] = []

    return "OK"

def monitor():
    while True:
        now = time.time()
        for device_id in list(last_seen.keys()):
            # Device should be OFF if no ping for > 60 sec
            if status.get(device_id, "OFF") == "ON" and now - last_seen[device_id] > 60:
                status[device_id] = "OFF"
                on_time = last_on_time.get(device_id, now)
                duration = now - on_time
                intervals.setdefault(device_id, []).append(duration)
                last_off_time[device_id] = now

                duration_str = format_duration(duration)
                emoji = random.choice(off_emojis)
                send_message(f"🌑🌑{emoji} Power Lost\nOnline duration: {duration_str}")
                print(f"Device {device_id} was ON for {duration_str}")

            # Device should be ON if it just pinged and was OFF
            elif status.get(device_id, "OFF") == "OFF" and now - last_seen[device_id] <= 60:
                status[device_id] = "ON"
                downtime = now - last_off_time.get(device_id, now)
                downtimes.setdefault(device_id, []).append(downtime)
                last_on_time[device_id] = now

                downtime_str = format_duration(downtime)
                emoji = random.choice(on_emojis)
                send_message(f"🔵🔵{emoji} Power Restored\nOffline duration: {duration_str}")
                print(f"Device {device_id} turned ON, was OFF for {downtime_str}")

        time.sleep(10)

# Start monitor thread
threading.Thread(target=monitor, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

