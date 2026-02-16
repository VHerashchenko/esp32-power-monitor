from flask import Flask, request
import time
import requests
import os
import random

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# --- Device tracking ---
status = {}  # "ON" or "OFF"

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
    if seconds is None or seconds < 0:
        return "unknown"
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
    event_time = request.args.get("time")  # timestamp from ESP32

    try:
        event_time = float(event_time)
    except (TypeError, ValueError):
        event_time = time.time()  # fallback if not provided

    now = time.time()  # current server time
    # time difference between now and last event reported by ESP32
    duration = now - event_time

    # --- Light turned ON ---
    if new_status == "ON" and status.get(device_id) != "ON":
        emoji = random.choice(on_emojis)
        send_message(f"🔵🔵{emoji} Power Restored\nOffline duration: {format_duration(duration)}")
        status[device_id] = "ON"

    # --- Light turned OFF ---
    elif new_status == "OFF" and status.get(device_id) == "ON":
        emoji = random.choice(off_emojis)
        send_message(f"🌑🌑{emoji} Power Lost\nOnline duration: {format_duration(duration)}")
        status[device_id] = "OFF"

    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
