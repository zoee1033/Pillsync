from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    full_name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(120),
        unique=True,
        nullable=False,
        index=True
    )

    phone = Column(
        String(20),
        nullable=True
    )

    password = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(20),
        nullable=False,
        default="patient"
    )

    is_active = Column(
        Boolean,
        default=True
    )

    # Patient Health Profile Fields
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    blood_group = Column(String(10), nullable=True)
    weight = Column(String(20), nullable=True)
    height = Column(String(20), nullable=True)
    medical_conditions = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    primary_doctor = Column(String(100), nullable=True)
    hospital = Column(String(100), nullable=True)
    language = Column(String(50), default="English")
    timezone = Column(String(50), default="UTC")
    reminder_preferences = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    treatments = relationship(
        "Treatment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    history = relationship(
        "History",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    device_tokens = relationship(
        "DeviceToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )