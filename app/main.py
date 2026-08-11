from datetime import datetime
from typing import Dict

from fastapi import FastAPI
from pydantic import BaseModel

from app.database import Base, engine, SessionLocal
from app.models.telemetry import Telemetry


app = FastAPI()


Base.metadata.create_all(bind=engine)


class TelemetryData(BaseModel):
    device_id: str
    timestamp: datetime
    telemetry: Dict[str, float]


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


@app.post("/telemetry")
def receive_telemetry(data: TelemetryData):

    db = SessionLocal()

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