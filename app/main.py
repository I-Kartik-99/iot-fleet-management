from datetime import datetime
from typing import Dict

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from app.database import Base, engine, SessionLocal
from app.models.telemetry import Telemetry
from app.models.device import Device

import json
import paho.mqtt.client as mqtt

from app.models.user import User
from app.schemas.auth import LoginData, Token

from app.auth.auth import (
    verify_password,
    create_access_token,
    get_current_user
)

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# MQTT CONFIGURATION
# =========================

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "devices/+/telemetry"


Base.metadata.create_all(bind=engine)


# =========================
# PYDANTIC MODELS
# =========================

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


# =========================
# TELEMETRY DATABASE FUNCTION
# =========================

def store_telemetry(data):

    db = SessionLocal()

    try:

        # Check whether device is registered
        device = (
            db.query(Device)
            .filter(Device.device_id == data["device_id"])
            .first()
        )

        if not device:
            print(
                f"Device {data['device_id']} is not registered"
            )
            return None

        # Update device status
        device.status = "ONLINE"
        device.last_seen = datetime.utcnow()

        # Create telemetry record
        telemetry_record = Telemetry(
            device_id=data["device_id"],
            temperature=data["telemetry"].get("temperature"),
            humidity=data["telemetry"].get("humidity"),
            voltage=data["telemetry"].get("voltage"),
            pressure=data["telemetry"].get("pressure"),
            timestamp=datetime.fromisoformat(
                data["timestamp"]
            )
        )

        db.add(telemetry_record)

        db.commit()

        db.refresh(telemetry_record)

        print(
            f"Telemetry stored: "
            f"{data['device_id']}"
        )

        return telemetry_record.id

    finally:

        db.close()


# =========================
# MQTT CALLBACKS
# =========================

def on_connect(client, userdata, flags, reason_code, properties):

    print("Connected to MQTT broker")

    client.subscribe(MQTT_TOPIC)

    print(
        f"Subscribed to: {MQTT_TOPIC}"
    )


def on_message(client, userdata, message):

    try:

        payload = message.payload.decode()

        data = json.loads(payload)

        print(
            f"MQTT received: "
            f"{message.topic}"
        )

        store_telemetry(data)

    except Exception as error:

        print(
            f"MQTT processing error: {error}"
        )


# =========================
# MQTT CLIENT
# =========================

mqtt_client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2
)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(
    MQTT_BROKER,
    MQTT_PORT
)

mqtt_client.loop_start()


# =========================
# API ROUTES
# =========================

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


# =========================
# DEVICE REGISTRATION
# =========================

@app.post("/devices")
def register_device(data: DeviceData):

    db = SessionLocal()

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


# =========================
# GET ALL DEVICES
# =========================

@app.get("/devices")
def get_devices(
    current_user: str = Depends(get_current_user)
):

    db = SessionLocal()

    devices = db.query(Device).all()

    db.close()

    return devices


# =========================
# GET SINGLE DEVICE
# =========================

@app.get("/devices/{device_id}")
def get_device(
    device_id: str,
    current_user: str = Depends(get_current_user)
):

    db = SessionLocal()

    device = (
        db.query(Device)
        .filter(Device.device_id == device_id)
        .first()
    )

    if not device:

        db.close()

        raise HTTPException(
            status_code=404,
            detail=f"Device {device_id} is not registered"
        )

    db.close()

    return device


# =========================
# DEVICE STATUS
# =========================

@app.get("/devices/{device_id}/status")
def get_device_status(
    device_id: str,
    current_user: str = Depends(get_current_user)
):

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

    if device.last_seen is None:

        current_status = "OFFLINE"

    else:

        time_since_last_seen = (
            datetime.utcnow() - device.last_seen
        )

        if time_since_last_seen.total_seconds() < 60:

            current_status = "ONLINE"

        else:

            current_status = "OFFLINE"

    device.status = current_status

    db.commit()

    last_seen = device.last_seen

    db.close()

    return {
        "device_id": device.device_id,
        "status": current_status,
        "last_seen": last_seen
    }


# =========================
# HTTP TELEMETRY
# =========================

@app.post("/telemetry")
def receive_telemetry(data: TelemetryData):

    telemetry_data = {
        "device_id": data.device_id,
        "timestamp": data.timestamp.isoformat(),
        "telemetry": data.telemetry
    }

    record_id = store_telemetry(
        telemetry_data
    )

    if record_id is None:

        raise HTTPException(
            status_code=404,
            detail=f"Device {data.device_id} is not registered"
        )

    return {
        "status": "stored",
        "id": record_id,
        "device_id": data.device_id
    }


# =========================
# TELEMETRY HISTORY
# =========================

@app.get("/devices/{device_id}/telemetry")
def get_device_telemetry(
    device_id: str,
    limit: int = 5,
    current_user: str = Depends(get_current_user)
):

    db = SessionLocal()

    records = (
        db.query(Telemetry)
        .filter(Telemetry.device_id == device_id)
        .order_by(
            Telemetry.timestamp.desc()
        )
        .limit(limit)
        .all()
    )

    db.close()

    return records

@app.post("/auth/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    db = SessionLocal()

    user = (
        db.query(User)
        .filter(User.username == form_data.username)
        .first()
    )

    if not user:
        db.close()

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not verify_password(
        form_data.password,
        user.hashed_password
    ):
        db.close()

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token = create_access_token({
        "sub": user.username
    })

    db.close()

    return {
        "access_token": token,
        "token_type": "bearer"
    }