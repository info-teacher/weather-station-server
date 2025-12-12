from flask import Flask, request
import requests
import time

TOKEN = "8513191267:AAE1_qvgvjHR4g5-cONFN4CB-r_NtM4rHdk"
CHAT_ID = "945281794"

app = Flask(__name__)

current_temp = None
current_hum = None
last_update = 0

ROOM = {
    "temp": (20, 24),
    "hum": (40, 60)
}

def send_message(text):
    requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                 params={"chat_id": CHAT_ID, "text": text})

@app.route("/data", methods=["POST"])
def receive_data():
    global current_temp, current_hum, last_update

    data = request.json
    temp = data.get("temp")
    hum = data.get("hum")

    current_temp = temp
    current_hum = hum
    last_update = time.time()

    check_values(temp, hum)

    return {"status": "ok"}

def check_values(temp, hum):
    t_min, t_max = ROOM["temp"]
    h_min, h_max = ROOM["hum"]

    if temp < t_min:
        send_message(f"⚠️ Температура низкая: {temp}°C. Подними отопление или закрой окна.")
    elif temp > t_max:
        send_message(f"⚠️ Температура высокая: {temp}°C. Проветри помещение.")

    if hum < h_min:
        send_message(f"⚠️ Влажность низкая: {hum}%. Нужно увлажнить воздух.")
    elif hum > h_max:
        send_message(f"⚠️ Влажность высокая: {hum}%. Проветри или уменьшай испарения.")

@app.route("/status")
def status():
    return {
        "temperature": current_temp,
        "humidity": current_hum,
        "last_update": last_update
    }

@app.route("/cron")
def cron_send():
    if current_temp is not None:
        send_message(f"🌡️Температура: {current_temp}°C\n💧Влажность: {current_hum}%")
    return "sent"

if name == "__main__":
    app.run()
