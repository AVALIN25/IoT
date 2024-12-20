import tkinter as tk
import random
import threading
import time
import paho.mqtt.client as mqtt

class IoTDevice:
    def __init__(self):
        self.soil_moisture = 50  # процент влажности почвы
        self.pump_active = False
        self.auto_mode = False
        self.lock = threading.Lock()

    def simulate_sensor(self):
        with self.lock:
            if not self.pump_active:
                self.soil_moisture = max(0, self.soil_moisture - random.uniform(0.5, 1.5))
            else:
                self.soil_moisture = min(100, self.soil_moisture + random.uniform(1.0, 3.0))

    def check_automatic_mode(self):
        if self.auto_mode and self.soil_moisture < 25:
            self.pump_active = True
        elif self.auto_mode and self.soil_moisture >= 60:
            self.pump_active = False

    def toggle_pump(self):
        with self.lock:
            self.pump_active = not self.pump_active

    def set_auto_mode(self, mode):
        with self.lock:
            self.auto_mode = mode

class IoTApplication:
    def __init__(self, root):
        self.device = IoTDevice()
        self.running = True

        # MQTT настройки
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.mqtt_on_connect
        self.mqtt_client.on_message = self.mqtt_on_message
        self.mqtt_broker = "10.40.81.71"
        self.mqtt_port = 1883

        # Подключение к MQTT-серверу
        self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
        self.mqtt_client.loop_start()

        # Элементы интерфейса
        self.root = root
        self.root.title("Симулятор IoT устройства")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.status_label = tk.Label(root, text="Влажность почвы: 50%", font=("Arial", 14))
        self.status_label.pack(pady=10)

        self.pump_button = tk.Button(root, text="Включить/Выключить насос", command=self.toggle_pump)
        self.pump_button.pack(pady=5)

        self.auto_mode_var = tk.BooleanVar()
        self.auto_mode_check = tk.Checkbutton(root, text="Автоматический режим", variable=self.auto_mode_var, command=self.set_auto_mode)
        self.auto_mode_check.pack(pady=5)

        self.log_text = tk.Text(root, height=10, width=50, state=tk.DISABLED)
        self.log_text.pack(pady=10)

        self.sensor_frequency_scale = tk.Scale(root, from_=1, to=60, orient=tk.HORIZONTAL, label="Интервал обновления датчиков (секунды)", command=self.set_sensor_interval)
        self.sensor_frequency_scale.set(10)
        self.sensor_frequency_scale.pack(pady=10)

        self.sensor_interval = 10  # Стандартный интервал обновления датчиков

        # Фоновый поток для симуляции
        self.simulation_thread = threading.Thread(target=self.run_simulation, daemon=True)
        self.simulation_thread.start()

    def update_ui(self):
        with self.device.lock:
            self.status_label.config(text=f"Влажность почвы: {self.device.soil_moisture:.1f}%")
            pump_status = "ВКЛ" if self.device.pump_active else "ВЫКЛ"
            self.log(f"Насос: {pump_status}, Влажность почвы: {self.device.soil_moisture:.1f}%")

    def run_simulation(self):
        while self.running:
            time.sleep(self.sensor_interval)  # Период обновления датчиков
            self.device.simulate_sensor()
            self.device.check_automatic_mode()

            # Публикация данных в MQTT
            self.publish_mqtt("iot/soil_moisture", f"{self.device.soil_moisture:.1f}")

            self.root.after(0, self.update_ui)

    def toggle_pump(self):
        self.device.toggle_pump()
        self.update_ui()

    def set_auto_mode(self):
        self.device.set_auto_mode(self.auto_mode_var.get())

    def set_sensor_interval(self, value):
        self.sensor_interval = int(value)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)

    def publish_mqtt(self, topic, message):
        self.mqtt_client.publish(topic, message)

    def mqtt_on_connect(self, client, userdata, flags, rc):
        try:
            if rc == 0:
                self.log("Подключено к MQTT-брокеру")
                self.mqtt_client.subscribe("iot/commands")
            else:
                self.log("Ошибка подключения к MQTT-брокеру")
        except Exception as e:
            print(f"Ошибка в mqtt_on_connect: {e}")

    def mqtt_on_message(self, client, userdata, msg):
        try:
            message = msg.payload.decode("utf-8")
            self.log(f"Получено сообщение: {message}")

            # Обработка команды
            if message == "TOGGLE_PUMP":
                self.device.toggle_pump()
            elif message == "AUTO_MODE_ON":
                self.device.set_auto_mode(True)
            elif message == "AUTO_MODE_OFF":
                self.device.set_auto_mode(False)

            # Обновление интерфейса
            self.root.after(0, self.update_ui)
        except Exception as e:
            print(f"Ошибка в mqtt_on_message: {e}")

    def on_close(self):
        self.running = False
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = IoTApplication(root)
    root.mainloop()


