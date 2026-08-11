import time

from simulation.sensor_data import TelemetrySimulator


sensor = TelemetrySimulator(
    device_id="ESP32-001",
    interval=2
)

sensor.start()

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    sensor.stop()

    print("Telemetry simulator stopped")