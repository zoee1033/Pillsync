import time
from typing import List, Tuple, Optional
from app.schemas.ocr_schema import ExtractedMedicine
from app.services.ocr.providers.base_provider import VisionProvider


class QwenVisionProvider(VisionProvider):
    """
    Qwen 2.5 Vision Provider implementation.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key
        self._model = model or "qwen/qwen-2.5-vl-72b-instruct"

    @property
    def provider_id(self) -> str:
        return "qwen"

    @property
    def model_name(self) -> str:
        return self._model

    def initialize(self) -> bool:
        import os
        key = self._api_key or os.getenv("OPENROUTER_API_KEY")
        return bool(key)

    def extract_prescription(
        self,
        image_bytes: bytes,
        timeout: Optional[int] = None
    ) -> Tuple[Optional[List[ExtractedMedicine]], float, float]:
        from app.services.ocr.providers.gemma_provider import GemmaVisionProvider
        gemma = GemmaVisionProvider(model=self._model)
        return gemma.extract_prescription(image_bytes, timeout)
