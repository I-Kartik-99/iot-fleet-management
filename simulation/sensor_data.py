import random
import time
import threading
from datetime import datetime
import requests
import json


class TelemetrySimulator:

    def __init__(
        self,
        device_id,
        interval=2,
        api_url="http://127.0.0.1:8000/telemetry"
    ):
        self.device_id = device_id
        self.interval = interval
        self.api_url = api_url

        self.running = False
        self.thread = None

    def generate_telemetry(self):
        return {
            "device_id": self.device_id,
            "timestamp": datetime.now().isoformat(),
            "telemetry": {
                "temperature": round(random.uniform(25, 40), 2),
                "humidity": round(random.uniform(40, 80), 2),
                "voltage": round(random.uniform(3.1, 3.3), 2),
                "pressure": round(random.uniform(995, 1020), 2)
            }
        }

    def send_telemetry(self, data):

        try:
            response = requests.post(
                self.api_url,
                json=data,
                timeout=5
            )

            print(
                f"[{self.device_id}] "
                f"Status: {response.status_code}"
                f"Response: {response.json()}"  
            )

        except requests.RequestException as error:
            print(
                f"[{self.device_id}] "
                f"Failed to send telemetry: {error}"
            )

    def run(self):

        while self.running:

            data = self.generate_telemetry()

            self.send_telemetry(data)

            time.sleep(self.interval)

    def start(self):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self.run,
            daemon=True
        )

        self.thread.start()

    def stop(self):

        self.running = False

        if self.thread:
            self.thread.join()