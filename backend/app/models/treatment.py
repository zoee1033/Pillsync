from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Text,
    ForeignKey
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Treatment(Base):
    __tablename__ = "treatments"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Foreign Key -> User
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Treatment Details
    disease_name = Column(
        String(150),
        nullable=False
    )

    doctor_name = Column(
        String(100),
        nullable=True
    )

    diagnosis_date = Column(
        Date,
        nullable=True
    )

    start_date = Column(
        Date,
        nullable=False
    )

    end_date = Column(
        Date,
        nullable=False
    )

    status = Column(
        String(20),
        nullable=False,
        default="Active"
    )

    notes = Column(
        Text,
        nullable=True
    )

    # Audit Fields
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

    user = relationship(
        "User",
        back_populates="treatments"
    )

    medicines = relationship(
        "Medicine",
        back_populates="treatment",
        cascade="all, delete-orphan"
    )