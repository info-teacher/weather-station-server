from flask import Flask, request, send_file

from flask_cors import CORS  
import time
import io
import matplotlib.pyplot as plt

app = Flask(__name__)
CORS(app)  
TOKEN = "8513191267:AAE1_qvgvjHR4g5-cONFN4CB-r_NtM4rHdk"
CHAT_ID = "945281794"

app = Flask(__name__)

# ДАННЫЕ
current_temp = None
current_hum = None
last_update = 0

history = []  # (time, temp, hum)
last_alert_time = 0
ALERT_INTERVAL = 1800  # 30 минут

# НОРМЫ 
ROOM = {
    "temp": (20, 24),
    "hum": (40, 60)
}

#TELEGRAM
def send_message(text):
    # Отправляем сообщение в Telegram
    requests.get(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        params={"chat_id": CHAT_ID, "text": text}
    )

# DATA
@app.route("/data", methods=["POST"])
def receive_data():
    global current_temp, current_hum, last_update, history

    data = request.json
    current_temp = data.get("temp")
    current_hum = data.get("hum")
    last_update = time.time()

    history.append((last_update, current_temp, current_hum))
    history = history[-100:]  # храним последние 100 точек

    check_values()  # проверяем отклонения и отправляем Telegram
    return {"status": "ok"}

# ПРОВЕРКА
def check_values():
    alerts, advice, health = [], [], []

    tmin, tmax = ROOM["temp"]
    hmin, hmax = ROOM["hum"]

    if current_temp is None:
        return

    #Температурные отклонения
    if current_temp < tmin:
        alerts.append("🧊 Холодно")
        health.append("риск простуды")
        advice.append("повысить отопление")
    elif current_temp > tmax:
        alerts.append("🥵 Жарко")
        health.append("ухудшение сна и концентрации")
        advice.append("проветрить помещение")

    # Влажность
    if current_hum < hmin:
        alerts.append("🌵 Сухо")
        health.append("сухость кожи и слизистых")
        advice.append("использовать увлажнитель")
    elif current_hum > hmax:
        alerts.append("🌫 Влажно")
        health.append("риск плесени")
        advice.append("проветривание")

    # Если есть превышения – формируем сообщение для Telegram
    if alerts:
        msg = "🏠 Состояние комнаты\n\n"
        msg += f"🌡 {current_temp}°C\n💧 {current_hum}%\n\n"

        msg += "⚠️ Проблемы:\n"
        for a in alerts:
            msg += f"• {a}\n"

        msg += "\n🩺 Возможные эффекты:\n"
        for h in health:
            msg += f"• {h}\n"

        msg += "\n💡 Советы:\n"
        for a in advice:
            msg += f"• {a}\n"

        sleep_text = sleep_impact()
        forecast = generate_forecast()

        if sleep_text:
            msg += f"\n😴 Сон:\n{sleep_text}"
        if forecast:
            msg += f"\n🔮 Прогноз:\n{forecast}"

        send_message(msg)

# ПРОГНОЗ
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

#  СОН
def sleep_impact():
    if not (18 <= current_temp <= 23):
        return "❌ Может быть трудно уснуть"
    if not (45 <= current_hum <= 60):
        return "⚠️ Сон может быть поверхностным"
    return "✅ Условия комфортны для сна"

# ГРАФИК 
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

# STATUS 
@app.route("/status")
def status():
    """
    Возвращает текущие значения и флаги тревоги,
    чтобы браузер мог воспроизвести звук.
    """
    tmin, tmax = ROOM["temp"]
    hmin, hmax = ROOM["hum"]

    tempAlert = False
    humAlert = False

    if current_temp is not None:
        tempAlert = current_temp < tmin or current_temp > tmax
    if current_hum is not None:
        humAlert = current_hum < hmin or current_hum > hmax

    return {
        "temperature": current_temp,
        "humidity": current_hum,
        "last_update": last_update,
        "tempAlert": tempAlert,   # <- тревога по температуре для браузера
        "humAlert": humAlert      # <- тревога по влажности для браузера
    }

if __name__ == "__main__":
    app.run()
