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
last_on_time = {}    # last time device turned ON
last_off_time = {}   # last time device turned OFF
uptimes = {}         # list of ON durations
downtimes = {}       # list of OFF durations

on_emojis = ["🌞","☀️","💡","✨","🔆","🌈","🌻","💛","😄","😃","😁","😎","🤩","🥳","🌸","🌼","🌷","🍀","🥰","😍","💖"]
off_emojis = ["🌑","🌧️","💤","😔","😢","😭","😡","😠","🖤","😱","😤","🤬","🥶"]

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
    new_status = request.args.get("status", "OFF").upper()  # ON / OFF
    now = time.time()

    # Light turned ON
    if new_status == "ON" and status.get(device_id) != "ON":
        # Calculate downtime
        downtime = 0
        if device_id in last_off_time:
            downtime = now - last_off_time[device_id]
            downtimes.setdefault(device_id, []).append(downtime)

        downtime_str = format_duration(downtime)
        emoji = random.choice(on_emojis)
        send_message(f"{emoji} Свет включился!\nЕго не было: {downtime_str}")

        status[device_id] = "ON"
        last_on_time[device_id] = now

    # Light turned OFF
    elif new_status == "OFF" and status.get(device_id) == "ON":
        status[device_id] = "OFF"
        on_time = last_on_time.get(device_id, now)
        duration = now - on_time
        uptimes.setdefault(device_id, []).append(duration)
        last_off_time[device_id] = now

        duration_str = format_duration(duration)
        emoji = random.choice(off_emojis)
        send_message(f"{emoji} Свет погас!\nОн горел: {duration_str}")

    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
