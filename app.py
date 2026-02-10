from flask import Flask, request
import time
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

last_seen = {}
status = {}

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text
    })

@app.route("/ping")
def ping():
    device_id = request.args.get("id", "unknown")
    now = time.time()

    if device_id not in status or status[device_id] == "OFF":
        send_message("💡 Свет появился")
        status[device_id] = "ON"

    last_seen[device_id] = now
    return "OK"

def monitor():
    while True:
        now = time.time()
        for device_id in list(last_seen.keys()):
            if now - last_seen[device_id] > 60 and status.get(device_id) == "ON":
                send_message("⚡ Свет пропал")
                status[device_id] = "OFF"
        time.sleep(10)

import threading
threading.Thread(target=monitor, daemon=True).start()

if __name__ == "__main__":
    app.run()
