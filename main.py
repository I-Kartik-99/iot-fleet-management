import json
import time
import requests
import paho.mqtt.client as mqtt

from simulation.sensor_data import TelemetrySimulator


API_BASE_URL = "http://127.0.0.1:8000"

USERNAME = "admin"
PASSWORD = "admin123"

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
REGISTER_TOPIC = "devices/register"


# Currently running simulators
sensors = {}


def load_devices():

    with open("simulation/devices.json", "r") as file:
        config = json.load(file)

    return config["devices"]


def login():

    try:

        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data={
                "username": USERNAME,
                "password": PASSWORD
            },
            timeout=5
        )

        if response.status_code != 200:

            print(
                "Login failed:",
                response.status_code,
                response.text
            )

            return None

        token = response.json()["access_token"]

        print("Authentication successful")

        return token

    except requests.RequestException as error:

        print(
            "Authentication request failed:",
            error
        )

        return None


def register_device(device, token):

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

            headers={
                "Authorization": f"Bearer {token}"
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

        elif response.status_code == 401:

            print(
                f"[{device['device_id']}] "
                f"Authentication failed"
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


def fetch_registered_devices(token):
    """
    Fetch every device already registered in the DB - this covers
    devices registered before main.py was started (e.g. through the
    dashboard), which the devices.json fixtures and the live MQTT
    registration event alone wouldn't catch.
    """

    try:

        response = requests.get(
            f"{API_BASE_URL}/devices",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=5
        )

        if response.status_code != 200:

            print(
                "Could not fetch existing devices:",
                response.status_code,
                response.text
            )

            return []

        return response.json()

    except requests.RequestException as error:

        print(
            "Request to fetch existing devices failed:",
            error
        )

        return []


def start_simulator(device_id, interval=3):

    # Don't start the same device twice
    if device_id in sensors:

        print(
            f"[{device_id}] "
            f"Simulator already running"
        )

        return

    sensor = TelemetrySimulator(
        device_id=device_id,
        interval=interval
    )

    sensor.start()

    sensors[device_id] = sensor

    print(
        f"[{device_id}] "
        f"Simulator started automatically"
    )


def on_message(client, userdata, message):

    if message.topic != REGISTER_TOPIC:
        return

    try:

        data = json.loads(
            message.payload.decode()
        )

        device_id = data["device_id"]

        interval = data.get(
            "interval",
            3
        )

        print(
            f"\nNew device registration event: "
            f"{device_id}"
        )

        start_simulator(
            device_id,
            interval
        )

    except Exception as error:

        print(
            "Failed to process "
            "device registration event:",
            error
        )


def setup_mqtt():

    client = mqtt.Client()

    client.on_message = on_message

    client.connect(
        MQTT_BROKER,
        MQTT_PORT,
        60
    )

    client.subscribe(
        REGISTER_TOPIC
    )

    client.loop_start()

    print(
        f"Listening for new devices on "
        f"'{REGISTER_TOPIC}'"
    )

    return client


def main():

    # Login first
    token = login()

    if not token:

        print(
            "Cannot start simulators "
            "without authentication."
        )

        return


    # Start MQTT listener - picks up devices registered *while this
    # script is running* (e.g. through the dashboard)
    mqtt_client = setup_mqtt()


    # Resume simulation for every device already registered in the DB
    # before this script started
    existing_devices = fetch_registered_devices(token)

    for device in existing_devices:

        start_simulator(
            device["device_id"],
            device.get("telemetry_interval", 3)
        )


    # Start fixture devices from devices.json that aren't already
    # registered (start_simulator skips duplicates on its own)
    devices = load_devices()

    for device in devices:

        # Register device using JWT
        register_device(
            device,
            token
        )

        start_simulator(
            device["device_id"],
            device["interval"]
        )


    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        print(
            "\nStopping telemetry simulators..."
        )

        for sensor in sensors.values():
            sensor.stop()

        mqtt_client.loop_stop()

        mqtt_client.disconnect()

        print(
            "Telemetry simulators stopped"
        )


if __name__ == "__main__":
    main()