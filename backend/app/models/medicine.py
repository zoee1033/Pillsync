from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Text
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Medicine(Base):
    __tablename__ = "medicines"

    # ============================
    # Primary Key
    # ============================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ============================
    # Foreign Key -> Treatment
    # ============================

    treatment_id = Column(
        Integer,
        ForeignKey(
            "treatments.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # ============================
    # Medicine Details
    # ============================

    medicine_name = Column(
        String(150),
        nullable=False
    )

    medicine_type = Column(
        String(50),
        nullable=False
    )

    dosage = Column(
        String(50),
        nullable=False
    )

    quantity = Column(
        Integer,
        nullable=False
    )

    instructions = Column(
        Text,
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True
    )

    # ============================
    # Audit Fields
    # ============================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # ============================
    # Relationships
    # ============================

    treatment = relationship(
        "Treatment",
        back_populates="medicines"
    )

    reminders = relationship(
        "Reminder",
        back_populates="medicine",
        cascade="all, delete-orphan"
    )

    history = relationship(
        "History",
        back_populates="medicine",
        cascade="all, delete-orphan"
    )