from typing import List, Optional
from pydantic import BaseModel, Field


class FieldConfidence(BaseModel):
    name_confidence: int = Field(95, description="Confidence for medicine name %")
    dosage_confidence: Optional[int] = Field(None, description="Confidence for dosage %")
    frequency_confidence: Optional[int] = Field(None, description="Confidence for frequency %")
    duration_confidence: Optional[int] = Field(None, description="Confidence for duration %")


class ExtractedMedicine(BaseModel):
    medicine_name: str = Field(..., description="Extracted name of the medicine")
    brand_name: Optional[str] = Field("", description="Prescription brand name e.g. Calpol")
    generic_name: Optional[str] = Field("", description="Canonical generic name e.g. Paracetamol")
    prefix: Optional[str] = Field("", description="Formulation prefix e.g. Syp, Tab, Cap")
    dosage: str = Field("", description="Extracted dosage e.g. 500mg")
    quantity: Optional[int] = Field(None, description="Extracted total quantity or stock")
    frequency: str = Field("", description="Daily, Twice daily, Weekly, etc.")
    duration: str = Field("", description="Duration of prescription")
    instructions: Optional[str] = Field("", description="Clinical instructions e.g. Take after meals")
    confidence: float = Field(0.95, ge=0.0, le=1.0, description="Overall OCR confidence score")
    field_confidence: Optional[FieldConfidence] = None
    needs_review: bool = Field(False, description="Flagged for manual review if confidence < 80%")


class OCRExtractResponse(BaseModel):
    success: bool
    message: str
    medicines: List[ExtractedMedicine] = Field(default_factory=list, description="Extracted medicine items")
    raw_text: Optional[str] = None

