from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class History(Base):
    __tablename__ = "history"

    # =====================================
    # Primary Key
    # =====================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # =====================================
    # Foreign Keys
    # =====================================

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    treatment_id = Column(
        Integer,
        ForeignKey(
            "treatments.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    medicine_id = Column(
        Integer,
        ForeignKey(
            "medicines.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    reminder_id = Column(
        Integer,
        ForeignKey(
            "reminders.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================
    # History Information
    # =====================================

    scheduled_time = Column(
        DateTime(timezone=True),
        nullable=False
    )

    action_time = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    status = Column(
        String(20),
        nullable=False
    )

    skip_reason = Column(
        String(150),
        nullable=True
    )

    notes = Column(
        Text,
        nullable=True
    )

    # =====================================
    # Audit Fields
    # =====================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # =====================================
    # Relationships
    # =====================================

    user = relationship(
        "User",
        back_populates="history"
    )

    treatment = relationship(
        "Treatment"
    )

    medicine = relationship(
        "Medicine",
        back_populates="history"
    )

    reminder = relationship(
        "Reminder",
        back_populates="history"
    )