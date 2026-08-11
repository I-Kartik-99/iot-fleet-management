from sqlalchemy import Column, Integer, String, Float, DateTime

from app.database import Base


class Telemetry(Base):

    __tablename__ = "telemetry"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    device_id = Column(
        String,
        nullable=False,
        index=True
    )

    temperature = Column(Float)
    humidity = Column(Float)
    voltage = Column(Float)
    pressure = Column(Float)

    timestamp = Column(
        DateTime,
        nullable=False
    )