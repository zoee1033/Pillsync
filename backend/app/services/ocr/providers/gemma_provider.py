from typing import List, Tuple, Optional
from app.schemas.ocr_schema import ExtractedMedicine
from app.services.ocr.providers.base_provider import VisionProvider
from app.services.ocr.gemma_vision import GemmaVisionService


class GemmaVisionProvider(VisionProvider):
    """
    Gemma Vision Provider implementation via OpenRouter API.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._service = GemmaVisionService(api_key=api_key, model=model)

    @property
    def provider_id(self) -> str:
        return "gemma"

    @property
    def model_name(self) -> str:
        return self._service.model

    def initialize(self) -> bool:
        return self._service.initialize_client()

    def extract_prescription(
        self,
        image_bytes: bytes,
        timeout: Optional[int] = None
    ) -> Tuple[Optional[List[ExtractedMedicine]], float, float]:
        return self._service.extract_prescription(image_bytes=image_bytes, timeout=timeout)
