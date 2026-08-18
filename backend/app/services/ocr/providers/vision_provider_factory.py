import os
import logging
from typing import Optional

from app.config import settings
from app.services.ocr.providers.base_provider import VisionProvider
from app.services.ocr.providers.gemma_provider import GemmaVisionProvider
from app.services.ocr.providers.gemini_provider import GeminiVisionProvider
from app.services.ocr.providers.gpt_provider import GPTVisionProvider
from app.services.ocr.providers.claude_provider import ClaudeVisionProvider
from app.services.ocr.providers.qwen_provider import QwenVisionProvider

logger = logging.getLogger("VISION_PROVIDER_FACTORY")


class VisionProviderFactory:
    """
    Dynamic Provider Registry & Factory.
    Instantiates configured Vision AI provider cleanly based on specified provider name
    or `settings.VISION_PROVIDER` / environment.
    """

    _REGISTRY = {
        "gemma": GemmaVisionProvider,
        "gemini": GeminiVisionProvider,
        "gpt": GPTVisionProvider,
        "claude": ClaudeVisionProvider,
        "qwen": QwenVisionProvider
    }

    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> VisionProvider:
        name = (provider_name or getattr(settings, "VISION_PROVIDER", "gemma") or os.getenv("VISION_PROVIDER", "gemma")).lower().strip()
        provider_cls = cls._REGISTRY.get(name, GemmaVisionProvider)
        provider_instance = provider_cls()
        logger.info(f"[PROVIDER_FACTORY] Instantiated Vision Provider: '{provider_instance.provider_id}' (Model: '{provider_instance.model_name}')")
        return provider_instance
