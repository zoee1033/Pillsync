import time
from typing import List, Tuple, Optional
from app.schemas.ocr_schema import ExtractedMedicine
from app.services.ocr.providers.base_provider import VisionProvider
from app.services.ocr.ai_ocr_engine import run_gemini_vision_verification, convert_gemini_response_to_medicines


class GeminiVisionProvider(VisionProvider):
    """
    Gemini Vision Provider implementation.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key
        self._model = model or "gemini-2.0-flash"

    @property
    def provider_id(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    def initialize(self) -> bool:
        import os
        key = self._api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        return bool(key)

    def extract_prescription(
        self,
        image_bytes: bytes,
        timeout: Optional[int] = None
    ) -> Tuple[Optional[List[ExtractedMedicine]], float, float]:
        t0 = time.perf_counter()
        res = run_gemini_vision_verification(
            image_bytes=image_bytes,
            tesseract_text="",
            ocr_confidence=75.0,
            detected_medicines=[]
        )
        latency = round((time.perf_counter() - t0) * 1000.0, 2)
        if res.get("success") and res.get("data"):
            meds = convert_gemini_response_to_medicines(res["data"])
            conf = float(res["data"].get("confidence", 0.90))
            return meds, conf, latency
        return None, 0.0, latency
