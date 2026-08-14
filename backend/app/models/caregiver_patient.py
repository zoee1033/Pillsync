from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CaregiverPatient(Base):
    __tablename__ = "caregiver_patients"

    id = Column(Integer, primary_key=True, index=True)
    caregiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="active", nullable=False)  # pending, active, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    caregiver = relationship("User", foreign_keys=[caregiver_id])
    patient = relationship("User", foreign_keys=[patient_id])

    __table_args__ = (
        UniqueConstraint('caregiver_id', 'patient_id', name='uix_caregiver_patient'),
    )
