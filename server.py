from flask import Flask, request, send_file
import requests
import time
import io
import matplotlib.pyplot as plt

# ===== TELEGRAM =====
TOKEN = "8513191267:AAE1_qvgvjHR4g5-cONFN4CB-r_NtM4rHdk"
CHAT_ID = "945281794"

app = Flask(__name__)

# ===== ДАННЫЕ =====
current_temp = None
current_hum = None
last_update = 0

history = []  # (time, temp, hum)

# ===== ФЛАГИ СОСТОЯНИЯ =====
alert_flags = {
    "temp_low": False,
    "temp_high": False,
    "hum_low": False,
    "hum_high": False
}

# ===== НОРМЫ =====
ROOM = {
    "temp": (20, 24),
    "hum": (40, 60)
}

# ===== TELEGRAM =====
def send_message(text):
    requests.get(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        params={"chat_id": CHAT_ID, "text": text}
    )

# ===== DATA =====
@app.route("/data", methods=["POST"])
def receive_data():
    global current_temp, current_hum, last_update, history

    data = request.json
    current_temp = data.get("temp")
    current_hum = data.get("hum")
    last_update = time.time()

    history.append((last_update, current_temp, current_hum))
    history = history[-100:]

    check_values()
    return {"status": "ok"}

# ===== ПРОВЕРКА =====
def check_values():
    global alert_flags

    if current_temp is None:
        return

    alerts, advice, health = [], [], []

    tmin, tmax = ROOM["temp"]
    hmin, hmax = ROOM["hum"]

    # Температура
    if current_temp < tmin:
        alerts.append("🧊 Холодно")
        health.append("риск простуды")
        advice.append("повысить отопление")
        if not alert_flags["temp_low"]:
            send_message(f"⚠️ Температура низкая: {current_temp}°C. Проверьте отопление!")
            alert_flags["temp_low"] = True
        alert_flags["temp_high"] = False
    elif current_temp > tmax:
        alerts.append("🥵 Жарко")
        health.append("ухудшение сна и концентрации")
        advice.append("проветрить помещение")
        if not alert_flags["temp_high"]:
            send_message(f"⚠️ Температура высокая: {current_temp}°C. Проветрите помещение!")
            alert_flags["temp_high"] = True
        alert_flags["temp_low"] = False
    else:
        alert_flags["temp_low"] = False
        alert_flags["temp_high"] = False

    # Влажность
    if current_hum < hmin:
        alerts.append("🌵 Сухо")
        health.append("сухость кожи и слизистых")
        advice.append("использовать увлажнитель")
        if not alert_flags["hum_low"]:
            send_message(f"⚠️ Влажность низкая: {current_hum}%. Используйте увлажнитель!")
            alert_flags["hum_low"] = True
        alert_flags["hum_high"] = False
    elif current_hum > hmax:
        alerts.append("🌫 Влажно")
        health.append("риск плесени")
        advice.append("проветривание")
        if not alert_flags["hum_high"]:
            send_message(f"⚠️ Влажность высокая: {current_hum}%. Проветрите помещение!")
            alert_flags["hum_high"] = True
        alert_flags["hum_low"] = False
    else:
        alert_flags["hum_low"] = False
        alert_flags["hum_high"] = False

    sleep_text = sleep_impact()
    forecast = generate_forecast()

    if alerts:
        msg = "🏠 Состояние комнаты\n\n"
        msg += f"🌡 {current_temp}°C\n💧 {current_hum}%\n\n"
        msg += "⚠️ Проблемы:\n" + "\n".join(f"• {a}" for a in alerts)
        msg += "\n\n🩺 Возможные эффекты:\n" + "\n".join(f"• {h}" for h in health)
        msg += "\n\n💡 Советы:\n" + "\n".join(f"• {a}" for a in advice)
        if sleep_text:
            msg += f"\n\n😴 Сон:\n{sleep_text}"
        if forecast:
            msg += f"\n\n🔮 Прогноз:\n{forecast}"

# ===== ПРОГНОЗ =====
def generate_forecast():
    if len(history) < 6:
        return None

    t0, temp0, hum0 = history[0]
    t1, temp1, hum1 = history[-1]

    dt = t1 - t0
    if dt == 0:
        return None

    temp_trend = (temp1 - temp0) / dt * 3600
    hum_trend = (hum1 - hum0) / dt * 3600

    text = ""
    if temp_trend > 0.5:
        text += "🌡 Температура растёт\n"
    if hum_trend < -1:
        text += "💧 Влажность падает\n"

    return text if text else None

# ===== СОН =====
def sleep_impact():
    if not (18 <= current_temp <= 23):
        return "❌ Может быть трудно уснуть"
    if not (45 <= current_hum <= 60):
        return "⚠️ Сон может быть поверхностным"
    return "✅ Условия комфортны для сна"

# ===== ГРАФИК =====
@app.route("/graph")
def graph():
    if not history:
        return "Нет данных"

    times = [h[0] for h in history]
    temps = [h[1] for h in history]
    hums = [h[2] for h in history]

    plt.figure(figsize=(10,5))
    plt.plot(times, temps, label="Температура")
    plt.plot(times, hums, label="Влажность")
    plt.legend()
    plt.title("Климат в помещении")
    plt.xlabel("Время")
    plt.ylabel("Значение")

    img = io.BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)

    return send_file(img, mimetype='image/png')

# ===== STATUS =====
@app.route("/status")
def status():
    return {
        "temperature": current_temp,
        "humidity": current_hum,
        "last_update": last_update
    }

if __name__ == "__main__":
    app.run()
