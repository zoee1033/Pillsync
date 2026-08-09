import os
import io
import time
import json
import base64
import logging
import urllib.request
import urllib.error
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image

from app.schemas.ocr_schema import ExtractedMedicine, FieldConfidence

logger = logging.getLogger("GEMMA_VISION")

USE_GEMMA = os.getenv("USE_GEMMA", "true").lower() == "true"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
GEMMA_TIMEOUT = int(os.getenv("GEMMA_TIMEOUT", "20"))
GEMMA_MAX_RETRIES = int(os.getenv("GEMMA_MAX_RETRIES", "1"))
GEMMA_MODEL = os.getenv("GEMMA_MODEL", "").strip()

DEBUG_OCR = os.getenv("DEBUG_OCR", "false").lower() == "true"
DEBUG_DIR = os.getenv("DEBUG_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "debug"))

SYSTEM_PROMPT = (
    "You are an expert Medical AI Vision Assistant. Analyze the provided prescription image "
    "and extract all prescribed medicines into strict JSON format with keys 'medicines' and 'confidence'.\n\n"
    "Each medicine object in 'medicines' must have:\n"
    "- 'medicine_name': string\n"
    "- 'dosage': string\n"
    "- 'frequency': string\n"
    "- 'duration': string\n"
    "- 'quantity': integer or null\n"
    "- 'instructions': string\n\n"
    "Return STRICT JSON ONLY. Do NOT use markdown code blocks (```json). No explanation or extra text."
)


class GemmaVisionService:
    """
    Gemma Vision Engine via OpenRouter API.
    Operates as an intelligent secondary AI fallback engine.
    Fully configurable via environment variables.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        env_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        env_model = os.getenv("GEMMA_MODEL", os.getenv("AI_MODEL", "")).strip()
        self.api_key = (api_key if api_key is not None else env_key).strip()
        self.model = (model if model is not None else env_model).strip()

    def initialize_client(self) -> bool:
        """Verifies presence of OpenRouter API key and GEMMA_MODEL environment variable."""
        if not self.api_key:
            logger.warning("[GEMMA] OPENROUTER_API_KEY environment variable is missing. Skipping Gemma Vision.")
            return False
        if not self.model:
            logger.warning("[GEMMA] GEMMA_MODEL environment variable is missing. Skipping Gemma Vision.")
            return False
        return True

    def parse_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Strips markdown wrappers and parses JSON response."""
        if not response_text:
            return None

        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as err:
            logger.warning(f"[GEMMA] JSON decoding failed: {err}")
            return None

    def validate_json(self, parsed_dict: Dict[str, Any]) -> bool:
        """Validates that parsed JSON matches expected schema."""
        if not isinstance(parsed_dict, dict):
            return False
        if "medicines" not in parsed_dict or not isinstance(parsed_dict["medicines"], list):
            return False
        return True

    def convert_dict_to_extracted_medicines(self, parsed_dict: Dict[str, Any]) -> List[ExtractedMedicine]:
        """Converts raw dict items into ExtractedMedicine Pydantic models."""
        medicines: List[ExtractedMedicine] = []
        overall_conf = float(parsed_dict.get("confidence", 0.90))

        for item in parsed_dict.get("medicines", []):
            if not isinstance(item, dict):
                continue
            m_name = str(item.get("medicine_name", "")).strip()
            if not m_name:
                continue

            dosage = str(item.get("dosage", "") or "").strip()
            freq = str(item.get("frequency", "") or "").strip()
            dur = str(item.get("duration", "") or "").strip()
            qty = item.get("quantity")
            if qty is not None:
                try:
                    qty = int(qty)
                except (ValueError, TypeError):
                    qty = None

            med = ExtractedMedicine(
                medicine_name=m_name,
                dosage=dosage,
                quantity=qty,
                frequency=freq,
                duration=dur,
                confidence=round(overall_conf, 2),
                field_confidence=FieldConfidence(
                    name_confidence=92,
                    dosage_confidence=90 if dosage else 50,
                    frequency_confidence=90 if freq else 50,
                    duration_confidence=90 if dur else 50
                ),
                needs_review=False
            )
            medicines.append(med)

        return medicines

    def extract_prescription(
        self,
        image_bytes: bytes,
        timeout: Optional[int] = None
    ) -> Tuple[Optional[List[ExtractedMedicine]], float, float]:
        """
        Calls Gemma-4 Vision via OpenRouter to extract prescription medicines.
        Returns (medicines_list, confidence, latency_ms).
        """
        start_time = time.perf_counter()
        req_timeout = timeout or GEMMA_TIMEOUT

        logger.info("[GEMMA] Started")

        if not USE_GEMMA:
            logger.info("[GEMMA] Gemma Vision is disabled via USE_GEMMA=false.")
            return None, 0.0, 0.0

        if not self.initialize_client():
            return None, 0.0, 0.0

        masked_key = f"{self.api_key[:8]}..." if len(self.api_key) > 8 else "***"
        logger.info(f"[GEMMA] Preparing request | Model='{self.model}' | API_Key='{masked_key}' | Timeout={req_timeout}s")

        b64_img = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:image/png;base64,{b64_img}"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": SYSTEM_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_uri}}
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1024
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://pillsync.ai",
            "X-Title": "PillSync OCR Engine"
        }

        raw_response_text = ""
        parsed_data = None
        attempts = 0
        max_attempts = 1 + GEMMA_MAX_RETRIES

        while attempts < max_attempts and not parsed_data:
            attempts += 1
            try:
                logger.info(f"[GEMMA] Sending request to OpenRouter (Attempt #{attempts}/{max_attempts})")
                req_data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=req_data, headers=headers, method="POST")

                with urllib.request.urlopen(req, timeout=req_timeout) as resp:
                    logger.info(f"[GEMMA] Response received (HTTP Status: {resp.status})")
                    resp_bytes = resp.read()
                    resp_json = json.loads(resp_bytes.decode("utf-8"))
                    choices = resp_json.get("choices", [])
                    if choices:
                        raw_response_text = choices[0].get("message", {}).get("content", "")

                parsed_data = self.parse_response(raw_response_text)
                if parsed_data and self.validate_json(parsed_data):
                    break
                else:
                    parsed_data = None
                    logger.warning(f"[GEMMA] Attempt #{attempts} failed JSON validation. Retrying...")

            except urllib.error.URLError as url_err:
                logger.warning(f"[GEMMA] Attempt #{attempts} API network error: {url_err}")
            except Exception as ex:
                logger.warning(f"[GEMMA] Attempt #{attempts} error: {ex}")

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if not parsed_data or not self.validate_json(parsed_data):
            logger.warning(f"[GEMMA] Failed to extract valid JSON after {attempts} attempts ({elapsed_ms:.1f} ms).")
            logger.info("[GEMMA] Completed")
            return None, 0.0, round(elapsed_ms, 2)

        gemma_meds = self.convert_dict_to_extracted_medicines(parsed_data)
        overall_conf = float(parsed_data.get("confidence", 0.90))

        logger.info(
            f"[GEMMA] Model='{self.model}', Latency={elapsed_ms:.1f} ms, "
            f"Confidence={overall_conf*100:.1f}%, Medicines Found={len(gemma_meds)}"
        )
        logger.info("[GEMMA] Completed")

        # Save Debug Output if DEBUG_OCR is enabled
        if DEBUG_OCR or os.path.exists(DEBUG_DIR):
            try:
                os.makedirs(DEBUG_DIR, exist_ok=True)
                with open(os.path.join(DEBUG_DIR, "gemma_result.json"), "w", encoding="utf-8") as f_json:
                    json.dump({
                        "model": self.model,
                        "latency_ms": round(elapsed_ms, 2),
                        "raw_response": raw_response_text,
                        "parsed_json": parsed_data,
                        "extracted_medicines_count": len(gemma_meds)
                    }, f_json, indent=2)
            except Exception as dbg_err:
                logger.warning(f"[GEMMA] Debug save error: {dbg_err}")

        return gemma_meds, overall_conf, round(elapsed_ms, 2)

    def compare_with_tesseract(
        self,
        tesseract_meds: List[ExtractedMedicine],
        gemma_meds: List[ExtractedMedicine],
        tesseract_conf: float,
        gemma_conf: float
    ) -> Tuple[List[ExtractedMedicine], float, str]:
        """
        Compares Tesseract vs Gemma-4 Vision candidates.
        Returns (chosen_medicines, chosen_confidence, decision_reason).
        """
        def score_med_set(meds: List[ExtractedMedicine], conf: float) -> float:
            if not meds:
                return 0.0
            valid_names = [m for m in meds if m.medicine_name and m.medicine_name.lower() not in ["unknown", "unrecognized"]]
            if not valid_names:
                return 0.0
            count_score = len(valid_names) * 100.0
            field_score = sum(
                (30.0 if m.dosage else 0.0) +
                (30.0 if m.frequency else 0.0) +
                (20.0 if m.duration else 0.0)
                for m in valid_names
            ) / float(len(valid_names))
            return count_score + field_score + (conf * 0.5)

        t_score = score_med_set(tesseract_meds, tesseract_conf)
        g_score = score_med_set(gemma_meds, gemma_conf)

        if g_score > t_score:
            reason = f"Chose Gemma-4 Vision (Score: {g_score:.1f} vs Tesseract: {t_score:.1f})"
            logger.info(f"[GEMMA] Decision: {reason}")
            return gemma_meds, gemma_conf, reason
        else:
            reason = f"Retained Tesseract OCR (Score: {t_score:.1f} vs Gemma: {g_score:.1f})"
            logger.info(f"[GEMMA] Decision: {reason}")
            return tesseract_meds, tesseract_conf, reason
