import threading
from typing import Dict, Optional

from simulation.sensor_data import TelemetrySimulator


class SimulatorManager:
    """
    Owns the lifecycle of in-process TelemetrySimulator threads, one
    per registered device.

    Registration auto-starts a simulator for the new device_id. Each
    simulator publishes synthetic telemetry over MQTT on its own
    thread until explicitly stopped or the process shuts down.

    Thread-safety note: FastAPI runs sync `def` routes in a thread
    pool, so multiple registrations/stops can call into this manager
    concurrently. All access to the underlying dict is guarded by a
    lock.
    """

    def __init__(self, broker: str = "127.0.0.1", port: int = 1883):
        self._broker = broker
        self._port = port
        self._simulators: Dict[str, TelemetrySimulator] = {}
        self._lock = threading.Lock()

    def is_running(self, device_id: str) -> bool:
        with self._lock:
            simulator = self._simulators.get(device_id)
            return simulator is not None and simulator.running

    def start(self, device_id: str, interval: int = 2) -> bool:
        """
        Start a simulator thread for device_id.
        Returns False if one is already running (no-op, not an error).
        """
        with self._lock:
            existing = self._simulators.get(device_id)
            if existing is not None and existing.running:
                return False

            simulator = TelemetrySimulator(
                device_id=device_id,
                interval=interval,
                broker=self._broker,
                port=self._port,
            )
            simulator.start()
            self._simulators[device_id] = simulator
            return True

    def stop(self, device_id: str) -> bool:
        """
        Stop the simulator for device_id, if one is running.
        Returns False if none was running.
        """
        with self._lock:
            simulator = self._simulators.pop(device_id, None)

        if simulator is None:
            return False

        # simulator.stop() joins its worker thread, which only checks
        # the running flag once per sleep cycle - it can block for up
        # to `interval` seconds. Do that join off the request thread
        # so callers (e.g. an API endpoint) return immediately.
        threading.Thread(target=simulator.stop, daemon=True).start()
        return True

    def stop_all(self) -> None:
        """
        Stop every running simulator and wait for them to fully shut
        down. Intended for use during application shutdown, where
        blocking until threads/MQTT connections are cleanly released
        is the desired behavior.
        """
        with self._lock:
            simulators = list(self._simulators.values())
            self._simulators.clear()

        for simulator in simulators:
            simulator.stop()


# Single shared instance used by the FastAPI app.
simulator_manager = SimulatorManager(broker="127.0.0.1", port=1883)