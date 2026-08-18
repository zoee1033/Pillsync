import time
from typing import List, Tuple, Optional
from app.schemas.ocr_schema import ExtractedMedicine
from app.services.ocr.providers.base_provider import VisionProvider
from app.services.ocr.ai_ocr_engine import run_openai_vision_ocr, convert_gemini_response_to_medicines


class GPTVisionProvider(VisionProvider):
    """
    GPT-4o Vision Provider implementation.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key
        self._model = model or "gpt-4o-mini"

    @property
    def provider_id(self) -> str:
        return "gpt"

    @property
    def model_name(self) -> str:
        return self._model

    def initialize(self) -> bool:
        import os
        key = self._api_key or os.getenv("OPENAI_API_KEY")
        return bool(key)

    def extract_prescription(
        self,
        image_bytes: bytes,
        timeout: Optional[int] = None
    ) -> Tuple[Optional[List[ExtractedMedicine]], float, float]:
        t0 = time.perf_counter()
        res = run_openai_vision_ocr(image_bytes=image_bytes)
        latency = round((time.perf_counter() - t0) * 1000.0, 2)
        if res.get("success") and res.get("structured_data"):
            meds = convert_gemini_response_to_medicines(res["structured_data"])
            conf = float(res.get("confidence", 95)) / 100.0
            return meds, conf, latency
        return None, 0.0, latency
