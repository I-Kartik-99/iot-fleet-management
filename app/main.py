from datetime import datetime
from typing import Dict

from pydantic import BaseModel

from app.database import Base, engine, SessionLocal
from app.models import device
from app.models.telemetry import Telemetry
from app.models.device import Device
from fastapi import FastAPI, HTTPException

app = FastAPI()


Base.metadata.create_all(bind=engine)


class TelemetryData(BaseModel):
    device_id: str
    timestamp: datetime
    telemetry: Dict[str, float]

class DeviceData(BaseModel):
    device_id: str
    name: str
    device_type: str
    location: str | None = None
    firmware_version: str | None = None


@app.get("/")
def root():
    return {
        "message": "IoT Fleet Management API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }

@app.post("/devices")
def register_device(data: DeviceData):

    db = SessionLocal()

    # Check if device already exists
    existing_device = (
        db.query(Device)
        .filter(Device.device_id == data.device_id)
        .first()
    )

    if existing_device:
        db.close()

        return {
            "status": "error",
            "message": "Device already registered",
            "device_id": data.device_id
        }

    device = Device(
        device_id=data.device_id,
        name=data.name,
        device_type=data.device_type,
        location=data.location,
        firmware_version=data.firmware_version
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    device_id = device.device_id

    db.close()

    return {
        "status": "registered",
        "device_id": device_id
    }

@app.get("/devices")
def get_devices():

    db = SessionLocal()

    devices = db.query(Device).all()

    db.close()

    return devices

@app.get("/devices/{device_id}")
def get_device(device_id: str):

    db = SessionLocal()

    device = (
        db.query(Device)
        .filter(Device.device_id == device_id)
        .first()
    )

    db.close()

    if not device:
        db.close()

        raise HTTPException(
            status_code=404,
            detail=f"Device {device_id} is not registered"
        )

    return device

@app.get("/devices/{device_id}/status")
def get_device_status(device_id: str):

    db = SessionLocal()

    device = (
        db.query(Device)
        .filter(Device.device_id == device_id)
        .first()
    )

    if not device:
        db.close()

        return {
            "status": "error",
            "message": "Device not found",
            "device_id": device_id
        }

    # Device has never sent telemetry
    if device.last_seen is None:
        current_status = "OFFLINE"
    else:
        time_since_last_seen = datetime.utcnow() - device.last_seen

        if time_since_last_seen.total_seconds() < 60:
            current_status = "ONLINE"
        else:
            current_status = "OFFLINE"

    # Update status in database
    device.status = current_status

    db.commit()

    last_seen = device.last_seen

    db.close()

    return {
        "device_id": device.device_id,
        "status": current_status,
        "last_seen": last_seen
    }

@app.post("/telemetry")
def receive_telemetry(data: TelemetryData):

    db = SessionLocal()

    # Check whether device is registered
    device = (
        db.query(Device)
        .filter(Device.device_id == data.device_id)
        .first()
    )

    if not device:
        db.close()

        raise HTTPException(
            status_code=404,
            detail=f"Device {data.device_id} is not registered"
        )
    
    device.status = "ONLINE"
    device.last_seen = datetime.utcnow()

    telemetry_record = Telemetry(
        device_id=data.device_id,
        temperature=data.telemetry.get("temperature"),
        humidity=data.telemetry.get("humidity"),
        voltage=data.telemetry.get("voltage"),
        pressure=data.telemetry.get("pressure"),
        timestamp=data.timestamp
    )

    db.add(telemetry_record)

    db.commit()

    db.refresh(telemetry_record)

    record_id = telemetry_record.id

    db.close()

    return {
        "status": "stored",
        "id": record_id,
        "device_id": data.device_id
    }

@app.get("/devices/{device_id}/telemetry")
def get_device_telemetry(device_id: str, limit: int = 5):

    db = SessionLocal()

    records = (
        db.query(Telemetry)
        .filter(Telemetry.device_id == device_id)
        .order_by(Telemetry.timestamp.desc())
        .limit(limit)
        .all()
    )

    db.close()

    return records