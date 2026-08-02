from typing import List, Optional
from pydantic import BaseModel, Field


class FieldConfidence(BaseModel):
    name_confidence: int = Field(95, description="Confidence for medicine name %")
    dosage_confidence: int = Field(95, description="Confidence for dosage %")
    frequency_confidence: int = Field(95, description="Confidence for frequency %")
    duration_confidence: int = Field(95, description="Confidence for duration %")


class ExtractedMedicine(BaseModel):
    medicine_name: str = Field(..., description="Extracted name of the medicine")
    dosage: str = Field(..., description="Extracted dosage e.g. 500mg")
    quantity: int = Field(..., ge=1, description="Extracted total quantity or stock")
    frequency: str = Field("Daily", description="Daily, Twice daily, Weekly, etc.")
    duration: str = Field("7 days", description="Duration of prescription")
    confidence: float = Field(0.95, ge=0.0, le=1.0, description="Overall OCR confidence score")
    field_confidence: Optional[FieldConfidence] = None
    needs_review: bool = Field(False, description="Flagged for manual review if confidence < 80%")


class OCRExtractResponse(BaseModel):
    success: bool
    message: str
    medicines: List[ExtractedMedicine] = []
    raw_text: Optional[str] = None

