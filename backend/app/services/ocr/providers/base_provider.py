from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from app.schemas.ocr_schema import ExtractedMedicine


class VisionProvider(ABC):
    """
    Abstract Base Class for Vision AI Providers (Gemma, Gemini, GPT-4o, Claude, Qwen).
    Provides unified vision interface for prescription extraction.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Returns provider identifier (e.g. 'gemma', 'gemini', 'gpt', 'claude', 'qwen')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns underlying model ID."""
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """Initializes API client credentials and verifies configuration."""
        pass

    @abstractmethod
    def extract_prescription(
        self,
        image_bytes: bytes,
        timeout: Optional[int] = None
    ) -> Tuple[Optional[List[ExtractedMedicine]], float, float]:
        """
        Extracts prescription medicine candidates from image bytes.
        Returns (medicines_list, confidence, latency_ms).
        """
        pass
