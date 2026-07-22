from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Time,
    ForeignKey
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Reminder(Base):
    __tablename__ = "reminders"

    # =====================================
    # Primary Key
    # =====================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # =====================================
    # Foreign Key
    # =====================================

    medicine_id = Column(
        Integer,
        ForeignKey(
            "medicines.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================
    # Reminder Information
    # =====================================

    reminder_time = Column(
        Time,
        nullable=False
    )

    repeat_type = Column(
        String(20),
        nullable=False,
        default="Daily"
    )

    notification_enabled = Column(
        Boolean,
        default=True
    )

    snooze_minutes = Column(
        Integer,
        default=10
    )

    next_trigger_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    last_triggered_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    status = Column(
        String(20),
        default="Active"
    )

    # =====================================
    # Audit Fields
    # =====================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # =====================================
    # Relationships
    # =====================================

    medicine = relationship(
        "Medicine",
        back_populates="reminders"
    )

    history = relationship(
        "History",
        back_populates="reminder",
        cascade="all, delete-orphan"
    )