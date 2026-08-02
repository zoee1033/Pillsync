import os
import base64
import json
import time
import urllib.request
from typing import Dict, Any, Optional, Tuple, List
from app.services.ocr.knowledge_base import match_medicine_rapidfuzz, load_medicine_database

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


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
        print("[OPENAI_VISION] OPENAI_API_KEY environment variable is not set. Skipping cloud Vision AI fallback.", flush=True)
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

                print(f"[OPENAI_VISION] Successfully extracted prescription in {elapsed_ms}ms: {parsed_json.get('medicine_name')} ({parsed_json.get('dosage')})", flush=True)

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
        print(f"[OPENAI_VISION] OpenAI Vision API call failed ({elapsed_ms}ms): {api_err}", flush=True)
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
