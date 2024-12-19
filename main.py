import tkinter as tk
import random
import threading
import time

class IoTDevice:
    def __init__(self):
        self.soil_moisture = 50
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
        self.sensor_frequency_scale.pack(pady=5)

        self.sensor_interval = 10


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

    def on_close(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = IoTApplication(root)
    root.mainloop()

#for good github

