from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)

    device_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    name = Column(String, nullable=False)
    device_type = Column(String, nullable=False)
    location = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    status = Column(String, default="OFFLINE")
    last_seen = Column(DateTime, nullable=True)
    telemetry_interval = Column(Integer, nullable=False, default=2)


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )