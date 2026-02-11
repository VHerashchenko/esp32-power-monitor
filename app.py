from flask import Flask, request
import time
import requests
import os
import threading

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

last_seen = {}       # time of last ping
status = {}          # "ON" or "OFF"
last_on_time = {}    # time when the device last turned ON
last_off_time = {}   # time when the device last turned OFF
intervals = {}       # list of ON durations
downtimes = {}       # list of OFF durations

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

    # Device was OFF or first ping
    if device_id not in status or status[device_id] == "OFF":
        # Calculate downtime if we have a previous OFF time
        downtime = 0
        if device_id in last_off_time:
            downtime = now - last_off_time[device_id]
            if device_id not in downtimes:
                downtimes[device_id] = []
            downtimes[device_id].append(downtime)

        downtime_str = format_duration(downtime)
        send_message(f"💡 Light turned ON\nIt was OFF for: {downtime_str}")

        status[device_id] = "ON"
        last_on_time[device_id] = now

    last_seen[device_id] = now
    return "OK"

def monitor():
    while True:
        now = time.time()
        for device_id in list(last_seen.keys()):
            # If no ping for >60 seconds and device was ON
            if now - last_seen[device_id] > 60 and status.get(device_id) == "ON":
                status[device_id] = "OFF"
                on_time = last_on_time.get(device_id, now)
                duration = now - on_time
                if device_id not in intervals:
                    intervals[device_id] = []
                intervals[device_id].append(duration)

                last_off_time[device_id] = now

                duration_str = format_duration(duration)
                send_message(f"⚡ Light turned OFF\nIt was ON for: {duration_str}")

                print(f"Device {device_id} was ON for {duration_str}")

        time.sleep(10)

# Start monitoring thread
threading.Thread(target=monitor, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
