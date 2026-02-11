from flask import Flask, request
import time
import requests
import os
import threading
import random
import json

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

STATE_FILE = "state.json"

# --- Device tracking ---
status = {}          # "ON" or "OFF"
last_seen = {}       # last ping time
last_on_time = {}    # last time device turned ON
last_off_time = {}   # last time device turned OFF
intervals = {}
downtimes = {}

on_emojis = ["🌞","☀️","💡","✨","🔆","🌻","💛","😄","😃","😁","😎","🤩","🥳","🌸","🌼","🌷","🍀"]
off_emojis = ["🌧️","💤","😔","😢","😭","😡","😠","🖤","😱","😤","🤬","🥶"]

# ------------------ STATE ------------------

def save_state():
    data = {
        "status": status,
        "last_on_time": last_on_time,
        "last_off_time": last_off_time
    }
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print("Failed to save state:", e)


def load_state():
    global status, last_on_time, last_off_time
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            status = data.get("status", {})
            last_on_time = data.get("last_on_time", {})
            last_off_time = data.get("last_off_time", {})
            print("State loaded from file")
    except:
        print("No previous state found")

# ------------------ TELEGRAM ------------------

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": text
        }, timeout=5)
    except Exception as e:
        print("Failed to send Telegram message:", e)

# ------------------ UTILS ------------------

def format_duration(seconds):
    if seconds is None:
        return "unknown"

    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    parts = []
    if h > 0:
        parts.append(f"{h}h")
    if m > 0:
        parts.append(f"{m}m")
    parts.append(f"{s}s")

    return " ".join(parts)

# ------------------ ROUTES ------------------

@app.route("/ping")
def ping():
    device_id = request.args.get("id", "unknown")
    now = time.time()

    last_seen[device_id] = now

    # First time initialization (no fake ON message)
    if device_id not in status:
        status[device_id] = "ON"
        last_on_time[device_id] = now
        last_off_time[device_id] = None
        save_state()
        print(f"{device_id} initialized as ON")
        return "OK"

    return "OK"

# ------------------ MONITOR ------------------

def monitor():
    while True:
        load_state()  # ensure state is restored after sleep
        now = time.time()

        for device_id in list(last_seen.keys()):

            # -------- TURN OFF --------
            if status.get(device_id) == "ON" and now - last_seen[device_id] > 90:
                status[device_id] = "OFF"

                on_time = last_on_time.get(device_id)
                duration = now - on_time if on_time else None

                last_off_time[device_id] = now
                save_state()

                duration_str = format_duration(duration)
                emoji = random.choice(off_emojis)

                send_message(
                    f"🌑🌑{emoji} Power Lost\n"
                    f"Online duration: {duration_str}"
                )

                print(f"{device_id} OFF, was ON for {duration_str}")

            # -------- TURN ON --------
            elif status.get(device_id) == "OFF" and now - last_seen[device_id] <= 90:
                status[device_id] = "ON"

                off_time = last_off_time.get(device_id)
                downtime = now - off_time if off_time else None

                last_on_time[device_id] = now
                save_state()

                downtime_str = format_duration(downtime)
                emoji = random.choice(on_emojis)

                send_message(
                    f"🔵🔵{emoji} Power Restored\n"
                    f"Offline duration: {downtime_str}"
                )

                print(f"{device_id} ON, was OFF for {downtime_str}")

        time.sleep(10)

# ------------------ STARTUP ------------------

if __name__ == "__main__":
    load_state()
    threading.Thread(target=monitor, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

