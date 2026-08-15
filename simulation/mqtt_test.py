import paho.mqtt.client as mqtt

BROKER = "127.0.0.1"
PORT = 1883
TOPIC = "test"


def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected to MQTT broker")

    client.subscribe(TOPIC)


def on_message(client, userdata, message):
    print(
        f"Received: {message.topic} -> "
        f"{message.payload.decode()}"
    )


client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2
)

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT)

client.loop_forever()