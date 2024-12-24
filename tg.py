import paho.mqtt.client as mqtt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Конфигурация MQTT
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
TELEMETRY_TOPIC = "iot/soil_moisture"
COMMANDS_TOPIC = "iot/commands"


# MQTT клиент
class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.last_telemetry = None  # Храним последние данные о влажности почвы

    def connect(self):
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print("Подключено к MQTT-брокеру.")
        self.client.subscribe(TELEMETRY_TOPIC)  # Подписка на топик телеметрии

    def on_message(self, client, userdata, msg):
        # Обработка полученных данных из MQTT
        telemetry_data = msg.payload.decode("utf-8")
        self.last_telemetry = float(telemetry_data)  # Сохраняем последние данные о влажности
        print(f"Получены данные: {telemetry_data}")

    def publish(self, topic, message):
        self.client.publish(topic, message)

    def get_last_telemetry(self):
        return self.last_telemetry


# Telegram-бот
class IoTApplication:
    def __init__(self, token, mqtt_client):
        self.token = token
        self.mqtt_client = mqtt_client
        self.application = ApplicationBuilder().token(self.token).build()

        # Регистрируем команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("telemetry", self.telemetry))
        self.application.add_handler(CommandHandler("start_pump", self.start_pump))
        self.application.add_handler(CommandHandler("stop_pump", self.stop_pump))
        self.application.add_handler(CommandHandler("set_auto_mode", self.set_auto_mode))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Добро пожаловать в IoT-бот! Используйте команды для управления.")

    async def telemetry(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Получаем последние данные о влажности из MQTT
        telemetry_data = self.mqtt_client.get_last_telemetry()

        if telemetry_data is not None:
            await update.message.reply_text(f"Текущая влажность почвы: {telemetry_data:.1f}%")
        else:
            await update.message.reply_text("Нет данных о влажности. Попробуйте позже.")

    async def start_pump(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.mqtt_client.publish(COMMANDS_TOPIC, "TOGGLE_PUMP")
        await update.message.reply_text("Насос включён.")

    async def stop_pump(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.mqtt_client.publish(COMMANDS_TOPIC, "TOGGLE_PUMP")
        await update.message.reply_text("Насос выключён.")

    async def set_auto_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        mode = context.args[0] if context.args else "ON"
        command = "AUTO_MODE_ON" if mode.upper() == "ON" else "AUTO_MODE_OFF"
        self.mqtt_client.publish(COMMANDS_TOPIC, command)
        await update.message.reply_text(f"Автоматический режим {'включён' if mode.upper() == 'ON' else 'выключён'}.")

    def run(self):
        self.application.run_polling()


# Запуск программы
if __name__ == "__main__":
    TELEGRAM_TOKEN = "7217111054:AAGqux25mcum4SveCrJYdxPjqgVzDDQeGBg"

    # Инициализация MQTT клиента
    mqtt_client = MQTTClient()
    mqtt_client.connect()

    # Инициализация Telegram-бота
    bot = IoTApplication(TELEGRAM_TOKEN, mqtt_client)
    bot.run()
