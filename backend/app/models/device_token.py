from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class DeviceToken(Base):
    __tablename__ = "device_tokens"

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

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # =====================================
    # Device Information
    # =====================================

    fcm_token = Column(
        String(500),
        nullable=False,
        unique=True
    )

    device_name = Column(
        String(100),
        nullable=True
    )

    browser = Column(
        String(100),
        nullable=True
    )

    platform = Column(
        String(100),
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True
    )

    last_used_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
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
    # Relationship
    # =====================================

    user = relationship(
        "User",
        back_populates="device_tokens"
    )