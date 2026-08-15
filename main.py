import json
import time
import requests

from simulation.sensor_data import TelemetrySimulator


API_BASE_URL = "http://127.0.0.1:8000"


def load_devices():

    with open("simulation/devices.json", "r") as file:
        config = json.load(file)

    return config["devices"]


def register_device(device):

    try:

        response = requests.post(
            f"{API_BASE_URL}/devices",
            json={
                "device_id": device["device_id"],
                "name": device["name"],
                "device_type": device["device_type"],
                "location": device.get("location"),
                "firmware_version": device.get("firmware_version")
            },
            timeout=5
        )

        if response.status_code == 200:

            result = response.json()

            if result.get("status") == "registered":

                print(
                    f"[{device['device_id']}] "
                    f"Registered successfully"
                )

            elif result.get("status") == "error":

                print(
                    f"[{device['device_id']}] "
                    f"Already registered"
                )

        else:

            print(
                f"[{device['device_id']}] "
                f"Registration failed: "
                f"{response.status_code}"
            )

    except requests.RequestException as error:

        print(
            f"[{device['device_id']}] "
            f"Registration request failed: {error}"
        )


def main():

    devices = load_devices()

    sensors = []

    for device in devices:

        # Register device in FastAPI
        register_device(device)

        # Start MQTT simulator
        sensor = TelemetrySimulator(
            device_id=device["device_id"],
            interval=device["interval"]
        )

        sensor.start()

        sensors.append(sensor)

        print(
            f"Started simulator: "
            f"{device['device_id']}"
        )

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        print("\nStopping telemetry simulators...")

        for sensor in sensors:
            sensor.stop()

        print("Telemetry simulators stopped")


if __name__ == "__main__":
    main()