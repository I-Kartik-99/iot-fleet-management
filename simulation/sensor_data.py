import random
import time
import threading
from datetime import datetime
import json
import paho.mqtt.client as mqtt


class TelemetrySimulator:

    def __init__(
        self,
        device_id,
        interval=2,
        broker="127.0.0.1",
        port=1883
    ):
        self.device_id = device_id
        self.interval = interval

        self.broker = broker
        self.port = port

        self.running = False
        self.thread = None

        self.mqtt_client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2
        )

        self.mqtt_client.connect(
            self.broker,
            self.port
        )

        self.mqtt_client.loop_start()

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

        topic = f"devices/{self.device_id}/telemetry"

        payload = json.dumps(data)

        result = self.mqtt_client.publish(
            topic,
            payload
        )

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(
                f"[{self.device_id}] "
                f"MQTT Published"
            )
        else:
            print(
                f"[{self.device_id}] "
                f"MQTT Publish Failed"
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

        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()