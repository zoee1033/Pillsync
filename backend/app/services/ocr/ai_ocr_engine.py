import os
import re
import base64
import json
import time
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Tuple, List
from app.services.ocr.knowledge_base import match_medicine_rapidfuzz, validate_dosage_non_destructive, load_medicine_database
from app.schemas.ocr_schema import ExtractedMedicine, FieldConfidence

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


# Configurable Decision Thresholds (Loaded ONCE at application startup)
OCR_CONFIDENCE_THRESHOLD = float(os.environ.get("OCR_CONFIDENCE_THRESHOLD", "75.0"))
FIELD_CONFIDENCE_THRESHOLD = int(os.environ.get("FIELD_CONFIDENCE_THRESHOLD", "80"))
MEDICINE_CONFIDENCE_THRESHOLD = float(os.environ.get("MEDICINE_CONFIDENCE_THRESHOLD", "0.85"))

# Task 1: Global In-Memory Cache for Medicine Database Candidates
_CACHED_MEDICINE_CANDIDATES: Optional[List[str]] = None


def get_gemini_api_key() -> str:
    """Reads GEMINI_API_KEY or GOOGLE_API_KEY from environment variables."""
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")


def get_known_medicine_candidates() -> List[str]:
    """
    Task 1: Caches medicine_database.json in memory on first call.
    Reuses the cached list for all subsequent OCR requests.
    Reloads only when application restarts.
    """
    global _CACHED_MEDICINE_CANDIDATES
    if _CACHED_MEDICINE_CANDIDATES is not None:
        return _CACHED_MEDICINE_CANDIDATES

    db_list = load_medicine_database()
    candidates = []
    seen = set()
    for drug in db_list:
        gen = drug.get("generic_name")
        if gen and gen.lower() not in seen:
            seen.add(gen.lower())
            candidates.append(gen)
        for brand in drug.get("brand_names", []):
            if brand and brand.lower() not in seen:
                seen.add(brand.lower())
                candidates.append(brand)
        for alias in drug.get("aliases", []):
            if alias and alias.lower() not in seen:
                seen.add(alias.lower())
                candidates.append(alias)

    _CACHED_MEDICINE_CANDIDATES = candidates
    logger.info(f"[CACHE] Loaded and cached {len(_CACHED_MEDICINE_CANDIDATES)} medicine candidates in memory.")
    return _CACHED_MEDICINE_CANDIDATES


def select_relevant_medicine_candidates(ocr_text: str, top_k: int = 25) -> List[str]:
    """
    Task 2: Filters medicine_database candidates using RapidFuzz against Tesseract OCR text,
    selecting only the Top 20-30 most relevant candidates to minimize Gemini prompt size & cost.
    """
    from rapidfuzz import fuzz

    all_candidates = get_known_medicine_candidates()
    if not ocr_text or not ocr_text.strip() or not all_candidates:
        return all_candidates[:top_k]

    # Split OCR text into meaningful line tokens
    lines_and_tokens = [t.strip() for t in re.split(r'[\n,;:]+', ocr_text) if len(t.strip()) > 2]
    
    scored_candidates = {}
    for cand in all_candidates:
        max_score = 0.0
        for item in lines_and_tokens:
            score = fuzz.token_set_ratio(item, cand)
            if score > max_score:
                max_score = score
        scored_candidates[cand] = max_score

    # Sort candidates descending by match score
    sorted_cands = sorted(scored_candidates.keys(), key=lambda c: scored_candidates[c], reverse=True)
    
    # Filter top candidates with score >= 30.0
    top_matches = [c for c in sorted_cands if scored_candidates[c] >= 30.0][:top_k]

    # If matches count < 15, backfill from popular database candidates to maintain context up to top_k
    if len(top_matches) < 15:
        for c in all_candidates:
            if c not in top_matches:
                top_matches.append(c)
            if len(top_matches) >= top_k:
                break

    return top_matches[:top_k]


def run_gemini_vision_verification(
    image_bytes: bytes,
    tesseract_text: str,
    enhanced_image_bytes: Optional[bytes] = None,
    ocr_confidence: float = 0.0,
    detected_medicines: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Gemini Vision Verification Layer:
    Compares original prescription image (+ optional enhanced preprocessed image) against
    Tesseract OCR output, confidence score, parser-detected medicines, and Top relevant candidate medicines.
    """
    start_time = time.time()
    api_key = get_gemini_api_key()

    if not image_bytes:
        return {
            "success": False,
            "error": "No image bytes provided",
            "engine": "Gemini_Vision",
            "data": None,
            "inference_time_ms": 0.0
        }

    if not api_key:
        logger.warning("[GEMINI_VISION] GEMINI_API_KEY or GOOGLE_API_KEY environment variable is not set. Skipping Gemini Vision Verification.")
        return {
            "success": False,
            "error": "GEMINI_API_KEY environment variable is not set.",
            "engine": "Gemini_Vision_Unconfigured",
            "data": None,
            "inference_time_ms": round((time.time() - start_time) * 1000, 2)
        }

    logger.info(f"[GEMINI_VISION] Invoking Gemini Vision Verification with Tesseract OCR text ({len(tesseract_text)} chars, Conf: {ocr_confidence:.1f}%)...")

    try:
        b64_orig = base64.b64encode(image_bytes).decode("utf-8")
        mime_orig = "image/png"
        if image_bytes.startswith(b'\xff\xd8'):
            mime_orig = "image/jpeg"
        elif image_bytes.startswith(b'RIFF') and b'WEBP' in image_bytes[:16]:
            mime_orig = "image/webp"

        b64_enhanced = None
        mime_enhanced = "image/png"
        if enhanced_image_bytes:
            b64_enhanced = base64.b64encode(enhanced_image_bytes).decode("utf-8")
            if enhanced_image_bytes.startswith(b'\xff\xd8'):
                mime_enhanced = "image/jpeg"

        meds_repr = json.dumps(detected_medicines, indent=2) if detected_medicines else "[]"

        # Task 2: Select ONLY Top 20-30 relevant medicine candidates via RapidFuzz
        candidate_list = select_relevant_medicine_candidates(tesseract_text, top_k=25)
        candidates_formatted = "\n".join(f"- {name}" for name in candidate_list)

        prompt_text = (
            "You are an expert medical prescription verification assistant.\n\n"
            "You are NOT performing OCR from scratch.\n\n"
            "You are given:\n"
            "1. Original prescription image.\n"
            f"{'2. Enhanced image after preprocessing.' if b64_enhanced else ''}\n"
            f"3. OCR text generated by Tesseract:\n---\n{tesseract_text}\n---\n"
            f"4. OCR confidence score: {ocr_confidence:.1f}%\n"
            f"5. Medicines detected by the parser:\n{meds_repr}\n\n"
            "Known medicine candidates:\n"
            f"{candidates_formatted}\n\n"
            "Your task is ONLY to verify and correct OCR mistakes.\n\n"
            "Rules\n"
            "• Use these medicine names only as reference.\n"
            "• Preserve correct OCR text.\n"
            "• Correct obvious OCR mistakes.\n"
            "• Never invent medicine names.\n"
            "• Never guess dosage.\n"
            "• Never guess frequency.\n"
            "• Never guess duration.\n"
            "• If none match the prescription image, return null.\n"
            "• Return ONLY JSON.\n\n"
            "Schema\n"
            "{\n"
            '    "patient_name":"",\n'
            '    "doctor_name":"",\n'
            '    "date":"",\n'
            '    "medicines":[\n'
            "        {\n"
            '            "name":"",\n'
            '            "dosage":"",\n'
            '            "frequency":"",\n'
            '            "duration":"",\n'
            '            "instructions":""\n'
            "        }\n"
            "    ]\n"
            "}"
        )

        parts = [
            {"text": prompt_text},
            {
                "inline_data": {
                    "mime_type": mime_orig,
                    "data": b64_orig
                }
            }
        ]

        if b64_enhanced:
            parts.append({
                "inline_data": {
                    "mime_type": mime_enhanced,
                    "data": b64_enhanced
                }
            })

        # Gemini REST API endpoints to try (gemini-1.5-flash primary, fallbacks to 2.0-flash / 1.5-pro)
        models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
        parsed_json = None
        last_error = None

        for model_name in models_to_try:
            endpoint_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            
            payload = {
                "contents": [
                    {
                        "parts": parts
                    }
                ],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.1
                }
            }

            req = urllib.request.Request(
                endpoint_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )

            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    res_body = json.loads(response.read().decode("utf-8"))
                    candidates = res_body.get("candidates", [])
                    if candidates:
                        res_parts = candidates[0].get("content", {}).get("parts", [])
                        if res_parts:
                            raw_content = res_parts[0].get("text", "").strip()
                            # Clean potential markdown block wrappers
                            if raw_content.startswith("```json"):
                                raw_content = raw_content[7:]
                            if raw_content.startswith("```"):
                                raw_content = raw_content[3:]
                            if raw_content.endswith("```"):
                                raw_content = raw_content[:-3]
                            raw_content = raw_content.strip()

                            parsed_json = json.loads(raw_content)
                            extracted_count = len(parsed_json.get("medicines", [])) if isinstance(parsed_json, dict) else 0
                            logger.info(f"[GEMINI_VISION] Gemini ({model_name}) response parsed successfully ({extracted_count} medicine items extracted).")
                            break
            except urllib.error.HTTPError as http_err:
                err_body = http_err.read().decode('utf-8')
                last_error = f"HTTP {http_err.code}: {err_body}"
                logger.warning(f"[GEMINI_VISION] Model {model_name} failed: HTTP {http_err.code}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[GEMINI_VISION] Model {model_name} error: {last_error}")

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        if parsed_json and isinstance(parsed_json, dict):
            return {
                "success": True,
                "data": parsed_json,
                "engine": "Gemini_Vision",
                "inference_time_ms": elapsed_ms
            }

        logger.error(f"[GEMINI_VISION] All Gemini API attempts failed ({elapsed_ms}ms). Last error: {last_error}")
        return {
            "success": False,
            "error": f"Gemini Vision call failed: {last_error}",
            "engine": "Gemini_Vision_Error",
            "data": None,
            "inference_time_ms": elapsed_ms
        }

    except Exception as exc:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"[GEMINI_VISION] Unexpected exception during Gemini Vision Verification: {exc}", exc_info=True)
        return {
            "success": False,
            "error": str(exc),
            "engine": "Gemini_Vision_Exception",
            "data": None,
            "inference_time_ms": elapsed_ms
        }


def convert_gemini_response_to_medicines(gemini_data: Dict[str, Any]) -> List[ExtractedMedicine]:
    """
    Task 3 & Task 5:
    Parses structured Gemini response and validates against Knowledge Base & RapidFuzz.
    Removes all fabricated/invented default values. Sets needs_review = True if essential fields are null/missing.
    Preserves original OCR name and normalized name in audit logging & metadata.
    """
    extracted_meds: List[ExtractedMedicine] = []
    med_list = gemini_data.get("medicines", [])

    if not isinstance(med_list, list):
        return []

    for item in med_list:
        if not isinstance(item, dict):
            continue

        raw_ocr_name = item.get("name") or ""
        if not raw_ocr_name or str(raw_ocr_name).strip().lower() in ["null", "none", "unreadable", "unknown", "n/a"]:
            logger.info("[MEDICINE_VALIDATION] Gemini marked medicine name as unreadable or null. Skipping item.")
            continue

        raw_ocr_name = str(raw_ocr_name).strip()

        # RapidFuzz medicine validation against Knowledge Base
        kb_info = match_medicine_rapidfuzz(raw_ocr_name)
        is_known = kb_info.get("is_known", False)
        
        if is_known:
            normalized_name = kb_info["matched_name"]
            name_conf = int(kb_info.get("similarity_score", 95.0))
        else:
            normalized_name = raw_ocr_name.capitalize()
            name_conf = 70

        # Task 6: Log RapidFuzz correction and Normalized medicine name (no API keys or PII)
        logger.info(f"[RAPIDFUZZ] Corrected raw OCR text '{raw_ocr_name}' -> '{normalized_name}' (Score: {name_conf}%)")
        logger.info(f"[MEDICINE_NORMALIZATION] Normalized medicine name: '{normalized_name}'")

        # Task 5: Log & preserve original vs normalized details for debugging
        resolution_metadata = {
            "ocr_name": raw_ocr_name,
            "normalized_name": normalized_name,
            "similarity_score": name_conf,
            "is_known": is_known,
            "algorithm_used": kb_info.get("algorithm_used", "none")
        }
        logger.info(f"[DEBUG_RESOLUTION] {json.dumps(resolution_metadata)}")

        # Task 3: Remove invented defaults (Do NOT default to "500mg", "Daily", "7 days")
        raw_dosage = item.get("dosage")
        raw_dosage_str = str(raw_dosage).strip() if raw_dosage and str(raw_dosage).strip().lower() not in ["null", "none", ""] else ""
        
        dosage_val = validate_dosage_non_destructive(raw_dosage_str, kb_info.get("drug_object")) if raw_dosage_str else {"valid": False}
        dosage_conf = 95 if (raw_dosage_str and dosage_val.get("valid")) else 50

        raw_freq = item.get("frequency")
        freq_str = str(raw_freq).strip() if raw_freq and str(raw_freq).strip().lower() not in ["null", "none", ""] else ""
        freq_conf = 90 if freq_str else 50

        raw_dur = item.get("duration")
        duration_str = str(raw_dur).strip() if raw_dur and str(raw_dur).strip().lower() not in ["null", "none", ""] else ""
        duration_conf = 90 if duration_str else 50

        # Task 2: Populate quantity ONLY if explicitly present/extracted, else None (Never invent quantity)
        raw_qty = item.get("quantity")
        parsed_qty = None
        if raw_qty is not None and str(raw_qty).isdigit() and int(raw_qty) > 0:
            parsed_qty = int(raw_qty)

        # Calculate overall confidence
        overall_conf = round((name_conf + dosage_conf + freq_conf + duration_conf) / 400.0, 2)
        
        field_conf = FieldConfidence(
            name_confidence=name_conf,
            dosage_confidence=dosage_conf,
            frequency_confidence=freq_conf,
            duration_confidence=duration_conf
        )

        # Task 3 & Task 4: Flag needs_review if any important field is missing/null, invalid dosage, or low confidence
        is_missing_fields = not raw_dosage_str or not freq_str or not duration_str
        needs_review = is_missing_fields or (not dosage_val.get("valid")) or (not is_known) or (overall_conf < MEDICINE_CONFIDENCE_THRESHOLD)

        extracted_meds.append(
            ExtractedMedicine(
                medicine_name=normalized_name,
                dosage=raw_dosage_str,
                quantity=parsed_qty,
                frequency=freq_str,
                duration=duration_str,
                confidence=overall_conf,
                field_confidence=field_conf,
                needs_review=needs_review
            )
        )

    return extracted_meds


def run_openai_vision_ocr(image_bytes: bytes) -> Dict[str, Any]:
    """
    OpenAI Vision OCR Engine (Cloud AI Fallback):
    Runs GPT-4o-mini Vision AI model to extract structured prescription details
    (medicine_name, dosage, quantity, frequency, duration, confidence).
    """
    if not image_bytes:
        return {"success": False, "raw_text": "", "engine": "OpenAI_Vision", "confidence": 0.0, "inference_time_ms": 0.0}

    start_time = time.time()

    if not OPENAI_API_KEY:
        import logging
        logger = logging.getLogger("AI_OCR_ENGINE")
        from app.config import settings
        if settings.ENABLE_VERBOSE_OCR_LOGS:
            logger.debug("OPENAI_API_KEY environment variable is not set. Skipping cloud Vision AI fallback.")
        return {
            "success": False,
            "raw_text": "OpenAI Vision skipped: OPENAI_API_KEY not configured.",
            "engine": "OpenAI_Vision_Unconfigured",
            "confidence": 0.0,
            "inference_time_ms": round((time.time() - start_time) * 1000, 2)
        }

    try:
        b64_img = base64.b64encode(image_bytes).decode('utf-8')
        data_url = f"data:image/png;base64,{b64_img}"
        url = "https://api.openai.com/v1/chat/completions"

        payload = {
            "model": "gpt-4o-mini",
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert clinical prescription vision model specializing in reading complex doctor handwriting, cursive medical scripts, "
                        "and printed prescriptions. Extract all structured medicine details into a JSON object with fields: "
                        "'medicine_name' (string, main drug or brand name), 'generic_name' (string or null), 'dosage' (string, e.g. 500mg, 2 puffs), "
                        "'quantity' (integer), 'frequency' (string, decode Latin abbreviations: QD=once daily, BID=twice daily, TID=three times daily, QID=four times daily, PRN=as needed), "
                        "'duration' (string, e.g. 7 days, 1 month), 'instructions' (string, e.g. Take after meals), 'confidence' (integer 0-100 score). "
                        "Output strict JSON only. Do not include markdown code block syntax or conversational text."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all medicine prescription details from this image."},
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ]
                }
            ],
            "max_tokens": 300,
            "temperature": 0.1
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            }
        )

        with urllib.request.urlopen(req, timeout=12) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            choices = res_data.get("choices", [])
            if choices:
                content_str = choices[0].get("message", {}).get("content", "")
                parsed_json = json.loads(content_str)
                elapsed_ms = round((time.time() - start_time) * 1000, 2)

                import logging
                logger = logging.getLogger("AI_OCR_ENGINE")
                logger.info(f"OpenAI Vision extracted prescription ({elapsed_ms}ms): {parsed_json.get('medicine_name')} ({parsed_json.get('dosage')})")

                raw_text_repr = f"Rx: {parsed_json.get('medicine_name')} {parsed_json.get('dosage')} {parsed_json.get('frequency')} Qty {parsed_json.get('quantity')} {parsed_json.get('duration')}"

                return {
                    "success": True,
                    "raw_text": raw_text_repr,
                    "structured_data": parsed_json,
                    "engine": "OpenAI_Vision_GPT4o",
                    "confidence": float(parsed_json.get("confidence", 95)),
                    "inference_time_ms": elapsed_ms
                }

    except Exception as api_err:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        import logging
        logger = logging.getLogger("AI_OCR_ENGINE")
        logger.warning(f"OpenAI Vision API call failed ({elapsed_ms}ms): {api_err}")
        return {
            "success": False,
            "raw_text": f"OpenAI Vision error: {str(api_err)}",
            "engine": "OpenAI_Vision_Error",
            "confidence": 0.0,
            "inference_time_ms": elapsed_ms
        }

    return {"success": False, "raw_text": "", "engine": "OpenAI_Vision", "confidence": 0.0, "inference_time_ms": 0.0}


def resolve_openai_hybrid_conflict(
    tesseract_med: str,
    tesseract_conf: float,
    openai_med: Optional[str],
    openai_conf: float
) -> Tuple[str, float, bool, Dict[str, Any]]:
    """
    OpenAI Hybrid Resolution Engine:
    Compares Tesseract Result vs OpenAI Vision Result using RapidFuzz Knowledge Base scoring.
    If both engines disagree on known drugs, sets needs_review = True and preserves candidate metadata.
    """
    tess_info = match_medicine_rapidfuzz(tesseract_med) if tesseract_med else {}
    openai_info = match_medicine_rapidfuzz(openai_med) if openai_med else {}

    tess_score = tess_info.get("similarity_score", 0.0)
    openai_score = openai_info.get("similarity_score", 0.0)

    tess_gen = tess_info.get("generic_name", tesseract_med)
    openai_gen = openai_info.get("generic_name", openai_med)

    details = {
        "tesseract_candidate": tesseract_med,
        "tesseract_generic": tess_gen,
        "tesseract_confidence": tesseract_conf,
        "tesseract_kb_score": tess_score,
        "openai_candidate": openai_med,
        "openai_generic": openai_gen,
        "openai_confidence": openai_conf,
        "openai_kb_score": openai_score,
        "selected_engine": "Tesseract",
        "resolution_reason": ""
    }

    # 1. Agreement Check
    if tess_gen.lower() == openai_gen.lower() and tess_info.get("is_known"):
        details["selected_engine"] = "Ensemble (Agreement)"
        details["resolution_reason"] = f"Tesseract ({tesseract_conf:.1f}%) and OpenAI Vision ({openai_conf:.1f}%) agree on '{tess_gen}'"
        return tess_gen, max(tesseract_conf, openai_conf), False, details

    # 2. Conflict & Candidate Selection
    needs_review = True
    if openai_score > tess_score and openai_score >= 80.0:
        winning_med = openai_gen
        winning_conf = openai_conf
        details["selected_engine"] = "OpenAI_Vision_GPT4o"
        details["resolution_reason"] = f"OpenAI Vision selected due to higher Knowledge Base score ({openai_score:.1f}% vs {tess_score:.1f}%)"
    else:
        winning_med = tess_gen
        winning_conf = tesseract_conf
        details["selected_engine"] = "Tesseract_Ensemble"
        details["resolution_reason"] = f"Tesseract selected due to higher Knowledge Base score ({tess_score:.1f}% vs {openai_score:.1f}%)"

    if tess_gen != openai_gen and tess_info.get("is_known") and openai_info.get("is_known"):
        details["conflict_detected"] = True
        details["resolution_reason"] += f" | Conflict: Tesseract='{tess_gen}' vs OpenAI='{openai_gen}'"

    return winning_med, winning_conf, needs_review, details

