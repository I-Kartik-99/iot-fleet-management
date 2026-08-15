import json
import time

from sensor_data import TelemetrySimulator


def load_devices():

    with open("simulation/devices.json", "r") as file:
        config = json.load(file)

    return config["devices"]


def main():

    devices = load_devices()

    simulators = []

    for device in devices:

        simulator = TelemetrySimulator(
            device_id=device["device_id"],
            interval=device["interval"]
        )

        simulator.start()

        simulators.append(simulator)

        print(
            f"Started simulator for {device['device_id']}"
        )

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        print("\nStopping simulators...")

        for simulator in simulators:
            simulator.stop()


if __name__ == "__main__":
    main()