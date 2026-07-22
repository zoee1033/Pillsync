from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

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

    reminder_id = Column(
        Integer,
        ForeignKey(
            "reminders.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================
    # Notification Content
    # =====================================

    title = Column(
        String(200),
        nullable=False
    )

    message = Column(
        Text,
        nullable=False
    )

    notification_type = Column(
        String(50),
        default="Reminder"
    )

    is_read = Column(
        Boolean,
        default=False
    )

    is_sent = Column(
        Boolean,
        default=False
    )

    sent_at = Column(
        DateTime(timezone=True),
        nullable=True
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

    user = relationship(
        "User",
        back_populates="notifications"
    )

    reminder = relationship(
        "Reminder"
    )