import json
import time

from simulation.sensor_data import TelemetrySimulator


def load_devices():

    with open("simulation/devices.json", "r") as file:
        config = json.load(file)

    return config["devices"]


devices = load_devices()

sensors = []

for device in devices:

    sensor = TelemetrySimulator(
        device_id=device["device_id"],
        interval=device["interval"]
    )

    sensor.start()

    sensors.append(sensor)

    print(
        f"Started simulator: {device['device_id']}"
    )


try:

    while True:
        time.sleep(1)

except KeyboardInterrupt:

    print("\nStopping telemetry simulators...")

    for sensor in sensors:
        sensor.stop()

    print("Telemetry simulators stopped")